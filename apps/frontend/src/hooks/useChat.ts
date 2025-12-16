import { useState, useCallback, useRef } from 'react';
import { api } from '../lib/api';

interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

interface UseChatReturn {
  sessionId: string | null;
  messages: ChatMessage[];
  isStreaming: boolean;
  error: string | null;
  sendMessage: (message: string) => Promise<void>;
  createSession: () => Promise<string>;
  clearMessages: () => void;
}

export function useChat(): UseChatReturn {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const createSession = useCallback(async (): Promise<string> => {
    try {
      const response = await api.post('/api/v1/chat/sessions', {
        title: 'Nuovo Dataset'
      });
      const newSessionId = response.data.id;
      setSessionId(newSessionId);
      return newSessionId;
    } catch (err: any) {
      setError(err.message || 'Failed to create chat session');
      throw err;
    }
  }, []); // Empty deps - function is stable

  const sendMessage = useCallback(async (message: string) => {
    if (!sessionId) {
      const newSessionId = await createSession();
      setSessionId(newSessionId);
    }

    const currentSessionId = sessionId || await createSession();
    
    // Add user message
    const userMessage: ChatMessage = { role: 'user', content: message };
    setMessages(prev => [...prev, userMessage]);
    setIsStreaming(true);
    setError(null);

    // Cancel previous request if any
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();

    try {
      // Send message with streaming
      const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
      const token = localStorage.getItem('access_token');
      
      if (!token) {
        throw new Error('No access token found. Please login again.');
      }

      const response = await fetch(
        `${API_BASE_URL}/api/v1/chat/sessions/${currentSessionId}/messages/stream`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            content: message,
            role: 'user'
          }),
          signal: abortControllerRef.current.signal
        }
      );

      if (!response.ok) {
        const errorText = await response.text();
        let errorMessage = `HTTP error! status: ${response.status}`;
        try {
          const errorJson = JSON.parse(errorText);
          errorMessage = errorJson.detail || errorJson.message || errorMessage;
        } catch {
          if (errorText) {
            errorMessage = errorText;
          }
        }
        throw new Error(errorMessage);
      }

      // Handle streaming response
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let assistantMessage = '';
      let buffer = '';

      if (!reader) {
        throw new Error('No response body');
      }

      // Add assistant message placeholder
      setMessages(prev => [...prev, { role: 'assistant', content: '' }]);

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') {
              setIsStreaming(false);
              return;
            }
            
            try {
              const parsed = JSON.parse(data);
              
              // Check for errors first
              if (parsed.error) {
                setError(parsed.error);
                setIsStreaming(false);
                return;
              }
              
              // Check if done
              if (parsed.done) {
                setIsStreaming(false);
                return;
              }
              
              if (parsed.content) {
                assistantMessage += parsed.content;
                // Update last message
                setMessages(prev => {
                  const newMessages = [...prev];
                  newMessages[newMessages.length - 1] = {
                    role: 'assistant',
                    content: assistantMessage
                  };
                  return newMessages;
                });
              }
              
              // Check for DatasetPlan in response (sent separately by backend)
              if (parsed.dataset_plan) {
                // DatasetPlan received from backend as separate field
                // Don't add it to message content, store it separately
                // ChatStep will extract it via useEffect
                if (!assistantMessage.includes('✅ Piano dataset generato')) {
                  assistantMessage += '\n\n✅ Piano dataset generato con successo!';
                }
                setMessages(prev => {
                  const newMessages = [...prev];
                  const messageWithPlan = {
                    role: 'assistant' as const,
                    content: assistantMessage,
                    _datasetPlan: parsed.dataset_plan // Hidden property for extraction
                  };
                  newMessages[newMessages.length - 1] = messageWithPlan as any;
                  return newMessages;
                });
              }
              
              // Check for tool calls
              if (parsed.tool_calls) {
                for (const toolCall of parsed.tool_calls) {
                  if (toolCall.function?.name === 'create_dataset_plan') {
                    try {
                      const planArgs = JSON.parse(toolCall.function.arguments);
                      // DatasetPlan detected - store it but don't show JSON
                      assistantMessage += '\n\n✅ Piano dataset generato con successo!';
                      setMessages(prev => {
                        const newMessages = [...prev];
                        const messageWithPlan = {
                          role: 'assistant' as const,
                          content: assistantMessage,
                          _datasetPlan: planArgs // Hidden property
                        };
                        newMessages[newMessages.length - 1] = messageWithPlan as any;
                        return newMessages;
                      });
                    } catch (e) {
                      console.error('Error parsing tool call:', e);
                    }
                  }
                }
              }
            } catch (e) {
              // Not JSON, might be plain text
              if (data.trim() && data !== '[DONE]') {
                assistantMessage += data;
                setMessages(prev => {
                  const newMessages = [...prev];
                  newMessages[newMessages.length - 1] = {
                    role: 'assistant',
                    content: assistantMessage
                  };
                  return newMessages;
                });
              }
            }
          }
        }
      }

      setIsStreaming(false);
    } catch (err: any) {
      if (err.name === 'AbortError') {
        return; // Request was cancelled
      }
      
      // Better error handling
      let errorMessage = 'Failed to send message';
      if (err.message) {
        errorMessage = err.message;
      } else if (err.response) {
        errorMessage = `Server error: ${err.response.status}`;
      } else if (!navigator.onLine) {
        errorMessage = 'No internet connection';
      }
      
      console.error('Chat error:', err);
      setError(errorMessage);
      setIsStreaming(false);
      // Remove failed assistant message
      setMessages(prev => prev.slice(0, -1));
    }
  }, [sessionId, createSession]);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  return {
    sessionId,
    messages,
    isStreaming,
    error,
    sendMessage,
    createSession,
    clearMessages
  };
}

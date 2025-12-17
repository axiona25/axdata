import { useState, useRef, useEffect } from 'react';
import { Send, User, RotateCcw, Edit2, Trash2, X } from 'lucide-react';
import type { DatasetPlan } from '../../types';
import botAvatar from '../../assets/avatar-axdata.png';

interface ChatStepProps {
  sessionId: string | null;
  messages: Array<{ role: 'user' | 'assistant' | 'system'; content: string }>;
  isStreaming: boolean;
  onSendMessage: (message: string) => Promise<void>;
  onDatasetPlanGenerated: (plan: DatasetPlan) => void;
  onResetChat?: () => void;
  onUserConfirmed?: () => void; // Callback when user confirms
  error?: string | null;
}

export default function ChatStep({
  sessionId,
  messages,
  isStreaming,
  onSendMessage,
  onDatasetPlanGenerated,
  onResetChat,
  onUserConfirmed,
  error
}: ChatStepProps) {
  const [inputMessage, setInputMessage] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [datasetPlanReady, setDatasetPlanReady] = useState<DatasetPlan | null>(null);
  const [userConfirmed, setUserConfirmed] = useState(false); // Track if user confirmed
  const [editingMessageId, setEditingMessageId] = useState<number | null>(null);
  const [editingContent, setEditingContent] = useState<string>('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const processedMessageRef = useRef<number>(0); // Track last processed message index

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isStreaming]);

  // Reset isProcessing when streaming ends
  useEffect(() => {
    if (!isStreaming && isProcessing) {
      setIsProcessing(false);
    }
  }, [isStreaming, isProcessing]);

  // Parse messages to extract DatasetPlan from tool calls or metadata
  useEffect(() => {
    // Only process if we have new messages and not streaming
    if (messages.length === 0 || isStreaming || isProcessing) {
      return;
    }

    // Only process if we haven't already processed this message
    const currentMessageIndex = messages.length - 1;
    if (currentMessageIndex <= processedMessageRef.current) {
      return;
    }

    const lastMessage = messages[currentMessageIndex];
    if (!lastMessage || lastMessage.role !== 'assistant') {
      return;
    }

    // Mark as processed immediately to prevent re-processing
    processedMessageRef.current = currentMessageIndex;

    try {
      // Method 1: Check for hidden _datasetPlan property (preferred method)
      const messageWithPlan = lastMessage as any;
      if (messageWithPlan._datasetPlan) {
        const planJson = messageWithPlan._datasetPlan;
        if (planJson.domain && planJson.title) {
          console.log('DatasetPlan extracted from _datasetPlan property:', planJson);
          // Store plan and notify parent, but don't auto-advance - wait for user confirmation
          setDatasetPlanReady(planJson as DatasetPlan);
          onDatasetPlanGenerated(planJson as DatasetPlan);
          return;
        }
      }
      
      // Method 2: Look for [DATASET_PLAN] marker (from backend streaming)
      const planMarkerMatch = lastMessage.content.match(/\[DATASET_PLAN\]\s*\n([\s\S]*?)(?:\n\n|$)/);
      if (planMarkerMatch) {
        const planJson = JSON.parse(planMarkerMatch[1]);
        if (planJson.domain && planJson.title) {
          setDatasetPlanReady(planJson as DatasetPlan);
          onDatasetPlanGenerated(planJson as DatasetPlan);
          return;
        }
      }
      
      // Method 3: Look for JSON code block
      const jsonBlockMatch = lastMessage.content.match(/```json\s*([\s\S]*?)\s*```/);
      if (jsonBlockMatch) {
        const planJson = JSON.parse(jsonBlockMatch[1]);
        if (planJson.domain && planJson.title) {
          setDatasetPlanReady(planJson as DatasetPlan);
          onDatasetPlanGenerated(planJson as DatasetPlan);
          return;
        }
      }
      
      // Method 4: Try to find JSON object directly in content (last resort)
      const jsonMatch = lastMessage.content.match(/\{[\s\S]*"domain"[\s\S]*"title"[\s\S]*\}/);
      if (jsonMatch) {
        const planJson = JSON.parse(jsonMatch[0]);
        if (planJson.domain && planJson.title) {
          setDatasetPlanReady(planJson as DatasetPlan);
          onDatasetPlanGenerated(planJson as DatasetPlan);
          return;
        }
      }
    } catch (e) {
      // Not a valid DatasetPlan JSON, continue
      console.debug('No DatasetPlan found in message:', e);
    }
  }, [messages.length, isStreaming, isProcessing, onDatasetPlanGenerated]);

  // Check if AI asked for confirmation and user confirmed
  useEffect(() => {
    // Don't check if streaming is active
    if (isStreaming || messages.length === 0) {
      return;
    }

    // Check if AI asked for confirmation (look for various confirmation patterns)
    const assistantMessages = messages.filter(msg => msg.role === 'assistant');
    const aiAskedConfirmation = assistantMessages.some(msg => {
      const content = msg.content.toLowerCase();
      return (
        /confermi\?/i.test(content) ||
        /procedo\?/i.test(content) ||
        /procediamo\?/i.test(content) ||
        /va bene\?/i.test(content) ||
        /creazione del piano/i.test(content) ||
        /procedo con/i.test(content) ||
        /posso procedere/i.test(content) ||
        /vuoi che proceda/i.test(content)
      );
    });

    // Check last user message for confirmation
    const userMessages = messages.filter(msg => msg.role === 'user');
    const lastUserMessage = userMessages[userMessages.length - 1];
    
    if (aiAskedConfirmation && lastUserMessage && !userConfirmed) {
      const userContent = lastUserMessage.content.trim().toLowerCase();
      const isConfirmation = /^(sì|si|yes|ok|confermo|conferma|va bene|perfetto|procedi|procediamo|conferma e continua|vai|go)$/i.test(userContent);
      
      if (isConfirmation) {
        console.log('User confirmed detected:', userContent);
        console.log('DatasetPlan ready:', datasetPlanReady);
        setUserConfirmed(true);
        if (onUserConfirmed) {
          onUserConfirmed();
        }
      }
    }
  }, [messages, datasetPlanReady, userConfirmed, onUserConfirmed, isStreaming]);

  const handleSend = async () => {
    if (!inputMessage.trim() || isProcessing || isStreaming) return;
    
    const messageToSend = inputMessage.trim();
    setIsProcessing(true);
    
    setInputMessage('');
    
    try {
      await onSendMessage(messageToSend);
      
      // Check if user is confirming after message is sent
      // This will be handled by the useEffect that watches messages
      const isConfirmation = /^(sì|si|yes|ok|confermo|conferma|va bene|perfetto|procedi|procediamo|vai|go)$/i.test(messageToSend.toLowerCase());
      if (isConfirmation && datasetPlanReady) {
        // Small delay to ensure message is added to messages array
        setTimeout(() => {
          setUserConfirmed(true);
          if (onUserConfirmed) {
            onUserConfirmed();
          }
        }, 100);
      }
      
      // isProcessing will be reset by useEffect when isStreaming becomes false
    } catch (error: any) {
      console.error('Error sending message:', error);
      setIsProcessing(false);
      // Error is already handled in useChat hook and shown via error state
    }
  };

  const handleResetChat = () => {
    if (window.confirm('Sei sicuro di voler ricominciare? Tutti i messaggi verranno cancellati.')) {
      setDatasetPlanReady(null);
      processedMessageRef.current = 0;
      if (onResetChat) {
        onResetChat();
      }
    }
  };

  const handleEditMessage = (index: number) => {
    const message = messages[index];
    if (message.role === 'user') {
      setEditingMessageId(index);
      setEditingContent(message.content);
    }
  };

  const handleSaveEdit = async () => {
    if (editingMessageId === null || !editingContent.trim()) return;
    
    const newMessage = editingContent.trim();
    setEditingMessageId(null);
    setEditingContent('');
    
    // Reset chat and send new message
    if (onResetChat) {
      onResetChat();
      // Wait a bit for reset to complete, then send new message
      setTimeout(() => {
        onSendMessage(newMessage);
      }, 200);
    }
  };

  const handleDeleteMessage = (index: number) => {
    if (window.confirm('Vuoi eliminare questo messaggio e tutti i messaggi successivi? La chat verrà resettata.')) {
      // Reset chat - simpler approach
      if (onResetChat) {
        onResetChat();
      }
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header with Reset button */}
      {messages.length > 0 && (
        <div className="flex justify-end mb-4">
          <button
            onClick={handleResetChat}
            className="px-3 py-1.5 text-sm rounded-input bg-dark-secondary text-text-secondary hover:bg-dark-secondary/80 hover:text-text-primary transition-colors flex items-center gap-2"
            title="Ricominciare la conversazione"
          >
            <RotateCcw className="w-4 h-4" />
            Reset Chat
          </button>
        </div>
      )}

      {/* Chat Messages */}
      <div 
        ref={chatContainerRef}
        className="flex-1 overflow-y-auto space-y-4 mb-4 min-h-[400px]"
      >
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <img
              src={botAvatar}
              alt="AXDATA"
              className="w-12 h-12 mb-4 opacity-90 object-contain"
              loading="eager"
              decoding="async"
            />
            <h3 className="text-lg font-semibold text-text-primary mb-2">
              Descrivi il dataset che vuoi creare
            </h3>
            <p className="text-text-secondary text-sm max-w-md">
              Scrivi in linguaggio naturale cosa ti serve. AXDATA interpreterà la tua richiesta e genererà automaticamente la configurazione del dataset.
            </p>
            <div className="mt-6 space-y-2 text-left">
              <p className="text-text-secondary text-sm font-medium">Esempi:</p>
              <ul className="text-text-secondary text-sm space-y-1 list-disc list-inside">
                <li>"GDP per capita in paesi UE dal 2020 al 2024"</li>
                <li>"Dati clinici su trial fase III per malattie cardiovascolari"</li>
                <li>"Popolazione per regione in Italia dal 2015"</li>
              </ul>
            </div>
          </div>
        ) : (
          messages.map((msg, idx) => {
            const isEditing = editingMessageId === idx;
            
            return (
              <div
                key={idx}
                className={`flex gap-3 group ${
                  msg.role === 'user' ? 'justify-end' : 'justify-start'
                }`}
              >
                {msg.role === 'assistant' && (
                  <div className="w-8 h-8 rounded-full bg-accent-blue/20 flex items-center justify-center flex-shrink-0">
                    <img
                      src={botAvatar}
                      alt="AXDATA"
                      className="w-5 h-5 object-contain"
                      loading="eager"
                      decoding="async"
                    />
                  </div>
                )}
                <div className="flex flex-col gap-2 max-w-[80%]">
                  {isEditing && msg.role === 'user' ? (
                    <div className="bg-dark-secondary rounded-lg px-4 py-3 border border-accent-blue">
                      <textarea
                        value={editingContent}
                        onChange={(e) => setEditingContent(e.target.value)}
                        className="w-full bg-transparent text-text-primary text-sm resize-none focus:outline-none"
                        rows={3}
                        autoFocus
                      />
                      <div className="flex justify-end gap-2 mt-2">
                        <button
                          onClick={() => {
                            setEditingMessageId(null);
                            setEditingContent('');
                          }}
                          className="px-3 py-1 text-xs rounded-input bg-dark-secondary hover:bg-dark-secondary/80 text-text-secondary"
                        >
                          <X className="w-3 h-3" />
                        </button>
                        <button
                          onClick={handleSaveEdit}
                          className="px-3 py-1 text-xs rounded-input bg-accent-blue text-white hover:bg-accent-blue/90"
                        >
                          Salva
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div
                      className={`rounded-lg px-4 py-3 relative ${
                        msg.role === 'user'
                          ? 'bg-accent-blue text-white'
                          : 'bg-dark-secondary text-text-primary'
                      }`}
                    >
                      {/* Don't show JSON or technical markers in chat */}
                      <p className="text-sm whitespace-pre-wrap">
                        {(() => {
                          let displayContent = msg.content;
                          // Remove [DATASET_PLAN] marker and everything after
                          displayContent = displayContent.replace(/\[DATASET_PLAN\][\s\S]*$/, '');
                          // Remove JSON code blocks
                          displayContent = displayContent.replace(/```json[\s\S]*?```/g, '');
                          // Remove standalone JSON objects (DatasetPlan)
                          displayContent = displayContent.replace(/\{[^{}]*"domain"[^{}]*"title"[^{}]*\}/g, '');
                          // Remove multi-line JSON objects
                          displayContent = displayContent.replace(/\{[\s\S]*?"domain"[\s\S]*?"title"[\s\S]*?\}/g, '');
                          return displayContent.trim() || 'Generando il piano del dataset...';
                        })()}
                      </p>
                      
                      {/* Edit/Delete buttons for user messages */}
                      {msg.role === 'user' && !isStreaming && (
                        <div className="absolute -right-8 top-2 opacity-0 group-hover:opacity-100 transition-opacity flex gap-1">
                          <button
                            onClick={() => handleEditMessage(idx)}
                            className="p-1 rounded-input bg-dark-secondary hover:bg-dark-secondary/80 text-text-secondary hover:text-accent-blue transition-colors"
                            title="Modifica messaggio"
                          >
                            <Edit2 className="w-3 h-3" />
                          </button>
                          <button
                            onClick={() => handleDeleteMessage(idx)}
                            className="p-1 rounded-input bg-dark-secondary hover:bg-red-500/20 text-text-secondary hover:text-red-400 transition-colors"
                            title="Elimina messaggio"
                          >
                            <Trash2 className="w-3 h-3" />
                          </button>
                        </div>
                      )}
                    </div>
                  )}
                </div>
                {msg.role === 'user' && (
                  <div className="w-8 h-8 rounded-full bg-dark-secondary flex items-center justify-center flex-shrink-0">
                    <User className="w-4 h-4 text-text-secondary" />
                  </div>
                )}
              </div>
            );
          })
        )}
        
        {isStreaming && (
          <div className="flex gap-3 justify-start">
            <div className="w-8 h-8 rounded-full bg-accent-blue/20 flex items-center justify-center flex-shrink-0">
              <img
                src={botAvatar}
                alt="AXDATA"
                className="w-5 h-5 object-contain"
                loading="eager"
                decoding="async"
              />
            </div>
            <div className="bg-dark-secondary rounded-lg px-4 py-3">
              <div className="flex gap-1">
                <div className="w-2 h-2 bg-accent-blue rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-2 h-2 bg-accent-blue rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-2 h-2 bg-accent-blue rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-500/20 border border-red-500/50 rounded-input p-3 mb-4">
          <p className="text-sm text-red-400">{error}</p>
        </div>
      )}

      {/* Input Area */}
      <div className="border-t border-dark-secondary pt-4">
        <div className="flex gap-2">
          <textarea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={datasetPlanReady ? "Rispondi all'AI (es: 'Sì, confermo' o 'Procedi')..." : "Descrivi il dataset che vuoi creare..."}
            className="flex-1 min-h-[80px] max-h-[200px] px-4 py-3 bg-dark-secondary border border-dark-secondary rounded-input text-text-primary placeholder-text-secondary resize-none focus:outline-none focus:border-accent-blue"
            disabled={isProcessing || isStreaming}
          />
          <button
            onClick={handleSend}
            disabled={!inputMessage.trim() || isProcessing || isStreaming}
            className="px-6 py-3 bg-accent-blue text-white rounded-input hover:bg-accent-blue/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <Send className="w-4 h-4" />
            Invia
          </button>
        </div>
        <p className="text-xs text-text-secondary mt-2">
          {datasetPlanReady 
            ? "Rispondi per confermare e continua la conversazione."
            : "AXDATA analizzerà la tua richiesta e ti spiegherà come costruirà il dataset"}
        </p>
      </div>
    </div>
  );
}

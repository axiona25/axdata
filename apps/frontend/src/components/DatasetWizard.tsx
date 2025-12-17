import { useState, useEffect, useCallback } from 'react';
import { X, MessageSquare, Eye, CheckCircle, Loader2 } from 'lucide-react';
import ChatStep from './DatasetWizardSteps/ChatStep';
import PreviewStep from './DatasetWizardSteps/PreviewStep';
import ConfirmStep from './DatasetWizardSteps/ConfirmStep';
import { useChat } from '../hooks/useChat';
import { useCreateDataset } from '../hooks/useCreateDataset';
import { api } from '../lib/api';
import type { DatasetPlan, DatasetSpec } from '../types';

interface DatasetWizardProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: (datasetId: string) => void;
}

type WizardStep = 'chat' | 'preview' | 'confirm';

export default function DatasetWizard({ isOpen, onClose, onSuccess }: DatasetWizardProps) {
  const [currentStep, setCurrentStep] = useState<WizardStep>('chat');
  const [datasetPlan, setDatasetPlan] = useState<DatasetPlan | null>(null);
  const [dsSpec, setDsSpec] = useState<DatasetSpec | null>(null);
  const [chatSessionId, setChatSessionId] = useState<string | null>(null);
  const [userConfirmedPlan, setUserConfirmedPlan] = useState(false);
  
  const { 
    sessionId, 
    messages, 
    isStreaming, 
    sendMessage, 
    createSession,
    clearMessages,
    error: chatError
  } = useChat();
  
  const { 
    createDataset, 
    isCreating, 
    error: createError 
  } = useCreateDataset();

  // Initialize chat session when wizard opens
  useEffect(() => {
    if (isOpen && !sessionId) {
      createSession().then(id => {
        setChatSessionId(id);
      }).catch(err => {
        console.error('Error creating session:', err);
      });
    }
  }, [isOpen, sessionId]); // Removed createSession to avoid loop - it's stable from useChat

  // Handle DatasetPlan extraction from chat
  const handleDatasetPlanGenerated = useCallback((plan: DatasetPlan) => {
    console.log('DatasetPlan generated in DatasetWizard:', plan);
    setDatasetPlan(plan);
    // DON'T auto-advance - wait for user to click "Conferma e Continua"
  }, []);

  // Reset to chat step when going back
  const handleBackToChat = useCallback(() => {
    setCurrentStep('chat');
    // Keep datasetPlan so user can go back and forth
  }, []);

  // Reset chat - clear messages and dataset plan
  const handleResetChat = useCallback(() => {
    // Clear chat messages
    clearMessages();
    
    // Reset dataset plan and confirmation
    setDatasetPlan(null);
    setDsSpec(null);
    setUserConfirmedPlan(false);
    
    // Create new session
    createSession().then(id => {
      setChatSessionId(id);
    }).catch(err => {
      console.error('Error creating new session:', err);
    });
  }, [clearMessages, createSession]);

  // Convert DatasetPlan to DS-SPEC
  const convertPlanToDsSpec = async (plan: DatasetPlan) => {
    // Call backend to convert DatasetPlan → DS-SPEC
    try {
      const response = await api.post('/api/v1/datasets/convert-plan-to-ds-spec', {
        plan: plan
      }, {
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      const dsSpecData = response.data;
      setDsSpec(dsSpecData);
      return dsSpecData;
    } catch (error: any) {
      console.error('Error converting plan to DS-SPEC:', error);
      // Fallback: use convert_dataset_plan_to_ds_spec logic
      // This will be handled by the backend endpoint
      throw error;
    }
  };

  // Handle preview confirmation
  const handlePreviewConfirm = async () => {
    if (!datasetPlan) return;
    
    // Convert to DS-SPEC
    const spec = await convertPlanToDsSpec(datasetPlan);
    setDsSpec(spec);
    setCurrentStep('confirm');
  };

  // Handle final confirmation and dataset creation
  const handleFinalConfirm = async () => {
    if (!dsSpec) return;
    
    try {
      const datasetId = await createDataset(dsSpec, chatSessionId);
      if (onSuccess) {
        onSuccess(datasetId);
      }
      onClose();
      // Reset wizard
      setCurrentStep('chat');
      setDatasetPlan(null);
      setDsSpec(null);
    } catch (error) {
      console.error('Error creating dataset:', error);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-dark-card border border-dark-secondary rounded-lg w-full max-w-4xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-dark-secondary">
          <div>
            <h2 className="text-xl font-semibold text-text-primary">Crea Nuovo Dataset</h2>
            <p className="text-sm text-text-secondary mt-1">
              Descrivi la tua richiesta e AXDATA genererà il dataset per te
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-input hover:bg-dark-secondary transition-colors"
          >
            <X className="w-5 h-5 text-text-secondary" />
          </button>
        </div>

        {/* Progress Steps */}
        <div className="flex items-center justify-center gap-4 p-4 border-b border-dark-secondary">
          <div className={`flex items-center gap-2 ${currentStep === 'chat' ? 'text-accent-blue' : currentStep !== 'chat' ? 'text-green-500' : 'text-text-secondary'}`}>
            <MessageSquare className="w-5 h-5" />
            <span className="text-sm font-medium">1. Chat</span>
          </div>
          <div className="w-12 h-0.5 bg-dark-secondary" />
          <div className={`flex items-center gap-2 ${currentStep === 'preview' ? 'text-accent-blue' : currentStep === 'confirm' ? 'text-green-500' : 'text-text-secondary'}`}>
            <Eye className="w-5 h-5" />
            <span className="text-sm font-medium">2. Preview</span>
          </div>
          <div className="w-12 h-0.5 bg-dark-secondary" />
          <div className={`flex items-center gap-2 ${currentStep === 'confirm' ? 'text-accent-blue' : 'text-text-secondary'}`}>
            <CheckCircle className="w-5 h-5" />
            <span className="text-sm font-medium">3. Conferma</span>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {currentStep === 'chat' && (
            <ChatStep
              sessionId={sessionId}
              messages={messages}
              isStreaming={isStreaming}
              onSendMessage={sendMessage}
              onDatasetPlanGenerated={handleDatasetPlanGenerated}
              onResetChat={handleResetChat}
              onUserConfirmed={() => {
                // User confirmed in chat, show button in footer
                console.log('User confirmed - showing button in footer');
                setUserConfirmedPlan(true);
              }}
              error={chatError}
            />
          )}
          
          {currentStep === 'preview' && datasetPlan && (
            <PreviewStep
              datasetPlan={datasetPlan}
              onConfirm={handlePreviewConfirm}
              onBack={handleBackToChat}
            />
          )}
          
          {currentStep === 'confirm' && dsSpec && (
            <ConfirmStep
              dsSpec={dsSpec}
              onConfirm={handleFinalConfirm}
              onBack={() => {
                setCurrentStep('preview');
              }}
              isCreating={isCreating}
              error={createError}
            />
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-dark-secondary">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-input text-text-secondary hover:bg-dark-secondary transition-colors"
          >
            Annulla
          </button>
          <div className="flex gap-2">
            {currentStep === 'chat' && datasetPlan && userConfirmedPlan && (
              <button
                onClick={() => {
                  console.log('Navigating to preview step');
                  setCurrentStep('preview');
                }}
                className="px-6 py-2 rounded-input bg-accent-blue text-white hover:bg-accent-blue/90 transition-colors flex items-center gap-2"
              >
                <CheckCircle className="w-4 h-4" />
                Conferma e Continua
              </button>
            )}
            {currentStep === 'preview' && (
              <button
                onClick={handleBackToChat}
                className="px-4 py-2 rounded-input bg-dark-secondary text-text-primary hover:bg-dark-secondary/80 transition-colors"
              >
                Indietro
              </button>
            )}
            {currentStep === 'preview' && (
              <button
                onClick={handlePreviewConfirm}
                className="px-6 py-2 rounded-input bg-accent-blue text-white hover:bg-accent-blue/90 transition-colors flex items-center gap-2"
              >
                <CheckCircle className="w-4 h-4" />
                Conferma e Continua
              </button>
            )}
            {currentStep === 'confirm' && (
              <button
                onClick={() => setCurrentStep('preview')}
                className="px-4 py-2 rounded-input bg-dark-secondary text-text-primary hover:bg-dark-secondary/80 transition-colors"
              >
                Indietro
              </button>
            )}
            {currentStep === 'confirm' && (
              <button
                onClick={handleFinalConfirm}
                disabled={isCreating}
                className="px-6 py-2 rounded-input bg-accent-blue text-white hover:bg-accent-blue/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {isCreating ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Creazione...
                  </>
                ) : (
                  'Crea Dataset'
                )}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

import { useState, useCallback } from 'react';
import { api } from '../lib/api';
import type { DatasetSpec } from '../types';

interface UseCreateDatasetReturn {
  createDataset: (dsSpec: DatasetSpec, chatSessionId?: string | null) => Promise<string>;
  isCreating: boolean;
  error: string | null;
}

export function useCreateDataset(): UseCreateDatasetReturn {
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const createDataset = useCallback(async (
    dsSpec: DatasetSpec,
    chatSessionId?: string | null
  ): Promise<string> => {
    setIsCreating(true);
    setError(null);

    try {
      const response = await api.post('/api/v1/datasets/from-ds-spec', {
        ds_spec: dsSpec,
        chat_session_id: chatSessionId
      });

      const datasetId = response.data.dataset_id;
      setIsCreating(false);
      return datasetId;
    } catch (err: any) {
      let errorMessage = err.response?.data?.detail || err.message || 'Failed to create dataset';
      
      // Handle 402 Payment Required with user-friendly message
      if (err.response?.status === 402) {
        if (errorMessage.includes('No active package')) {
          errorMessage = 'Nessun pacchetto attivo trovato. Per favore, acquista un pacchetto per creare dataset.';
        } else if (errorMessage.includes('Package exhausted')) {
          errorMessage = 'Il tuo pacchetto è esaurito. Per favore, acquista un nuovo pacchetto per continuare.';
        } else if (errorMessage.includes('Domain')) {
          errorMessage = `Dominio non incluso nel tuo pacchetto. ${errorMessage}`;
        } else {
          errorMessage = 'Pacchetto non valido o esaurito. Per favore, acquista un pacchetto per creare dataset.';
        }
      }
      
      setError(errorMessage);
      setIsCreating(false);
      throw err;
    }
  }, []);

  return {
    createDataset,
    isCreating,
    error
  };
}

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
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to create dataset';
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

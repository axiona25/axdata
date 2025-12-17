import { CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import type { DatasetSpec } from '../../types';

interface ConfirmStepProps {
  dsSpec: DatasetSpec;
  onConfirm: () => void;
  onBack: () => void;
  isCreating: boolean;
  error: string | null;
}

export default function ConfirmStep({ 
  dsSpec, 
  onConfirm, 
  onBack, 
  isCreating, 
  error 
}: ConfirmStepProps) {
  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-text-primary mb-2">Conferma Creazione Dataset</h3>
        <p className="text-sm text-text-secondary">
          Verifica le informazioni e conferma per creare il dataset.
        </p>
      </div>

      {/* DS-SPEC Summary */}
      <div className="bg-dark-secondary rounded-input p-4 space-y-3">
        <div>
          <span className="text-sm font-medium text-text-primary">Query:</span>
          <p className="text-text-secondary text-sm mt-1">{dsSpec.request.query_text}</p>
        </div>
        <div>
          <span className="text-sm font-medium text-text-primary">Settore:</span>
          <p className="text-text-secondary text-sm mt-1 capitalize">{dsSpec.sector}</p>
        </div>
        <div>
          <span className="text-sm font-medium text-text-primary">Template:</span>
          <p className="text-text-secondary text-sm mt-1">{dsSpec.output.template}</p>
        </div>
        <div>
          <span className="text-sm font-medium text-text-primary">Formati:</span>
          <p className="text-text-secondary text-sm mt-1">{dsSpec.output.formats.join(', ')}</p>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-500/20 border border-red-500/50 rounded-input p-4 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-sm font-medium text-red-500 mb-1">Errore</p>
            <p className="text-sm text-red-400 mb-3">{error}</p>
            {(error.includes('package') || error.includes('Package') || error.includes('pacchetto') || error.includes('No active package')) && (
              <a
                href="/dashboard/packages"
                className="inline-block px-4 py-2 bg-accent-blue text-white rounded-input text-sm font-medium hover:bg-accent-blue/90 transition-colors"
              >
                Acquista un Pacchetto
              </a>
            )}
          </div>
        </div>
      )}

      {/* Info Message */}
      <div className="bg-accent-blue/20 border border-accent-blue/50 rounded-input p-4 flex items-start gap-3">
        <CheckCircle className="w-5 h-5 text-accent-blue flex-shrink-0 mt-0.5" />
        <div>
          <p className="text-sm font-medium text-accent-blue mb-1">Cosa succederà</p>
          <ul className="text-sm text-text-secondary space-y-1 list-disc list-inside">
            <li>Il dataset verrà creato e processato automaticamente</li>
            <li>Riceverai una notifica quando sarà pronto</li>
            <li>Potrai visualizzarlo e scaricarlo dalla pagina Dataset</li>
          </ul>
        </div>
      </div>
    </div>
  );
}

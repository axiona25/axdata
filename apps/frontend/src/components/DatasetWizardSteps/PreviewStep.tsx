import { Database, Globe, Calendar, Tag, FileText, CheckCircle, Info } from 'lucide-react';
import type { DatasetPlan } from '../../types';

interface PreviewStepProps {
  datasetPlan: DatasetPlan;
  onConfirm: () => void;
  onBack: () => void;
}

// Mappa nomi fonti più leggibili
const sourceNames: Record<string, string> = {
  istat: 'ISTAT (Istituto Nazionale di Statistica)',
  eurostat: 'Eurostat',
  worldbank: 'World Bank',
  imf: 'Fondo Monetario Internazionale',
  oecd: 'OCSE',
  pubmed: 'PubMed',
  clinicaltrials: 'ClinicalTrials.gov',
  nasa: 'NASA',
  cern_opendata: 'CERN Open Data',
  un_data: 'Nazioni Unite',
  who_gho: 'Organizzazione Mondiale della Sanità',
};

// Mappa domini più leggibili
const domainNames: Record<string, string> = {
  economics: 'Economia',
  demography: 'Demografia',
  biomedical: 'Biomedico',
  physics: 'Fisica',
  math: 'Matematica',
};

export default function PreviewStep({ datasetPlan, onConfirm, onBack }: PreviewStepProps) {
  const getSourceDisplayName = (connector: string) => {
    return sourceNames[connector.toLowerCase()] || connector.toUpperCase();
  };

  const getDomainDisplayName = (domain: string) => {
    return domainNames[domain.toLowerCase()] || domain;
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-xl font-semibold text-text-primary mb-2">Riepilogo Dataset</h3>
        <p className="text-sm text-text-secondary">
          L'AI ha preparato il tuo dataset. Ecco cosa verrà creato:
        </p>
      </div>

      {/* Card principale con informazioni chiave */}
      <div className="bg-dark-card border border-dark-secondary rounded-input p-6 space-y-6">
        {/* Titolo Dataset */}
        <div className="pb-4 border-b border-dark-secondary">
          <div className="flex items-start gap-3">
            <div className="p-2 bg-accent-blue/20 rounded-lg">
              <FileText className="w-5 h-5 text-accent-blue" />
            </div>
            <div className="flex-1">
              <h4 className="text-lg font-semibold text-text-primary mb-1">{datasetPlan.title}</h4>
              <p className="text-sm text-text-secondary">
                Categoria: <span className="text-text-primary font-medium">{getDomainDisplayName(datasetPlan.domain)}</span>
              </p>
            </div>
          </div>
        </div>

        {/* Fonti Dati */}
        {datasetPlan.sources && datasetPlan.sources.length > 0 && (
          <div>
            <div className="flex items-center gap-2 mb-3">
              <Database className="w-5 h-5 text-accent-blue" />
              <h5 className="text-base font-semibold text-text-primary">Fonti dei Dati</h5>
            </div>
            <div className="space-y-2">
              {datasetPlan.sources.map((source, idx) => (
                <div key={idx} className="bg-dark-secondary rounded-input p-3 flex items-center gap-3">
                  <CheckCircle className="w-4 h-4 text-green-400 flex-shrink-0" />
                  <div>
                    <p className="text-sm font-medium text-text-primary">{getSourceDisplayName(source.connector)}</p>
                    <p className="text-xs text-text-secondary mt-0.5">Fonte ufficiale e verificata</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Copertura Geografica e Temporale */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {datasetPlan.geographic_coverage && (
            <div className="bg-dark-secondary rounded-input p-4">
              <div className="flex items-center gap-2 mb-2">
                <Globe className="w-4 h-4 text-accent-blue" />
                <span className="text-sm font-semibold text-text-primary">Area Geografica</span>
              </div>
              <p className="text-sm text-text-secondary">{datasetPlan.geographic_coverage}</p>
            </div>
          )}

          {datasetPlan.temporal_coverage && (
            <div className="bg-dark-secondary rounded-input p-4">
              <div className="flex items-center gap-2 mb-2">
                <Calendar className="w-4 h-4 text-accent-blue" />
                <span className="text-sm font-semibold text-text-primary">Periodo Temporale</span>
              </div>
              <p className="text-sm text-text-secondary">{datasetPlan.temporal_coverage}</p>
            </div>
          )}
        </div>

        {/* Formati di Output */}
        {datasetPlan.outputs && datasetPlan.outputs.length > 0 && (
          <div>
            <div className="flex items-center gap-2 mb-3">
              <Tag className="w-5 h-5 text-accent-blue" />
              <h5 className="text-base font-semibold text-text-primary">Formati Disponibili</h5>
            </div>
            <div className="flex flex-wrap gap-2">
              {datasetPlan.outputs.map((format, idx) => (
                <span
                  key={idx}
                  className="px-3 py-1.5 bg-accent-blue/20 text-accent-blue rounded-full text-sm font-medium"
                >
                  {format.toUpperCase()}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Info Box */}
        <div className="bg-accent-blue/10 border border-accent-blue/30 rounded-input p-4">
          <div className="flex items-start gap-3">
            <Info className="w-5 h-5 text-accent-blue flex-shrink-0 mt-0.5" />
            <div className="text-sm text-text-secondary">
              <p className="font-medium text-text-primary mb-1">Cosa succederà ora?</p>
              <ul className="space-y-1 list-disc list-inside">
                <li>Il sistema raccoglierà i dati dalle fonti indicate</li>
                <li>I dati verranno elaborati e validati automaticamente</li>
                <li>Riceverai una notifica quando il dataset sarà pronto</li>
                <li>Potrai scaricare il dataset nei formati selezionati</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

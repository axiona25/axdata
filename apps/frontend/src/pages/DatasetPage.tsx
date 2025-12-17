import { useState, useMemo, useEffect } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Database,
  Download,
  Edit,
  Trash2,
  MoreVertical,
  ChevronLeft,
  ChevronRight,
  Search,
  Plus,
  Clock,
  CheckCircle,
  X,
} from 'lucide-react';
import Layout from '../components/Layout';
import DatasetWizard from '../components/DatasetWizard';
import { api } from '../lib/api';

export default function DatasetPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [actionMenuOpen, setActionMenuOpen] = useState<number | null>(null);
  const [wizardOpen, setWizardOpen] = useState(false);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [selectedDatasetId, setSelectedDatasetId] = useState<string | null>(null);
  const itemsPerPage = 12;

  const queryClient = useQueryClient();

  type DatasetRow = {
    id: string;
    code: string;
    name: string;
    createdAt: string;
    price: string;
    status: 'paid' | 'to_pay' | 'processing';
  };

  const mapStatus = (s: string): DatasetRow['status'] => {
    if (s === 'paid' || s === 'delivered') return 'paid';
    if (s === 'ready_for_payment') return 'to_pay';
    if (s === 'running' || s === 'draft') return 'processing';
    return 'processing';
  };

  const formatDate = (iso: string | null | undefined) => {
    if (!iso) return '-';
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return iso;
    return d.toLocaleDateString('it-IT');
  };

  const { data: datasetsApi } = useQuery({
    queryKey: ['datasetsList'],
    queryFn: async () => (await api.get('/api/v1/datasets?limit=500')).data,
  });

  const allDatasets: DatasetRow[] = Array.isArray(datasetsApi)
    ? datasetsApi.map((d: any) => ({
        id: String(d.id),
        code: String(d.id).slice(0, 8).toUpperCase(),
        name: String(d.title || 'Dataset'),
        createdAt: formatDate(d.created_at),
        price: '-', // Prezzo per dataset non ancora esposto: gestito da pacchetti
        status: mapStatus(String(d.status)),
      }))
    : [];

  const getStatusPill = (status: string) => {
    switch (status) {
      case 'paid':
        return (
          <span className="px-3 py-1 rounded-full bg-green-500/20 text-green-500 text-sm font-medium">
            Pagato
          </span>
        );
      case 'to_pay':
        return (
          <span className="px-3 py-1 rounded-full bg-orange-500/20 text-orange-500 text-sm font-medium">
            Da pagare
          </span>
        );
      case 'processing':
        return (
          <span className="px-3 py-1 rounded-full bg-accent-blue/20 text-accent-blue text-sm font-medium">
            In elaborazione
          </span>
        );
      default:
        return (
          <span className="px-3 py-1 rounded-full bg-dark-secondary text-text-secondary text-sm font-medium">
            Unknown
          </span>
        );
    }
  };

  // Filtraggio e paginazione
  const filteredDatasets = useMemo(() => {
    if (!searchQuery.trim()) {
      return allDatasets;
    }
    const query = searchQuery.toLowerCase();
    return allDatasets.filter(
      (item) =>
        item.code.toLowerCase().includes(query) ||
        item.name.toLowerCase().includes(query) ||
        item.createdAt.toLowerCase().includes(query) ||
        item.price.toLowerCase().includes(query) ||
        item.status.toLowerCase().includes(query)
    );
  }, [searchQuery]);

  const totalPages = Math.ceil(filteredDatasets.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const paginatedDatasets = filteredDatasets.slice(startIndex, endIndex);
  
  // Sempre 12 righe per pagina (con dati o vuote)
  const minRows = 12;
  const emptyRowsCount = Math.max(0, minRows - paginatedDatasets.length);
  
  // Calcola il range per il contatore (sempre 12 per pagina)
  const displayStart = startIndex + 1;
  const displayEnd = Math.min(startIndex + minRows, filteredDatasets.length);

  // Calcola statistiche
  const totalCreated = allDatasets.length;
  const totalProcessing = allDatasets.filter(d => d.status === 'processing').length;
  const totalPaid = allDatasets.filter(d => d.status === 'paid').length;

  // Reset alla prima pagina quando cambia la ricerca
  useEffect(() => {
    setCurrentPage(1);
  }, [searchQuery]);

  // Blocca lo scroll verticale della pagina
  useEffect(() => {
    document.body.style.overflowY = 'hidden';
    return () => {
      document.body.style.overflowY = 'auto';
    };
  }, []);

  const { data: previewData } = useQuery({
    queryKey: ['datasetPreview', selectedDatasetId],
    queryFn: async () => (await api.get(`/api/v1/datasets/${selectedDatasetId}/preview`)).data,
    enabled: !!selectedDatasetId && previewOpen,
  });

  const previewPercent = Number(previewData?.meta?.preview_percent ?? 15);
  const watermark = Boolean(previewData?.meta?.watermark ?? true);
  const canDownload = Boolean(previewData?.meta?.can_download ?? false);
  const previewRows: Array<Record<string, any>> = Array.isArray(previewData?.rows) ? previewData.rows : [];

  const previewColumns = useMemo(() => {
    const first = previewRows[0];
    if (!first) return [];
    return Object.keys(first).slice(0, 8); // keep UI compact
  }, [previewRows]);

  const handleDownload = async (datasetId: string) => {
    try {
      const res = await api.get(`/api/v1/download/datasets/${datasetId}`);
      const url = res.data?.signed_url;
      if (url) {
        window.open(url, '_blank');
      }
    } catch (e: any) {
      // If locked, redirect user to plans page
      const msg = e?.response?.data?.detail || e?.message || 'Download non disponibile';
      alert(msg);
    }
  };

  return (
    <Layout 
      searchQuery={searchQuery} 
      onSearchChange={setSearchQuery}
      headerTitle="Dataset"
      headerSubtitle="Gestisci e visualizza tutti i tuoi dataset"
    >
      <div className="space-y-6">
        {/* Statistiche e Button Nuovo */}
        <div className="flex items-center justify-between">
          {/* Badge Statistiche */}
          <div className="flex items-center gap-4">
            {/* Badge Totale Dataset Creati */}
            <div 
              className="card text-white flex items-center justify-between border px-4 py-2.5"
              style={{
                background: 'linear-gradient(to bottom, #181f25, #064e7e)',
                borderColor: '#007ed2',
                minWidth: '180px',
              }}
            >
              <div>
                <p className="text-xs opacity-90 font-medium mb-0.5">Dataset Creati</p>
                <p className="text-xl font-semibold">{totalCreated}</p>
              </div>
              <div className="p-2 bg-white/10 rounded-full">
                <Database className="w-4 h-4" />
              </div>
            </div>

            {/* Badge Totale Dataset in Elaborazione */}
            <div 
              className="card text-white flex items-center justify-between border px-4 py-2.5"
              style={{
                background: 'linear-gradient(to bottom, #181f25, #064e7e)',
                borderColor: '#007ed2',
                minWidth: '180px',
              }}
            >
              <div>
                <p className="text-xs opacity-90 font-medium mb-0.5">In Elaborazione</p>
                <p className="text-xl font-semibold">{totalProcessing}</p>
              </div>
              <div className="p-2 bg-white/10 rounded-full">
                <Clock className="w-4 h-4" />
              </div>
            </div>

            {/* Badge Totale Dataset Pagati */}
            <div 
              className="card text-white flex items-center justify-between border px-4 py-2.5"
              style={{
                background: 'linear-gradient(to bottom, #181f25, #064e7e)',
                borderColor: '#007ed2',
                minWidth: '180px',
              }}
            >
              <div>
                <p className="text-xs opacity-90 font-medium mb-0.5">Dataset Pagati</p>
                <p className="text-xl font-semibold">{totalPaid}</p>
              </div>
              <div className="p-2 bg-white/10 rounded-full">
                <CheckCircle className="w-4 h-4 text-green-400" />
              </div>
            </div>
          </div>

          {/* Button Nuovo */}
          <button
            onClick={() => setWizardOpen(true)}
            className="px-6 py-3 text-white rounded-input border border-white transition-colors flex items-center gap-2"
            style={{ backgroundColor: '#0180d1' }}
          >
            <Plus className="w-5 h-5" />
            Nuovo
          </button>
        </div>

        {/* Tabella Dataset */}
        <div className="card border" style={{ borderColor: '#007ed2' }}>
          <div className="overflow-x-auto overflow-y-visible">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="text-text-secondary border-b border-dark-secondary">
                  <th className="py-3">Codice DataSet</th>
                  <th className="py-3">Nome DataSet</th>
                  <th className="py-3">Data di creazione</th>
                  <th className="py-3">Prezzo pagato</th>
                  <th className="py-3">Stato</th>
                  <th className="py-3">Dataset</th>
                  <th className="py-3">Azioni</th>
                </tr>
              </thead>
              <tbody>
                {paginatedDatasets.length > 0 ? (
                  <>
                    {paginatedDatasets.map((item) => (
                      <tr key={item.id} className="text-text-primary border-b border-dark-secondary hover:bg-dark-secondary/50 transition-colors cursor-pointer">
                        <td className="py-3">{item.code}</td>
                        <td className="py-3">{item.name}</td>
                        <td className="py-3">{item.createdAt}</td>
                        <td className="py-3">{item.price}</td>
                        <td className="py-3">{getStatusPill(item.status)}</td>
                        <td className="py-3">
                          <button
                            className="p-2 rounded-input hover:bg-dark-secondary transition-colors"
                            title="Apri Dataset"
                            onClick={() => {
                              setSelectedDatasetId(item.id);
                              setPreviewOpen(true);
                            }}
                          >
                            <Database className="w-5 h-5 text-accent-blue" />
                          </button>
                        </td>
                        <td className="py-3">
                          <div className="relative">
                            <button
                              className="p-2 rounded-input hover:bg-dark-secondary transition-colors"
                              onClick={() =>
                                setActionMenuOpen(
                                  actionMenuOpen === item.id ? null : item.id
                                )
                              }
                            >
                              <MoreVertical className="w-5 h-5 text-text-secondary" />
                            </button>
                          {actionMenuOpen === item.id && (
                            <div className="absolute right-0 bottom-full mb-2 w-48 bg-dark-card border border-dark-secondary rounded-input shadow-lg z-50">
                                <button
                                  className="w-full px-4 py-2 text-left text-sm text-text-primary hover:bg-dark-secondary flex items-center gap-2"
                                  onClick={() => {
                                    console.log('Modifica:', item.code);
                                    setActionMenuOpen(null);
                                  }}
                                >
                                  <Edit className="w-4 h-4" />
                                  Modifica
                                </button>
                                <button
                                  className="w-full px-4 py-2 text-left text-sm text-text-primary hover:bg-dark-secondary flex items-center gap-2"
                                  onClick={() => {
                                    console.log('Elimina:', item.code);
                                    setActionMenuOpen(null);
                                  }}
                                >
                                  <Trash2 className="w-4 h-4" />
                                  Elimina
                                </button>
                                <button
                                  className="w-full px-4 py-2 text-left text-sm text-text-primary hover:bg-dark-secondary flex items-center gap-2"
                                  onClick={() => {
                                    handleDownload(item.id);
                                    setActionMenuOpen(null);
                                  }}
                                >
                                  <Download className="w-4 h-4" />
                                  Scarica
                                </button>
                              </div>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                    {Array.from({ length: emptyRowsCount }).map((_, index) => (
                      <tr key={`empty-${index}`} className="text-text-primary" style={{ borderBottom: '1px solid transparent' }}>
                        <td className="py-3">&nbsp;</td>
                        <td className="py-3">&nbsp;</td>
                        <td className="py-3">&nbsp;</td>
                        <td className="py-3">&nbsp;</td>
                        <td className="py-3">&nbsp;</td>
                        <td className="py-3">&nbsp;</td>
                        <td className="py-3">&nbsp;</td>
                      </tr>
                    ))}
                  </>
                ) : (
                  <>
                    <tr className="border-b border-dark-secondary">
                      <td colSpan={7} className="py-3 text-center text-text-secondary">
                        Nessun dataset trovato
                      </td>
                    </tr>
                    {Array.from({ length: minRows - 1 }).map((_, index) => (
                      <tr key={`empty-${index}`} className="text-text-primary" style={{ borderBottom: '1px solid transparent' }}>
                        <td className="py-3">&nbsp;</td>
                        <td className="py-3">&nbsp;</td>
                        <td className="py-3">&nbsp;</td>
                        <td className="py-3">&nbsp;</td>
                        <td className="py-3">&nbsp;</td>
                        <td className="py-3">&nbsp;</td>
                        <td className="py-3">&nbsp;</td>
                      </tr>
                    ))}
                  </>
                )}
              </tbody>
            </table>
          </div>

          {/* Footer con paginazione */}
          <div className="border-t border-dark-secondary px-4 py-4 flex items-center justify-between">
            <div className="text-sm text-text-secondary">
              Mostrando {displayStart} - {displayEnd} di {filteredDatasets.length} dataset
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setCurrentPage((prev) => Math.max(1, prev - 1))}
                disabled={currentPage === 1}
                className="p-2 rounded-input hover:bg-dark-secondary transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronLeft className="w-5 h-5 text-text-secondary" />
              </button>
              <div className="flex items-center gap-1">
                {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
                  <button
                    key={page}
                    onClick={() => setCurrentPage(page)}
                    className={`px-3 py-1 rounded-input text-sm transition-colors ${
                      currentPage === page
                        ? 'bg-accent-blue text-white'
                        : 'text-text-secondary hover:bg-dark-secondary'
                    }`}
                  >
                    {page}
                  </button>
                ))}
              </div>
              <button
                onClick={() =>
                  setCurrentPage((prev) => Math.min(totalPages, prev + 1))
                }
                disabled={currentPage === totalPages}
                className="p-2 rounded-input hover:bg-dark-secondary transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronRight className="w-5 h-5 text-text-secondary" />
              </button>
            </div>
          </div>
        </div>
      </div>
      
      {/* Dataset Wizard Modal */}
      <DatasetWizard
        isOpen={wizardOpen}
        onClose={() => setWizardOpen(false)}
        onSuccess={(datasetId) => {
          console.log('Dataset created:', datasetId);
          setWizardOpen(false);
          queryClient.invalidateQueries({ queryKey: ['datasetsList'] });
        }}
      />

      {/* Preview modal with watermark + 15% gating */}
      {previewOpen && selectedDatasetId && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
          <div className="bg-dark-card border border-dark-secondary rounded-lg w-full max-w-4xl max-h-[90vh] flex flex-col">
            <div className="flex items-center justify-between p-6 border-b border-dark-secondary">
              <div>
                <div className="text-xl font-semibold text-text-primary">Anteprima Dataset</div>
                <div className="text-sm text-text-secondary mt-1">
                  {canDownload ? 'Accesso completo abilitato' : `Accesso limitato: visualizzazione ${previewPercent}%`}
                </div>
              </div>
              <button
                onClick={() => {
                  setPreviewOpen(false);
                  setSelectedDatasetId(null);
                }}
                className="p-2 rounded-input hover:bg-dark-secondary transition-colors"
              >
                <X className="w-5 h-5 text-text-secondary" />
              </button>
            </div>

            <div className="flex-1 overflow-auto p-6">
              <div className="relative">
                <div className="overflow-x-auto bg-dark-secondary/40 rounded-input border border-dark-secondary">
                  <table className="w-full text-left text-sm">
                    <thead>
                      <tr className="text-text-secondary border-b border-dark-secondary">
                        <th className="py-3 px-4">#</th>
                        {previewColumns.map((c) => (
                          <th key={c} className="py-3 px-4">{c}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-dark-secondary">
                      {previewRows.length === 0 ? (
                        <tr className="text-text-primary">
                          <td className="py-3 px-4 text-text-secondary" colSpan={previewColumns.length + 1}>
                            Anteprima non disponibile (dataset in elaborazione o bundle non pronto).
                          </td>
                        </tr>
                      ) : (
                        previewRows.map((r, idx) => (
                          <tr key={idx} className="text-text-primary">
                            <td className="py-3 px-4">{idx + 1}</td>
                            {previewColumns.map((c) => (
                              <td key={c} className={`py-3 px-4 ${!canDownload ? 'blur-sm select-none' : ''}`}>
                                {String(r?.[c] ?? '')}
                              </td>
                            ))}
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>

                {watermark && (
                  <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
                    <div className="rotate-[-20deg] text-white/10 text-6xl font-black tracking-widest select-none">
                      AXDATA · PREVIEW
                    </div>
                  </div>
                )}
              </div>

              {!canDownload && (
                <div className="mt-4 p-4 bg-orange-500/10 border border-orange-500/50 rounded-input">
                  <div className="text-sm text-orange-400">
                    Per vedere e scaricare il dataset completo, acquista un pacchetto in “Pagamenti e Fatture → Gestione Piani”.
                  </div>
                </div>
              )}
            </div>

            <div className="flex items-center justify-end gap-3 p-6 border-t border-dark-secondary">
              {!canDownload && (
                <button
                  onClick={() => (window.location.href = '/dashboard/billing')}
                  className="px-4 py-2 bg-dark-secondary text-text-primary rounded-input hover:bg-dark-secondary/80 transition-colors"
                >
                  Vai ai Piani
                </button>
              )}
              <button
                onClick={() => handleDownload(selectedDatasetId)}
                disabled={!canDownload}
                className="px-4 py-2 bg-accent-blue text-white rounded-input hover:bg-accent-blue/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                <Download className="w-4 h-4" />
                Scarica
              </button>
            </div>
          </div>
        </div>
      )}
    </Layout>
  );
}

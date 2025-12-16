import { useState, useMemo, useEffect } from 'react';
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
} from 'lucide-react';
import Layout from '../components/Layout';
import DatasetWizard from '../components/DatasetWizard';

export default function DatasetPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [actionMenuOpen, setActionMenuOpen] = useState<number | null>(null);
  const [wizardOpen, setWizardOpen] = useState(false);
  const itemsPerPage = 12;

  // Dati mock estesi (simulando più dataset)
  const allDatasets = [
    {
      id: 1,
      code: 'DS-ECON-2024-001',
      name: 'GDP Growth Rates - European Union (2010-2024)',
      createdAt: '15/03/2024',
      price: '€ 450.00',
      status: 'paid',
    },
    {
      id: 2,
      code: 'DS-ECON-2024-002',
      name: 'Inflation Data - OECD Countries',
      createdAt: '22/03/2024',
      price: '€ 320.00',
      status: 'paid',
    },
    {
      id: 3,
      code: 'DS-ECON-2024-003',
      name: 'Unemployment Statistics - Eurozone',
      createdAt: '05/04/2024',
      price: '€ 280.00',
      status: 'processing',
    },
    {
      id: 4,
      code: 'DS-ECON-2024-004',
      name: 'Trade Balance - G7 Nations',
      createdAt: '18/04/2024',
      price: '€ 510.00',
      status: 'to_pay',
    },
    {
      id: 5,
      code: 'DS-ECON-2024-005',
      name: 'Central Bank Interest Rates - Global',
      createdAt: '28/04/2024',
      price: '€ 380.00',
      status: 'paid',
    },
    {
      id: 6,
      code: 'DS-BIO-2024-001',
      name: 'Clinical Trial Data - Phase III Studies',
      createdAt: '10/01/2024',
      price: '€ 620.00',
      status: 'paid',
    },
    {
      id: 7,
      code: 'DS-BIO-2024-002',
      name: 'Genomic Sequencing - Cancer Research',
      createdAt: '25/01/2024',
      price: '€ 890.00',
      status: 'paid',
    },
    {
      id: 8,
      code: 'DS-PHYS-2024-001',
      name: 'Particle Physics Experiments - CERN Data',
      createdAt: '12/02/2024',
      price: '€ 750.00',
      status: 'processing',
    },
    {
      id: 9,
      code: 'DS-MATH-2024-001',
      name: 'Statistical Models - Machine Learning',
      createdAt: '08/03/2024',
      price: '€ 420.00',
      status: 'paid',
    },
    {
      id: 10,
      code: 'DS-ECON-2024-006',
      name: 'Market Volatility Index - Global Markets',
      createdAt: '30/04/2024',
      price: '€ 550.00',
      status: 'to_pay',
    },
    {
      id: 11,
      code: 'DS-DEMO-2024-001',
      name: 'Population Census Data - European Countries',
      createdAt: '15/05/2024',
      price: '€ 340.00',
      status: 'paid',
    },
    {
      id: 12,
      code: 'DS-ECON-2024-007',
      name: 'Consumer Price Index - Monthly Trends',
      createdAt: '20/05/2024',
      price: '€ 290.00',
      status: 'paid',
    },
    {
      id: 13,
      code: 'DS-BIO-2024-003',
      name: 'Drug Efficacy Studies - Pharmaceutical',
      createdAt: '05/06/2024',
      price: '€ 680.00',
      status: 'processing',
    },
    {
      id: 14,
      code: 'DS-PHYS-2024-002',
      name: 'Quantum Computing Experiments',
      createdAt: '18/06/2024',
      price: '€ 920.00',
      status: 'to_pay',
    },
    {
      id: 15,
      code: 'DS-MATH-2024-002',
      name: 'Cryptographic Algorithms Analysis',
      createdAt: '25/06/2024',
      price: '€ 480.00',
      status: 'paid',
    },
    {
      id: 16,
      code: 'DS-ECON-2024-008',
      name: 'Labor Market Statistics - Employment Rates',
      createdAt: '02/07/2024',
      price: '€ 360.00',
      status: 'paid',
    },
    {
      id: 17,
      code: 'DS-BIO-2024-004',
      name: 'Epidemiological Data - Disease Outbreaks',
      createdAt: '10/07/2024',
      price: '€ 540.00',
      status: 'processing',
    },
    {
      id: 18,
      code: 'DS-PHYS-2024-003',
      name: 'Astrophysics Observations - Telescope Data',
      createdAt: '22/07/2024',
      price: '€ 710.00',
      status: 'paid',
    },
    {
      id: 19,
      code: 'DS-ECON-2024-009',
      name: 'Financial Markets - Stock Exchange Data',
      createdAt: '01/08/2024',
      price: '€ 580.00',
      status: 'to_pay',
    },
    {
      id: 20,
      code: 'DS-MATH-2024-003',
      name: 'Numerical Analysis - Computational Methods',
      createdAt: '15/08/2024',
      price: '€ 410.00',
      status: 'paid',
    },
  ];

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
                              console.log('Open dataset:', item.code);
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
                                    console.log('Scarica:', item.code);
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
          // TODO: Refresh dataset list or navigate to detail page
        }}
      />
    </Layout>
  );
}

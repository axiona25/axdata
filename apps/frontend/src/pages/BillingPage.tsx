import { useEffect, useRef, useState } from 'react';
import {
  CreditCard,
  FileText,
  Edit,
  Check,
  X,
  Building2,
  User,
  MapPin,
  Hash,
  Package,
  Wallet,
  Info,
} from 'lucide-react';
import Layout from '../components/Layout';
import { api } from '../lib/api';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useLocation, useSearchParams } from 'react-router-dom';
import { authApi } from '../lib/auth';

type PaymentMethod = 'stripe' | 'paypal' | null;
type PersonType = 'fisica' | 'giuridica';

interface Payment {
  id: number;
  date: string;
  amount: string;
  method: string;
  status: 'completed' | 'pending' | 'failed';
  description: string;
}

interface Invoice {
  id: number;
  number: string;
  date: string;
  amount: string;
  status: 'paid' | 'pending' | 'overdue';
  paymentMethod: string;
}

export default function BillingPage() {
  const [activeTab, setActiveTab] = useState<'payments' | 'invoices' | 'plans'>('payments');
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>('stripe');
  const [isEditingPaymentMethod, setIsEditingPaymentMethod] = useState(false);
  const [personType, setPersonType] = useState<PersonType>('fisica');
  const [isEditingBillingInfo, setIsEditingBillingInfo] = useState(false);

  // Mock data - metodo pagamento dalla registrazione
  const [selectedPaymentMethod, setSelectedPaymentMethod] = useState<PaymentMethod>('stripe');

  const queryClient = useQueryClient();
  const [searchParams] = useSearchParams();
  const location = useLocation();
  const [unitPriceInfoOpen, setUnitPriceInfoOpen] = useState(false);
  const unitPriceInfoRef = useRef<HTMLSpanElement | null>(null);

  useEffect(() => {
    const onDocClick = (e: MouseEvent) => {
      const target = e.target as Node | null;
      if (unitPriceInfoRef.current && target && !unitPriceInfoRef.current.contains(target)) {
        setUnitPriceInfoOpen(false);
      }
    };
    document.addEventListener('mousedown', onDocClick);
    return () => document.removeEventListener('mousedown', onDocClick);
  }, []);

  useEffect(() => {
    const tab = (searchParams.get('tab') || '').toLowerCase();
    if (tab === 'plans') setActiveTab('plans');
    if (tab === 'payments') setActiveTab('payments');
    if (tab === 'invoices') setActiveTab('invoices');
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.search]);

  // Wallet (shared with header)
  const { data: walletSummary } = useQuery({
    queryKey: ['walletSummary'],
    queryFn: async () => (await api.get('/api/v1/wallet/summary')).data,
  });

  const { data: currentUser } = useQuery({
    queryKey: ['user'],
    queryFn: authApi.getCurrentUser,
    enabled: !!localStorage.getItem('access_token'),
    retry: false,
  });

  const canManualTopUp = (currentUser?.email || '').toLowerCase() === 'r.amoroso80@gmail.com';

  // Packages list
  const { data: packagesData, isLoading: isLoadingPlans, error: plansErrorObj } = useQuery({
    queryKey: ['packagesCatalog'],
    queryFn: async () => (await api.get('/api/v1/packages')).data,
  });

  const plansError = (plansErrorObj as any)?.message || null;
  const plans: Array<{ id: string; name: string; datasets: number; totalPrice: number; unitPrice: number }> = (packagesData?.packages ?? []).map((p: any) => {
    const totalPrice = Number(p.price ?? 0);
    const datasets = Number(p.dataset_count ?? 0);
    const unitPrice = datasets > 0 ? Number((totalPrice / datasets).toFixed(2)) : 0;
    return { id: String(p.id), name: String(p.name), datasets, totalPrice, unitPrice };
  });

  const walletBalance = Number(walletSummary?.balance ?? 0);
  const walletSpent = Number(walletSummary?.total_spent ?? 0);
  const walletLoaded = Number(walletSummary?.total_loaded ?? 0);

  // Toast system (local)
  const [toasts, setToasts] = useState<Array<{ id: string; title: string; message?: string }>>([]);
  const pushToast = (title: string, message?: string) => {
    const id = `${Date.now()}-${Math.random()}`;
    setToasts((t) => [...t, { id, title, message }]);
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 3500);
  };

  // Fire toast when plans loaded
  useEffect(() => {
    if (!isLoadingPlans && plans.length > 0) {
      pushToast('Nuovi Piani commerciali disponibili', 'Puoi acquistare un pacchetto usando il portfolio virtuale.');
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isLoadingPlans]);

  // Modals
  const [confirmPlan, setConfirmPlan] = useState<{ id: string; name: string; total: number } | null>(null);
  const [topUpOpen, setTopUpOpen] = useState(false);
  const [topUpAmount, setTopUpAmount] = useState<number>(1500);
  const [isPurchasing, setIsPurchasing] = useState<string | null>(null);
  const [isTopUping, setIsTopUping] = useState(false);

  // Mock data - coordinate fatturazione
  const [billingInfo, setBillingInfo] = useState({
    personType: 'fisica' as PersonType,
    codiceFiscale: '',
    ragioneSociale: '',
    partitaIva: '',
    sdi: '',
    address: '',
    city: '',
    postalCode: '',
    country: '',
  });

  // Mock data - storico pagamenti
  const payments: Payment[] = [
    {
      id: 1,
      date: '15/03/2024',
      amount: '€ 450.00',
      method: 'Carta di Credito',
      status: 'completed',
      description: 'Dataset: GDP Growth Rates - European Union',
    },
    {
      id: 2,
      date: '22/03/2024',
      amount: '€ 320.00',
      method: 'Carta di Credito',
      status: 'completed',
      description: 'Dataset: Inflation Data - OECD Countries',
    },
    {
      id: 3,
      date: '05/04/2024',
      amount: '€ 280.00',
      method: 'PayPal',
      status: 'pending',
      description: 'Dataset: Unemployment Statistics - Eurozone',
    },
    {
      id: 4,
      date: '18/04/2024',
      amount: '€ 510.00',
      method: 'Carta di Credito',
      status: 'failed',
      description: 'Dataset: Trade Balance - G7 Nations',
    },
    {
      id: 5,
      date: '28/04/2024',
      amount: '€ 380.00',
      method: 'Carta di Credito',
      status: 'completed',
      description: 'Dataset: Central Bank Interest Rates - Global',
    },
  ];

  // Mock data - fatture
  const invoices: Invoice[] = [
    {
      id: 1,
      number: 'FAT-2024-001',
      date: '15/03/2024',
      amount: '€ 450.00',
      status: 'paid',
      paymentMethod: 'Carta di Credito',
    },
    {
      id: 2,
      number: 'FAT-2024-002',
      date: '22/03/2024',
      amount: '€ 320.00',
      status: 'paid',
      paymentMethod: 'Carta di Credito',
    },
    {
      id: 3,
      number: 'FAT-2024-003',
      date: '28/04/2024',
      amount: '€ 380.00',
      status: 'pending',
      paymentMethod: 'Carta di Credito',
    },
  ];

  const getStatusPill = (status: string) => {
    switch (status) {
      case 'completed':
      case 'paid':
        return (
          <span className="px-3 py-1 rounded-full bg-green-500/20 text-green-500 text-sm font-medium">
            Completato
          </span>
        );
      case 'pending':
        return (
          <span className="px-3 py-1 rounded-full bg-orange-500/20 text-orange-500 text-sm font-medium">
            In attesa
          </span>
        );
      case 'failed':
      case 'overdue':
        return (
          <span className="px-3 py-1 rounded-full bg-red-500/20 text-red-500 text-sm font-medium">
            Fallito
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

  const handleSavePaymentMethod = () => {
    setSelectedPaymentMethod(paymentMethod);
    setIsEditingPaymentMethod(false);
  };

  const handleSaveBillingInfo = () => {
    setIsEditingBillingInfo(false);
    // Qui salveresti i dati al backend
  };

  return (
    <Layout headerTitle="Pagamenti e Fatture" headerSubtitle="Gestisci i tuoi pagamenti e le fatture">
      <div className="space-y-6">
        {/* Toasts */}
        {toasts.length > 0 && (
          <div className="fixed top-4 right-4 z-50 space-y-2">
            {toasts.map((t) => (
              <div key={t.id} className="bg-dark-secondary border border-dark-secondary rounded-input px-4 py-3 shadow-lg w-80">
                <div className="text-sm font-semibold text-text-primary">{t.title}</div>
                {t.message && <div className="text-xs text-text-secondary mt-1">{t.message}</div>}
              </div>
            ))}
          </div>
        )}

        {/* Tabs */}
        <div className="flex gap-4 border-b border-dark-secondary">
          <button
            onClick={() => setActiveTab('payments')}
            className={`px-4 py-3 font-semibold transition-colors border-b-2 ${
              activeTab === 'payments'
                ? 'text-white border-accent-blue'
                : 'text-text-secondary border-transparent hover:text-text-primary'
            }`}
          >
            Pagamenti
          </button>
          <button
            onClick={() => setActiveTab('invoices')}
            className={`px-4 py-3 font-semibold transition-colors border-b-2 ${
              activeTab === 'invoices'
                ? 'text-white border-accent-blue'
                : 'text-text-secondary border-transparent hover:text-text-primary'
            }`}
          >
            Fatture
          </button>
          <button
            onClick={() => setActiveTab('plans')}
            className={`px-4 py-3 font-semibold transition-colors border-b-2 ${
              activeTab === 'plans'
                ? 'text-white border-accent-blue'
                : 'text-text-secondary border-transparent hover:text-text-primary'
            }`}
          >
            Gestione Piani
          </button>
        </div>

        {/* Tab Content */}
        {activeTab === 'payments' ? (
          <div className="space-y-6">
            {/* Metodo di Pagamento */}
            <div className="card border" style={{ borderColor: '#007ed2' }}>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-text-primary">Metodo di Pagamento</h3>
                {!isEditingPaymentMethod && (
                  <button
                    onClick={() => setIsEditingPaymentMethod(true)}
                    className="flex items-center gap-2 px-3 py-1.5 rounded-input hover:bg-dark-secondary transition-colors text-sm text-text-secondary hover:text-text-primary"
                  >
                    <Edit className="w-4 h-4" />
                    Modifica
                  </button>
                )}
              </div>

              {!isEditingPaymentMethod ? (
                <div className="space-y-3">
                  <div className="flex items-center gap-3 p-4 bg-dark-secondary rounded-input">
                    <CreditCard className="w-5 h-5 text-accent-blue" />
                    <div className="flex-1">
                      <div className="text-sm font-semibold text-text-primary">
                        {selectedPaymentMethod === 'stripe'
                          ? 'Carta di Credito (Stripe)'
                          : selectedPaymentMethod === 'paypal'
                          ? 'PayPal'
                          : 'Nessun metodo selezionato'}
                      </div>
                      {selectedPaymentMethod && (
                        <div className="text-xs text-text-secondary mt-1">
                          Metodo di pagamento attivo
                        </div>
                      )}
                    </div>
                  </div>
                  {!selectedPaymentMethod && (
                    <div className="p-4 bg-orange-500/10 border border-orange-500/50 rounded-input">
                      <p className="text-sm text-orange-400">
                        ⚠️ Completa la configurazione del metodo di pagamento per utilizzare i
                        crediti e acquistare nuovi dataset.
                      </p>
                    </div>
                  )}
                </div>
              ) : (
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-text-secondary mb-2">
                      Seleziona Metodo di Pagamento
                    </label>
                    <div className="space-y-2">
                      <label className="flex items-center gap-3 p-4 bg-dark-secondary rounded-input cursor-pointer hover:bg-dark-secondary/80 transition-colors">
                        <input
                          type="radio"
                          name="paymentMethod"
                          value="stripe"
                          checked={paymentMethod === 'stripe'}
                          onChange={(e) => setPaymentMethod(e.target.value as PaymentMethod)}
                          className="w-4 h-4 text-accent-blue"
                        />
                        <CreditCard className="w-5 h-5 text-accent-blue" />
                        <div>
                          <div className="text-sm font-semibold text-text-primary">
                            Carta di Credito
                          </div>
                          <div className="text-xs text-text-secondary">
                            Visa, Mastercard, American Express
                          </div>
                        </div>
                      </label>
                      <label className="flex items-center gap-3 p-4 bg-dark-secondary rounded-input cursor-pointer hover:bg-dark-secondary/80 transition-colors">
                        <input
                          type="radio"
                          name="paymentMethod"
                          value="paypal"
                          checked={paymentMethod === 'paypal'}
                          onChange={(e) => setPaymentMethod(e.target.value as PaymentMethod)}
                          className="w-4 h-4 text-accent-blue"
                        />
                        <CreditCard className="w-5 h-5 text-accent-blue" />
                        <div>
                          <div className="text-sm font-semibold text-text-primary">PayPal</div>
                          <div className="text-xs text-text-secondary">
                            Paga con il tuo account PayPal
                          </div>
                        </div>
                      </label>
                    </div>
                  </div>
                  <div className="flex gap-3">
                    <button
                      onClick={handleSavePaymentMethod}
                      className="px-4 py-2 bg-accent-blue text-white rounded-input hover:bg-accent-blue/90 transition-colors flex items-center gap-2"
                    >
                      <Check className="w-4 h-4" />
                      Conferma
                    </button>
                    <button
                      onClick={() => {
                        setIsEditingPaymentMethod(false);
                        setPaymentMethod(selectedPaymentMethod);
                      }}
                      className="px-4 py-2 bg-dark-secondary text-text-primary rounded-input hover:bg-dark-secondary/80 transition-colors flex items-center gap-2"
                    >
                      <X className="w-4 h-4" />
                      Annulla
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Storico Pagamenti */}
            <div className="card border" style={{ borderColor: '#007ed2' }}>
              <h3 className="text-lg font-semibold text-text-primary mb-4">Storico Pagamenti</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="text-text-secondary border-b border-dark-secondary">
                      <th className="py-3">Data</th>
                      <th className="py-3">Importo</th>
                      <th className="py-3">Metodo</th>
                      <th className="py-3">Descrizione</th>
                      <th className="py-3">Stato</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-dark-secondary">
                    {payments.map((payment) => (
                      <tr
                        key={payment.id}
                        className="text-text-primary border-b border-dark-secondary hover:bg-dark-secondary/50 transition-colors"
                      >
                        <td className="py-3">{payment.date}</td>
                        <td className="py-3 font-semibold">{payment.amount}</td>
                        <td className="py-3">{payment.method}</td>
                        <td className="py-3">{payment.description}</td>
                        <td className="py-3">{getStatusPill(payment.status)}</td>
                      </tr>
                    ))}
                    {/* Righe vuote per mantenere altezza */}
                    {Array.from({ length: Math.max(0, 10 - payments.length) }).map((_, index) => (
                      <tr
                        key={`empty-${index}`}
                        className="text-text-primary"
                        style={{ borderBottom: '1px solid transparent' }}
                      >
                        <td className="py-3">&nbsp;</td>
                        <td className="py-3">&nbsp;</td>
                        <td className="py-3">&nbsp;</td>
                        <td className="py-3">&nbsp;</td>
                        <td className="py-3">&nbsp;</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        ) : activeTab === 'invoices' ? (
          <div className="space-y-6">
            {/* Coordinate Fatturazione */}
            <div className="card border" style={{ borderColor: '#007ed2' }}>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-text-primary">
                  Coordinate di Fatturazione
                </h3>
                {!isEditingBillingInfo && (
                  <button
                    onClick={() => setIsEditingBillingInfo(true)}
                    className="flex items-center gap-2 px-3 py-1.5 rounded-input hover:bg-dark-secondary transition-colors text-sm text-text-secondary hover:text-text-primary"
                  >
                    <Edit className="w-4 h-4" />
                    Modifica
                  </button>
                )}
              </div>

              {!isEditingBillingInfo ? (
                <div className="space-y-3">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <div className="text-xs text-text-secondary mb-1">Tipo Persona</div>
                      <div className="text-sm font-semibold text-text-primary">
                        {billingInfo.personType === 'fisica' ? 'Persona Fisica' : 'Persona Giuridica'}
                      </div>
                    </div>
                    {billingInfo.personType === 'fisica' ? (
                      <div>
                        <div className="text-xs text-text-secondary mb-1">Codice Fiscale</div>
                        <div className="text-sm font-semibold text-text-primary">
                          {billingInfo.codiceFiscale || 'Non inserito'}
                        </div>
                      </div>
                    ) : (
                      <>
                        <div>
                          <div className="text-xs text-text-secondary mb-1">Ragione Sociale</div>
                          <div className="text-sm font-semibold text-text-primary">
                            {billingInfo.ragioneSociale || 'Non inserita'}
                          </div>
                        </div>
                        <div>
                          <div className="text-xs text-text-secondary mb-1">Partita IVA</div>
                          <div className="text-sm font-semibold text-text-primary">
                            {billingInfo.partitaIva || 'Non inserita'}
                          </div>
                        </div>
                      </>
                    )}
                  </div>
                  <div>
                    <div className="text-xs text-text-secondary mb-1">SDI (Sistema di Interscambio)</div>
                    <div className="text-sm font-semibold text-text-primary">
                      {billingInfo.sdi || 'Non inserito'}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-text-secondary mb-1">Indirizzo</div>
                    <div className="text-sm font-semibold text-text-primary">
                      {billingInfo.address || 'Non inserito'}
                    </div>
                    <div className="text-sm text-text-secondary">
                      {billingInfo.postalCode} {billingInfo.city} - {billingInfo.country}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-text-secondary mb-2">
                      Tipo Persona
                    </label>
                    <div className="flex gap-4">
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="radio"
                          name="personType"
                          value="fisica"
                          checked={personType === 'fisica'}
                          onChange={(e) => setPersonType(e.target.value as PersonType)}
                          className="w-4 h-4 text-accent-blue"
                        />
                        <User className="w-4 h-4 text-text-secondary" />
                        <span className="text-sm text-text-primary">Persona Fisica</span>
                      </label>
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="radio"
                          name="personType"
                          value="giuridica"
                          checked={personType === 'giuridica'}
                          onChange={(e) => setPersonType(e.target.value as PersonType)}
                          className="w-4 h-4 text-accent-blue"
                        />
                        <Building2 className="w-4 h-4 text-text-secondary" />
                        <span className="text-sm text-text-primary">Persona Giuridica</span>
                      </label>
                    </div>
                  </div>

                  {personType === 'fisica' ? (
                    <div>
                      <label className="block text-sm font-medium text-text-secondary mb-2">
                        Codice Fiscale
                      </label>
                      <div className="relative">
                        <Hash className="absolute left-3 top-1/2 transform -translate-y-1/2 text-text-secondary w-5 h-5" />
                        <input
                          type="text"
                          value={billingInfo.codiceFiscale}
                          onChange={(e) =>
                            setBillingInfo({ ...billingInfo, codiceFiscale: e.target.value })
                          }
                          className="input-field pl-10"
                          placeholder="Inserisci Codice Fiscale"
                        />
                      </div>
                    </div>
                  ) : (
                    <>
                      <div>
                        <label className="block text-sm font-medium text-text-secondary mb-2">
                          Ragione Sociale
                        </label>
                        <div className="relative">
                          <Building2 className="absolute left-3 top-1/2 transform -translate-y-1/2 text-text-secondary w-5 h-5" />
                          <input
                            type="text"
                            value={billingInfo.ragioneSociale}
                            onChange={(e) =>
                              setBillingInfo({ ...billingInfo, ragioneSociale: e.target.value })
                            }
                            className="input-field pl-10"
                            placeholder="Inserisci Ragione Sociale"
                          />
                        </div>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-text-secondary mb-2">
                          Partita IVA
                        </label>
                        <div className="relative">
                          <Hash className="absolute left-3 top-1/2 transform -translate-y-1/2 text-text-secondary w-5 h-5" />
                          <input
                            type="text"
                            value={billingInfo.partitaIva}
                            onChange={(e) =>
                              setBillingInfo({ ...billingInfo, partitaIva: e.target.value })
                            }
                            className="input-field pl-10"
                            placeholder="Inserisci Partita IVA"
                          />
                        </div>
                      </div>
                    </>
                  )}

                  <div>
                    <label className="block text-sm font-medium text-text-secondary mb-2">
                      SDI (Sistema di Interscambio)
                    </label>
                    <input
                      type="text"
                      value={billingInfo.sdi}
                      onChange={(e) => setBillingInfo({ ...billingInfo, sdi: e.target.value })}
                      className="input-field"
                      placeholder="Inserisci codice SDI"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-text-secondary mb-2">
                      Indirizzo Completo
                    </label>
                    <div className="relative mb-2">
                      <MapPin className="absolute left-3 top-1/2 transform -translate-y-1/2 text-text-secondary w-5 h-5" />
                      <input
                        type="text"
                        value={billingInfo.address}
                        onChange={(e) =>
                          setBillingInfo({ ...billingInfo, address: e.target.value })
                        }
                        className="input-field pl-10"
                        placeholder="Via, Numero Civico"
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <input
                        type="text"
                        value={billingInfo.city}
                        onChange={(e) => setBillingInfo({ ...billingInfo, city: e.target.value })}
                        className="input-field"
                        placeholder="Città"
                      />
                      <input
                        type="text"
                        value={billingInfo.postalCode}
                        onChange={(e) =>
                          setBillingInfo({ ...billingInfo, postalCode: e.target.value })
                        }
                        className="input-field"
                        placeholder="CAP"
                      />
                    </div>
                    <input
                      type="text"
                      value={billingInfo.country}
                      onChange={(e) => setBillingInfo({ ...billingInfo, country: e.target.value })}
                      className="input-field mt-2"
                      placeholder="Nazione"
                    />
                  </div>

                  <div className="flex gap-3">
                    <button
                      onClick={handleSaveBillingInfo}
                      className="px-4 py-2 bg-accent-blue text-white rounded-input hover:bg-accent-blue/90 transition-colors flex items-center gap-2"
                    >
                      <Check className="w-4 h-4" />
                      Salva
                    </button>
                    <button
                      onClick={() => setIsEditingBillingInfo(false)}
                      className="px-4 py-2 bg-dark-secondary text-text-primary rounded-input hover:bg-dark-secondary/80 transition-colors flex items-center gap-2"
                    >
                      <X className="w-4 h-4" />
                      Annulla
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Elenco Fatture */}
            <div className="card border" style={{ borderColor: '#007ed2' }}>
              <h3 className="text-lg font-semibold text-text-primary mb-4">Fatture</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="text-text-secondary border-b border-dark-secondary">
                      <th className="py-3">Numero Fattura</th>
                      <th className="py-3">Data</th>
                      <th className="py-3">Importo</th>
                      <th className="py-3">Metodo Pagamento</th>
                      <th className="py-3">Stato</th>
                      <th className="py-3">Azioni</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-dark-secondary">
                    {invoices.map((invoice) => (
                      <tr
                        key={invoice.id}
                        className="text-text-primary border-b border-dark-secondary hover:bg-dark-secondary/50 transition-colors"
                      >
                        <td className="py-3 font-semibold">{invoice.number}</td>
                        <td className="py-3">{invoice.date}</td>
                        <td className="py-3 font-semibold">{invoice.amount}</td>
                        <td className="py-3">{invoice.paymentMethod}</td>
                        <td className="py-3">{getStatusPill(invoice.status)}</td>
                        <td className="py-3">
                          <button
                            className="p-2 rounded-input hover:bg-dark-secondary transition-colors"
                            title="Scarica Fattura"
                          >
                            <FileText className="w-5 h-5 text-accent-blue" />
                          </button>
                        </td>
                      </tr>
                    ))}
                    {/* Righe vuote per mantenere altezza */}
                    {Array.from({ length: Math.max(0, 10 - invoices.length) }).map((_, index) => (
                      <tr
                        key={`empty-${index}`}
                        className="text-text-primary"
                        style={{ borderBottom: '1px solid transparent' }}
                      >
                        <td className="py-3">&nbsp;</td>
                        <td className="py-3">&nbsp;</td>
                        <td className="py-3">&nbsp;</td>
                        <td className="py-3">&nbsp;</td>
                        <td className="py-3">&nbsp;</td>
                        <td className="py-3">&nbsp;</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-6" id="plans">
            {/* Wallet summary */}
            <div className="card border" style={{ borderColor: '#007ed2' }}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Wallet className="w-5 h-5 text-accent-blue" />
                  <div>
                    <div className="text-sm font-semibold text-text-primary">Portfolio virtuale</div>
                    <div className="text-xs text-text-secondary">
                      Saldo disponibile: <span className="text-text-primary font-semibold">€ {walletBalance.toFixed(2)}</span> · Spesa complessiva: <span className="text-text-primary font-semibold">€ {walletSpent.toFixed(2)}</span> · Totale caricato: <span className="text-text-primary font-semibold">€ {walletLoaded.toFixed(2)}</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <div className="text-xs text-text-secondary hidden md:block">
                    Il pacchetto può essere prenotato solo se il saldo copre l’importo totale.
                  </div>
                  <button
                    onClick={() => setTopUpOpen(true)}
                    disabled={!canManualTopUp}
                    className="px-4 py-2 bg-accent-blue text-white rounded-input hover:bg-accent-blue/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    title={
                      canManualTopUp
                        ? 'Ricarica manuale (solo test)'
                        : 'Per questo account la ricarica richiede un pagamento reale'
                    }
                  >
                    Ricarica portfolio
                  </button>
                </div>
              </div>
            </div>

            {/* Plans grid */}
            {plansError && (
              <div className="p-4 bg-red-500/10 border border-red-500/50 rounded-input">
                <p className="text-sm text-red-400">{plansError}</p>
              </div>
            )}
            <div className="text-xs text-text-secondary">
              Il prezzo c.u. è calcolato come{' '}
              <span ref={unitPriceInfoRef} className="text-text-primary font-semibold inline-flex items-center gap-1 relative">
                Totale / N. Dataset{' '}
                <button
                  type="button"
                  className="inline-flex items-center justify-center"
                  onClick={() => setUnitPriceInfoOpen((v) => !v)}
                  aria-label="Informazioni sul prezzo unitario"
                >
                  <Info className="w-3.5 h-3.5 opacity-80" />
                </button>
                {unitPriceInfoOpen && (
                  <div className="absolute left-0 top-full mt-2 w-96 max-w-[80vw] bg-dark-card border border-dark-secondary rounded-input shadow-lg p-4 z-50">
                    <div className="text-sm font-semibold text-text-primary mb-2">Regole di accesso</div>
                    <ul className="text-xs text-text-secondary space-y-1 list-disc list-inside font-normal">
                      <li>Puoi generare un dataset anche senza pacchetto.</li>
                      <li>Senza pacchetto/credito non puoi scaricarlo e l’anteprima sarà limitata (15%) e con filigrane.</li>
                      <li>Quando acquisti un pacchetto, il contatore crediti scala automaticamente fino a esaurimento.</li>
                    </ul>
                  </div>
                )}
              </span>
              .
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {plans.map((p) => {
                const total = p.totalPrice;
                const canBuy = walletBalance >= total;
                const isNew = p.datasets === 50 || p.datasets === 100 || p.datasets === 200;
                return (
                  <div key={p.id} className="card border" style={{ borderColor: '#007ed2' }}>
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-input bg-dark-secondary flex items-center justify-center">
                          <Package className="w-5 h-5 text-accent-blue" />
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <div className="text-base font-semibold text-text-primary">{p.name}</div>
                            {isNew && (
                              <span className="px-2 py-0.5 rounded-full bg-accent-orange/20 text-accent-orange text-xs font-semibold">
                                Nuovo
                              </span>
                            )}
                          </div>
                          <div className="text-xs text-text-secondary mt-1">
                            Prezzo promo: <span className="text-text-primary font-semibold">€ {p.unitPrice}</span> c.u. · Totale: <span className="text-text-primary font-semibold">€ {total}</span>
                          </div>
                        </div>
                      </div>
                      <span
                        className={`px-3 py-1 rounded-full text-sm font-medium ${
                          canBuy ? 'bg-green-500/20 text-green-500' : 'bg-orange-500/20 text-orange-500'
                        }`}
                      >
                        {canBuy ? 'Disponibile' : 'Saldo insufficiente'}
                      </span>
                    </div>

                    <div className="mt-4 flex items-center justify-between">
                      <div className="text-xs text-text-secondary">
                        Richiede saldo: <span className="text-text-primary font-semibold">€ {total.toFixed(2)}</span>
                      </div>
                      <button
                        disabled={!canBuy || isPurchasing === p.id}
                        className="px-4 py-2 bg-accent-blue text-white rounded-input hover:bg-accent-blue/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        onClick={() => setConfirmPlan({ id: p.id, name: p.name, total })}
                      >
                        {isPurchasing === p.id ? 'Acquisto...' : 'Acquista'}
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>

          </div>
        )}
      </div>

      {/* Confirm purchase modal */}
      {confirmPlan && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
          <div className="bg-dark-card border border-dark-secondary rounded-lg w-full max-w-md p-6">
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="text-lg font-semibold text-text-primary">Conferma acquisto</div>
                <div className="text-sm text-text-secondary mt-1">{confirmPlan.name}</div>
              </div>
              <button
                onClick={() => setConfirmPlan(null)}
                className="p-2 rounded-input hover:bg-dark-secondary transition-colors"
              >
                <X className="w-5 h-5 text-text-secondary" />
              </button>
            </div>

            <div className="mt-4 bg-dark-secondary rounded-input p-4 space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-text-secondary">Totale pacchetto</span>
                <span className="text-text-primary font-semibold">€ {confirmPlan.total.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-secondary">Saldo disponibile</span>
                <span className="text-text-primary font-semibold">€ {walletBalance.toFixed(2)}</span>
              </div>
            </div>

            <div className="mt-5 flex gap-3 justify-end">
              <button
                onClick={() => setConfirmPlan(null)}
                className="px-4 py-2 bg-dark-secondary text-text-primary rounded-input hover:bg-dark-secondary/80 transition-colors"
              >
                Annulla
              </button>
              <button
                disabled={walletBalance < confirmPlan.total || isPurchasing === confirmPlan.id}
                onClick={async () => {
                  try {
                    setIsPurchasing(confirmPlan.id);
                    await api.post('/api/v1/packages/purchase', {
                      package_id: confirmPlan.id,
                      selected_domains: null,
                      payment_id: null,
                    });
                    await queryClient.invalidateQueries({ queryKey: ['walletSummary'] });
                    pushToast('Dataset Comprato con successo', 'Pacchetto acquistato e crediti attivati.');
                    setConfirmPlan(null);
                  } catch (e: any) {
                    pushToast('Errore acquisto', e?.response?.data?.detail || e?.message || 'Errore acquisto pacchetto');
                  } finally {
                    setIsPurchasing(null);
                  }
                }}
                className="px-4 py-2 bg-accent-blue text-white rounded-input hover:bg-accent-blue/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Conferma acquisto
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Top-up modal */}
      {topUpOpen && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
          <div className="bg-dark-card border border-dark-secondary rounded-lg w-full max-w-md p-6">
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="text-lg font-semibold text-text-primary">Ricarica portfolio</div>
                <div className="text-sm text-text-secondary mt-1">Per i test puoi caricare credito manualmente.</div>
              </div>
              <button
                onClick={() => setTopUpOpen(false)}
                className="p-2 rounded-input hover:bg-dark-secondary transition-colors"
              >
                <X className="w-5 h-5 text-text-secondary" />
              </button>
            </div>

            <div className="mt-4">
              <label className="block text-sm font-medium text-text-secondary mb-2">Importo (€)</label>
              <input
                type="number"
                value={topUpAmount}
                onChange={(e) => setTopUpAmount(Number(e.target.value))}
                className="input-field"
                min={1}
              />
            </div>

            <div className="mt-5 flex gap-3 justify-end">
              <button
                onClick={() => setTopUpOpen(false)}
                className="px-4 py-2 bg-dark-secondary text-text-primary rounded-input hover:bg-dark-secondary/80 transition-colors"
              >
                Annulla
              </button>
              <button
                disabled={topUpAmount <= 0 || isTopUping}
                onClick={async () => {
                  try {
                    setIsTopUping(true);
                    await api.post('/api/v1/wallet/credit', { amount: topUpAmount, description: 'Test top-up (dev)' });
                    await queryClient.invalidateQueries({ queryKey: ['walletSummary'] });
                    pushToast('Ricarica portfolio effettuata', `Caricati € ${topUpAmount.toFixed(2)}`);
                    setTopUpOpen(false);
                  } catch (e: any) {
                    pushToast('Errore ricarica', e?.response?.data?.detail || e?.message || 'Errore ricarica portfolio');
                  } finally {
                    setIsTopUping(false);
                  }
                }}
                className="px-4 py-2 bg-accent-blue text-white rounded-input hover:bg-accent-blue/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Conferma ricarica
              </button>
            </div>
          </div>
        </div>
      )}
    </Layout>
  );
}

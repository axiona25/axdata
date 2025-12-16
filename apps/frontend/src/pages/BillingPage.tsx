import { useState } from 'react';
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
} from 'lucide-react';
import Layout from '../components/Layout';

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
  const [activeTab, setActiveTab] = useState<'payments' | 'invoices'>('payments');
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>('stripe');
  const [isEditingPaymentMethod, setIsEditingPaymentMethod] = useState(false);
  const [personType, setPersonType] = useState<PersonType>('fisica');
  const [isEditingBillingInfo, setIsEditingBillingInfo] = useState(false);

  // Mock data - metodo pagamento dalla registrazione
  const [selectedPaymentMethod, setSelectedPaymentMethod] = useState<PaymentMethod>('stripe');

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
        ) : (
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
        )}
      </div>
    </Layout>
  );
}

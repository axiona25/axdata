import { useEffect, useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  MessageSquare,
  Database,
  CreditCard,
  TrendingUp,
  Download,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  BarChart3,
  Users,
  ArrowUpRight,
  Search,
  MoreVertical,
  Edit,
  Trash2,
  ExternalLink,
  Settings,
  Euro,
  Package,
  Wallet,
} from 'lucide-react';
import Layout from '../components/Layout';
import { authApi } from '../lib/auth';
import { api } from '../lib/api';
import { Link } from 'react-router-dom';

export default function DashboardPage() {
  const { data: userData } = useQuery({
    queryKey: ['user'],
    queryFn: authApi.getCurrentUser,
    retry: false,
    enabled: !!localStorage.getItem('access_token'), // Only run if token exists
  });

  const { data: datasetsApi } = useQuery({
    queryKey: ['datasetsList'],
    queryFn: async () => (await api.get('/api/v1/datasets?limit=500')).data,
    enabled: !!localStorage.getItem('access_token'),
    refetchOnWindowFocus: true,
  });

  const { data: walletSummary } = useQuery({
    queryKey: ['walletSummary'],
    queryFn: async () => (await api.get('/api/v1/wallet/summary')).data,
    enabled: !!localStorage.getItem('access_token'),
    retry: 1,
    refetchOnWindowFocus: true,
  });

  const { data: packagesData } = useQuery({
    queryKey: ['packagesCatalog'],
    queryFn: async () => (await api.get('/api/v1/packages')).data,
    enabled: !!localStorage.getItem('access_token'),
    refetchOnWindowFocus: true,
  });

  const { data: myPackagesData } = useQuery({
    queryKey: ['myPackages'],
    queryFn: async () => (await api.get('/api/v1/packages/my-packages')).data,
    enabled: !!localStorage.getItem('access_token'),
    retry: 0,
    refetchOnWindowFocus: true,
  });

  const mapStatus = (s: string): 'paid' | 'to_pay' | 'processing' => {
    if (s === 'paid' || s === 'delivered') return 'paid';
    if (s === 'ready_for_payment') return 'to_pay';
    if (s === 'running' || s === 'draft') return 'processing';
    return 'processing';
  };

  const formatDate = (iso: string | null | undefined) => {
    if (!iso) return '-';
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return String(iso);
    return d.toLocaleDateString('it-IT');
  };

  const allDatasets = useMemo(() => {
    if (!Array.isArray(datasetsApi)) return [];
    return datasetsApi
      .map((d: any) => ({
        id: String(d.id),
        code: String(d.id).slice(0, 8).toUpperCase(),
        name: String(d.title || 'Dataset'),
        domain: String(d.domain || 'general'),
        createdAt: formatDate(d.created_at),
        createdAtISO: d.created_at ? String(d.created_at) : null,
        price: '-', // prezzo per dataset non esposto lato API
        status: mapStatus(String(d.status)),
      }))
      .sort((a, b) => {
        const ta = a.createdAtISO ? new Date(a.createdAtISO).getTime() : 0;
        const tb = b.createdAtISO ? new Date(b.createdAtISO).getTime() : 0;
        return tb - ta;
      });
  }, [datasetsApi]);

  const recentDatasets = useMemo(() => allDatasets.slice(0, 6), [allDatasets]);

  const totalCreated = allDatasets.length;
  const totalPaid = allDatasets.filter((d) => d.status === 'paid').length;
  const totalCompleted = allDatasets.filter((d) => d.status === 'paid' || d.status === 'to_pay').length;

  const walletBalance = Number(walletSummary?.balance ?? 0);
  const walletSpent = Number(walletSummary?.total_spent ?? 0);

  const [actionMenuOpen, setActionMenuOpen] = useState<number | null>(null);
  const [hoveredMonth, setHoveredMonth] = useState<number | null>(null);

  // Dati mock per l'anno accademico (settembre-giugno)
  const academicYearData = [
    { month: 'Set', created: 3, purchased: 3 },
    { month: 'Ott', created: 5, purchased: 4 },
    { month: 'Nov', created: 7, purchased: 6 },
    { month: 'Dic', created: 6, purchased: 5 },
    { month: 'Gen', created: 9, purchased: 8 },
    { month: 'Feb', created: 11, purchased: 10 },
    { month: 'Mar', created: 10, purchased: 9 },
    { month: 'Apr', created: 8, purchased: 7 },
    { month: 'Mag', created: 7, purchased: 6 },
    { month: 'Giu', created: 5, purchased: 4 },
  ];

  const maxValue = Math.max(
    ...academicYearData.map(d => Math.max(d.created, d.purchased))
  );

  const growth = 0;

  type PlanSlide = {
    kind: 'owned' | 'promo';
    title: string;
    subtitle: string;
    meta?: string;
  };

  const planSlides: PlanSlide[] = useMemo(() => {
    const owned = Array.isArray(myPackagesData)
      ? myPackagesData.map((up: any) => {
          const pkg = up?.package;
          const name = String(pkg?.name || 'Pacchetto');
          const remaining = Number(up?.remaining_datasets ?? 0);
          const total = Number(up?.total_datasets ?? pkg?.dataset_count ?? 0);
          return {
            kind: 'owned' as const,
            title: 'Piano acquistato',
            subtitle: name,
            meta: `Crediti: ${remaining}/${total}`,
          };
        })
      : [];

    const promosRaw = Array.isArray(packagesData?.packages) ? packagesData.packages : [];
    const promos = promosRaw
      .filter((p: any) => Boolean(p?.is_active))
      .filter((p: any) => Number(p?.dataset_count ?? 0) === 50 || Number(p?.dataset_count ?? 0) === 100)
      .map((p: any) => ({
        kind: 'promo' as const,
        title: 'Promo disponibile',
        subtitle: String(p?.name || 'Piano'),
        meta: `€ ${Number(p?.price ?? 0).toLocaleString('it-IT')} · ${Number(p?.dataset_count ?? 0)} dataset`,
      }));

    const merged = [...owned, ...promos];
    if (merged.length > 0) return merged;
    return [
      {
        kind: 'promo',
        title: 'Piani disponibili',
        subtitle: 'Scopri i pacchetti e attiva nuovi crediti',
        meta: 'Vai alla gestione piani',
      },
    ];
  }, [myPackagesData, packagesData]);

  const [planSlideIndex, setPlanSlideIndex] = useState(0);

  useEffect(() => {
    if (planSlides.length <= 1) return;
    const t = window.setInterval(() => {
      setPlanSlideIndex((i) => (i + 1) % planSlides.length);
    }, 4500);
    return () => window.clearInterval(t);
  }, [planSlides.length]);

  const activePlanSlide = planSlides[planSlideIndex] ?? planSlides[0];

  const categories = useMemo(() => {
    const total = totalCreated || 0;
    const counts = new Map<string, number>();
    for (const d of allDatasets as any[]) {
      const key = String(d.domain || 'general')
        .toLowerCase()
        .trim();
      counts.set(key, (counts.get(key) || 0) + 1);
    }
    const rows = Array.from(counts.entries())
      .map(([key, count]) => {
        const label = key ? key.charAt(0).toUpperCase() + key.slice(1) : 'General';
        const percent = total > 0 ? (count / total) * 100 : 0;
        return { label, value: String(count), percent: Math.round(percent * 10) / 10 };
      })
      .sort((a, b) => Number(b.value) - Number(a.value));
    return rows.slice(0, 6);
  }, [allDatasets, totalCreated]);

  const getStatusPill = (status: string) => {
    switch (status) {
      case 'paid':
        return (
          <span className="px-3 py-1 rounded-full bg-green-500/20 text-green-400 text-sm font-medium">
            Pagato
          </span>
        );
      case 'to_pay':
        return (
          <span className="px-3 py-1 rounded-full bg-accent-orange/20 text-accent-orange text-sm font-medium">
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

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'pending':
        return <Clock className="w-5 h-5 text-accent-orange" />;
      case 'cancel':
        return <XCircle className="w-5 h-5 text-red-500" />;
      default:
        return <AlertCircle className="w-5 h-5 text-text-secondary" />;
    }
  };

  return (
    <Layout>
      <div className="space-y-4">
        {/* Top cards and hero */}
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
          <div 
            className="xl:col-span-2 grid grid-cols-1 lg:grid-cols-3 gap-4"
            style={{ marginRight: '-85px', width: 'calc(100% + 85px)' }}
          >
            {/* Card sfumata - Totale Dataset Acquistati */}
            <div 
              className="card text-white flex items-center justify-between border"
              style={{
                background: 'linear-gradient(to bottom, #181f25, #064e7e)',
                borderColor: '#007ed2',
              }}
            >
              <div>
                <div className="text-xl opacity-90 font-semibold -mt-2 mb-3">Dataset Acquistati</div>
                <div className="text-3xl font-semibold">{totalPaid}</div>
                <div className="text-xs opacity-80 mt-3">Ultimo dataset: {recentDatasets[0]?.createdAt ?? '-'}</div>
              </div>
              <div className="p-3 bg-white/10 rounded-full">
                <CreditCard className="w-6 h-6" />
              </div>
            </div>
            
            {/* Card Dataset Elaborati */}
            <div 
              className="card text-white flex items-center justify-between border"
              style={{
                background: 'linear-gradient(to bottom, #181f25, #064e7e)',
                borderColor: '#007ed2',
              }}
            >
              <div>
                <div className="text-xl opacity-90 font-semibold -mt-2 mb-3">Dataset Elaborati</div>
                <div className="text-3xl font-semibold">{totalCompleted}</div>
                <div className="text-xs opacity-80 mt-3">Dataset creati: {totalCreated}</div>
              </div>
              <div className="p-3 bg-white/10 rounded-full">
                <Settings className="w-6 h-6" />
              </div>
            </div>
            
            {/* Card Totale Spesa */}
            <div 
              className="card text-white flex items-center justify-between border"
              style={{
                background: 'linear-gradient(to bottom, #181f25, #064e7e)',
                borderColor: '#007ed2',
              }}
            >
              <div>
                <div className="text-xl opacity-90 font-semibold -mt-2 mb-3">Dataset Disponibili</div>
                <div className="text-3xl font-semibold">{totalCompleted}</div>
                <div className="text-xs opacity-80 mt-3">Dataset creati: {totalCreated}</div>
              </div>
              <div className="p-3 bg-white/10 rounded-full">
                <Database className="w-6 h-6" />
              </div>
            </div>
          </div>
          
          {/* Card arancio */}
          <div 
            className="card text-white flex items-center justify-between border ml-auto"
            style={{
              background: 'linear-gradient(to bottom, #8b4a0a, #fa9f2a)',
              borderColor: 'white',
              width: 'calc(100% - 100px)',
            }}
          >
            <div>
              <div className="text-xl opacity-90 font-semibold -mt-2 mb-3">{activePlanSlide?.title ?? 'Piani'}</div>
              <div className="text-base font-semibold">{activePlanSlide?.subtitle ?? '-'}</div>
              <div className="text-xs opacity-80 mt-2">{activePlanSlide?.meta ?? ''}</div>
              <Link
                to="/dashboard/billing?tab=plans#plans"
                className="text-xs opacity-80 mt-3 inline-flex items-center gap-2 px-3 py-2 bg-white rounded-full w-fit font-bold"
                style={{ color: '#fa9f2a' }}
              >
                <ArrowUpRight className="w-4 h-4" style={{ color: '#fa9f2a' }} />
                Fai Upgrade
              </Link>
            </div>
            <div className="p-3 bg-white/10 rounded-full">
              <Package className="w-6 h-6" />
            </div>
          </div>
        </div>

        {/* Chart */}
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
          <div 
            className="card xl:col-span-2 border"
            style={{ borderColor: '#007ed2', marginRight: '-85px', width: 'calc(100% + 85px)' }}
          >
            <div className="flex flex-wrap items-center justify-between gap-4 mb-3">
              <div>
                <h2 className="text-xl font-semibold text-text-primary">Riepilogo Temporale</h2>
                <p className="text-text-secondary text-sm">Anno accademico 2025</p>
              </div>
              <div className="flex items-center gap-2 text-text-secondary text-sm">
                <div className="w-3 h-3 rounded-full bg-accent-blue" /> Dataset Creati
                <div className="w-3 h-3 rounded-full bg-orange-400 ml-3" /> Dataset Acquistati
              </div>
            </div>
            {/* Chart */}
            <div className="rounded-input bg-dark-secondary p-4 border border-dark-secondary relative overflow-hidden">
              <div className="absolute inset-0 opacity-20 bg-[radial-gradient(circle_at_center,_#3B82F6_1px,_transparent_1px)] bg-[length:40px_40px]" />
              
              {/* Y-axis labels */}
              <div className="absolute left-0 top-6 bottom-12 flex flex-col-reverse justify-between text-xs text-text-secondary pl-2">
                {[0, 5, 10, 15, 20, 25].map((val) => (
                  <span key={val}>{val}</span>
                ))}
              </div>

              {/* Chart area */}
              <div className="relative ml-6 h-48 flex items-end gap-3">
                {academicYearData.map((data, idx) => {
                  const createdHeight = (data.created / maxValue) * 100;
                  const purchasedHeight = (data.purchased / maxValue) * 100;
                  const isHovered = hoveredMonth === idx;

                  return (
                    <div
                      key={idx}
                      className="flex-1 flex flex-col items-center justify-end relative group h-full"
                      onMouseEnter={() => setHoveredMonth(idx)}
                      onMouseLeave={() => setHoveredMonth(null)}
                    >
                      {/* Vertical line on hover */}
                      {isHovered && (
                        <div className="absolute left-1/2 top-0 bottom-0 w-0.5 bg-accent-blue/50 -translate-x-1/2 z-10" />
                      )}

                      {/* Area chart for Purchased (orange) - from bottom, behind Created, more transparent */}
                      <div 
                        className="w-full relative rounded-t"
                        style={{ 
                          height: `${purchasedHeight}%`,
                          minHeight: purchasedHeight > 0 ? '4px' : '0px'
                        }}
                      >
                        <div
                          className="w-full h-full bg-gradient-to-t from-orange-400/30 to-orange-400/10 rounded-t"
                        />
                        {/* Top line for Purchased */}
                        <div
                          className="absolute top-0 left-0 right-0 h-0.5 bg-orange-400/40"
                        />
                        {/* Point on hover */}
                        {isHovered && (
                          <div className="absolute -top-1.5 left-1/2 -translate-x-1/2 w-3 h-3 bg-orange-400 rounded-full border-2 border-dark-secondary z-20" />
                        )}
                      </div>

                      {/* Area chart for Created (blue) - from bottom, in front of Purchased */}
                      <div 
                        className="w-full relative rounded-t absolute bottom-0"
                        style={{ 
                          height: `${createdHeight}%`,
                          minHeight: createdHeight > 0 ? '4px' : '0px',
                          zIndex: 1
                        }}
                      >
                        <div
                          className="w-full h-full bg-gradient-to-t from-accent-blue/50 to-accent-blue/20 rounded-t"
                        />
                        {/* Top line for Created */}
                        <div
                          className="absolute top-0 left-0 right-0 h-0.5 bg-accent-blue"
                        />
                        {/* Point on hover */}
                        {isHovered && (
                          <div className="absolute -top-1.5 left-1/2 -translate-x-1/2 w-3 h-3 bg-accent-blue rounded-full border-2 border-dark-secondary z-20" />
                        )}
                      </div>

                      {/* Tooltip on hover - styled like the mockup */}
                      {isHovered && (
                        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-orange-400 rounded-lg px-4 py-3 text-white z-30 shadow-lg">
                          <div className="text-xs opacity-90 mb-2">
                            {data.month} 2024
                          </div>
                          <div className="flex items-baseline gap-2">
                            <div className="text-2xl font-bold">
                              {data.created + data.purchased}
                            </div>
                            <div className="text-sm opacity-90">
                              Dataset
                            </div>
                          </div>
                          <div className="text-xs mt-2 opacity-90">
                            Creati: {data.created} • Acquistati: {data.purchased}
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>

              {/* X-axis labels */}
              <div className="mt-4 ml-6 text-text-secondary text-sm flex justify-between">
                {academicYearData.map((data, idx) => (
                  <span
                    key={idx}
                    className={hoveredMonth === idx ? 'text-accent-blue font-semibold' : ''}
                  >
                    {data.month}
                  </span>
                ))}
              </div>
            </div>
          </div>

          {/* Card Dataset Disponibili */}
          <div 
            className="card text-white border flex flex-col items-center justify-between ml-auto"
            style={{
              background: 'linear-gradient(to bottom, #181f25, #064e7e)',
              borderColor: '#007ed2',
              width: 'calc(100% - 100px)',
            }}
          >
            <div className="w-full">
              <h3 className="text-lg font-semibold text-white mb-3">Totale Spesa</h3>
            </div>
            <div className="flex flex-col items-center justify-center flex-1 w-full">
              <Wallet className="w-12 h-12 opacity-80 mb-3" />
              <div className="text-5xl font-bold">€ {walletSpent.toLocaleString('it-IT', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}</div>
            </div>
            <div className="w-full flex items-center justify-between">
              <div className="text-base opacity-90 font-semibold">
                Credito rimanente: € {walletBalance.toLocaleString('it-IT', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </div>
              <div className="flex flex-col items-end gap-1">
                <div className="px-3 py-1.5 bg-[#fa9f2a] rounded-full flex items-center gap-1.5">
                  <TrendingUp className="w-4 h-4" />
                  <span className="text-sm font-semibold">{growth}%</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Datasets table + Traffic */}
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
          <div 
            className="card xl:col-span-2 border"
            style={{ borderColor: '#007ed2', marginRight: '-85px', width: 'calc(100% + 85px)' }}
          >
            <div className="flex flex-wrap items-center justify-between gap-3 mb-2">
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-semibold text-text-primary">Dataset Recenti</h3>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="text-text-secondary border-b border-dark-secondary">
                    <th className="py-2">Codice DataSet</th>
                    <th className="py-2">Nome DataSet</th>
                    <th className="py-2">Data di creazione</th>
                    <th className="py-2">Prezzo pagato</th>
                    <th className="py-2">Stato</th>
                    <th className="py-2">Dataset</th>
                    <th className="py-2">Azioni</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-dark-secondary">
                  {(recentDatasets.length > 0
                    ? recentDatasets
                    : Array.from({ length: 6 }).map((_, i) => ({
                        id: `placeholder-${i}`,
                        code: '-',
                        name: 'Nessun dataset ancora',
                        createdAt: '-',
                        price: '-',
                        status: 'processing' as const,
                      }))
                  ).map((item: any, idx: number) => (
                    <tr key={item.id} className="text-text-primary">
                      <td className="py-2">{item.code}</td>
                      <td className="py-2">{item.name}</td>
                      <td className="py-2">{item.createdAt}</td>
                      <td className="py-2">{item.price}</td>
                      <td className="py-2">{recentDatasets.length > 0 ? getStatusPill(item.status) : '-'}</td>
                      <td className="py-2">
                        <Link
                          to="/dashboard/datasets"
                          className="p-2 rounded-input hover:bg-dark-secondary transition-colors inline-flex"
                          title="Vai ai Dataset"
                        >
                          <Database className="w-5 h-5 text-accent-blue" />
                        </Link>
                      </td>
                      <td className="py-2">
                        <div className="relative">
                          <button
                            className="p-2 rounded-input hover:bg-dark-secondary transition-colors"
                            onClick={() => setActionMenuOpen(actionMenuOpen === idx ? null : idx)}
                          >
                            <MoreVertical className="w-5 h-5 text-text-secondary" />
                          </button>
                          {actionMenuOpen === idx && (
                            <div className="absolute right-0 mt-2 w-48 bg-dark-card border border-dark-secondary rounded-input shadow-lg z-10">
                              <Link
                                to="/dashboard/datasets"
                                className="w-full px-4 py-2 text-left text-sm text-text-primary hover:bg-dark-secondary flex items-center gap-2"
                                onClick={() => setActionMenuOpen(null)}
                              >
                                <ExternalLink className="w-4 h-4" />
                                Vai ai Dataset
                              </Link>
                            </div>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div 
            className="card border ml-auto"
            style={{ borderColor: '#007ed2', width: 'calc(100% - 100px)' }}
          >
              <div className="mb-2">
                <h3 className="text-lg font-semibold text-text-primary">Riepilogo Categorie</h3>
              </div>
            <div className="space-y-3">
              {categories.map((item) => (
                <div key={item.label}>
                  <div className="flex items-center justify-between text-sm text-text-secondary mb-1">
                    <span>{item.label}</span>
                    <span>{item.value}</span>
                  </div>
                  <div className="w-full bg-dark-secondary rounded-full h-2">
                    <div
                      className="h-2 rounded-full bg-accent-blue"
                      style={{ width: `${item.percent}%` }}
                    />
                  </div>
                  <div className="text-xs text-text-secondary mt-0.5">{item.percent}%</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}

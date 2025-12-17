import { ReactNode, useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  LayoutDashboard,
  MessageSquare,
  Database,
  CreditCard,
  User,
  Settings,
  Menu,
  X,
  LogOut,
  BarChart,
  Users,
  Search,
  Bell,
  Wallet,
} from 'lucide-react';
import BrandLogo from './BrandLogo';
import { authApi } from '../lib/auth';
import { api } from '../lib/api';

interface LayoutProps {
  children: ReactNode;
  searchQuery?: string;
  onSearchChange?: (query: string) => void;
  headerTitle?: string;
  headerSubtitle?: string;
}

export default function Layout({ children, searchQuery, onSearchChange, headerTitle, headerSubtitle }: LayoutProps) {
  const location = useLocation();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [currentDateTime, setCurrentDateTime] = useState(new Date());
  const [notificationsCount, setNotificationsCount] = useState(0); // Mock: da sostituire con dati reali
  const [showWalletTooltip, setShowWalletTooltip] = useState(false);

  // Fetch user profile and current user data
  const { data: userProfile } = useQuery({
    queryKey: ['userProfile'],
    queryFn: authApi.getUserProfile,
    enabled: !!localStorage.getItem('access_token'),
    retry: 2,
    retryDelay: 1000,
    refetchOnMount: true,
    refetchOnWindowFocus: true,
  });

  const { data: currentUser } = useQuery({
    queryKey: ['currentUser'],
    queryFn: authApi.getCurrentUser,
    enabled: !!localStorage.getItem('access_token'),
    retry: false,
    refetchOnMount: true,
  });

  // Wallet summary (real from backend)
  const { data: walletSummary } = useQuery({
    queryKey: ['walletSummary'],
    queryFn: async () => (await api.get('/api/v1/wallet/summary')).data,
    enabled: !!localStorage.getItem('access_token'),
    retry: 1,
    refetchOnWindowFocus: true,
  });

  // Update date/time every second
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentDateTime(new Date());
    }, 1000);
    return () => clearInterval(interval);
  }, []);


  const formatDate = (date: Date) => {
    const days = ['Domenica', 'Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì', 'Sabato'];
    const dayName = days[date.getDay()];
    const day = date.getDate().toString().padStart(2, '0');
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const year = date.getFullYear();
    const hours = date.getHours().toString().padStart(2, '0');
    const minutes = date.getMinutes().toString().padStart(2, '0');
    const seconds = date.getSeconds().toString().padStart(2, '0');
    return `${dayName}, ${day}/${month}/${year} ${hours}:${minutes}:${seconds}`;
  };

  // Costruisci il nome completo dal profilo utente
  // Prova prima dal profilo (first_name, last_name), poi dall'email come fallback
  const fullName = userProfile?.first_name && userProfile?.last_name
    ? `${userProfile.first_name} ${userProfile.last_name}`
    : currentUser?.email
    ? currentUser.email.split('@')[0] // Usa la parte prima della @ come fallback
    : 'Utente';

  // Menu items base (visibili a tutti)
  const baseMenuItems = [
    { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { path: '/dashboard/datasets', icon: Database, label: 'Dataset' },
    { path: '/dashboard/billing', icon: CreditCard, label: 'Pagamenti e Fatture' },
    { path: '/dashboard/profile', icon: Users, label: 'Profilo' },
  ];

  // Menu items admin (visibili solo agli admin)
  // TODO: Sostituire con controllo ruolo reale dall'API quando disponibile
  // Per ora controlla localStorage o userProfile per il ruolo admin
  const isAdmin = localStorage.getItem('is_admin') === 'true' || (userProfile as any)?.is_admin === true;
  const adminMenuItems = [
    { path: '/dashboard/statistics', icon: BarChart, label: 'Statistics' },
    { path: '/dashboard/messages', icon: MessageSquare, label: 'Messages' },
    { path: '/dashboard/settings', icon: Settings, label: 'Settings' },
  ];

  const menuItems = isAdmin ? [...baseMenuItems, ...adminMenuItems] : baseMenuItems;

  const isActive = (path: string) => {
    if (path === '/dashboard') return location.pathname === '/dashboard';
    return location.pathname.startsWith(path);
  };

  const handleLogout = async () => {
    try {
      await authApi.logout();
    } catch (err) {
      // ignore
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      navigate('/login');
    }
  };

  return (
    <div
      className="min-h-screen text-text-primary flex"
      style={{ backgroundColor: '#1a1b1f' }}
    >
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed top-0 left-0 h-full w-64 border-r border-dark-secondary z-50 transform transition-transform duration-300 ease-in-out lg:translate-x-0 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
        style={{ backgroundColor: '#212a35' }}
      >
        <div className="flex flex-col h-full">
          <div
            className="p-6 border-b flex items-center justify-between"
            style={{ borderColor: '#212a35' }}
          >
            <BrandLogo className="h-10 w-auto" />
            <button
              className="lg:hidden text-text-secondary hover:text-text-primary"
              onClick={() => setSidebarOpen(false)}
            >
              <X className="w-6 h-6" />
            </button>
          </div>

          <nav className="flex-1 p-4 space-y-1 overflow-y-auto overflow-x-hidden">
            {menuItems.map((item) => {
              const Icon = item.icon;
              const active = isActive(item.path);
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={() => setSidebarOpen(false)}
                  className={`relative flex items-center gap-3 px-4 py-3 rounded-input transition-colors border overflow-hidden ${
                    active
                      ? 'text-white border-white'
                      : 'text-text-secondary hover:text-text-primary hover:bg-dark-secondary border-transparent'
                  }`}
                  style={active ? { backgroundColor: '#0180d1' } : {}}
                >
                  <Icon className="w-5 h-5" />
                  <span className="font-medium">{item.label}</span>
                  {active && (
                    <div className="absolute right-0 top-1/2 -translate-y-1/2 translate-x-1/2 w-4 h-4 bg-white rounded-full" />
                  )}
                </Link>
              );
            })}
          </nav>

          <div className="p-4 border-t border-dark-secondary">
            <button
              onClick={handleLogout}
              className="w-full flex items-center gap-3 px-4 py-3 rounded-input text-text-secondary hover:text-red-400 hover:bg-red-500/10 transition-colors"
            >
              <LogOut className="w-5 h-5" />
              <span className="font-medium">Esci</span>
            </button>
            <div className="text-xs text-text-secondary mt-2 pl-4">
              Powered by AXDATA Srl
            </div>
          </div>
        </div>
      </aside>

      {/* Main area */}
      <div className="flex-1 lg:ml-64 flex flex-col min-h-screen">
        {/* Header */}
        <header
          className="sticky top-0 z-30 border-b border-dark-secondary"
          style={{ backgroundColor: '#1a1b1f', borderColor: '#1a1b1f' }}
        >
          <div className="px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
            <button
              className="lg:hidden text-text-secondary hover:text-text-primary mr-4"
              onClick={() => setSidebarOpen(true)}
            >
              <Menu className="w-6 h-6" />
            </button>
            <div className="flex flex-col text-white">
              <div className="text-2xl font-semibold mb-1">
                {headerTitle || `Benvenuto ${fullName}`}
              </div>
              <div className="text-sm opacity-90">
                {headerSubtitle || formatDate(currentDateTime)}
              </div>
            </div>
            {onSearchChange && (
              <div className="flex-1 flex justify-center mx-8">
                <div className="relative w-full max-w-md">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-text-secondary" />
                  <input
                    type="text"
                    value={searchQuery || ''}
                    onChange={(e) => onSearchChange(e.target.value)}
                    placeholder="Cerca dataset..."
                    className="w-full pl-10 pr-4 py-2 bg-dark-secondary border border-dark-secondary rounded-input text-text-primary placeholder-text-secondary focus:outline-none focus:border-accent-blue transition-colors"
                  />
                </div>
              </div>
            )}
            {!onSearchChange && <div className="flex-1" />}
            <div className="flex items-center gap-4 text-white">
              {/* Portfolio Virtuale */}
              <div className="relative">
                <button
                  onClick={() => setShowWalletTooltip(!showWalletTooltip)}
                  className="relative p-2 rounded-input hover:bg-dark-secondary transition-colors"
                  title="Portfolio Virtuale"
                >
                  <Wallet className="w-5 h-5 text-text-secondary hover:text-text-primary" />
                </button>
                {showWalletTooltip && (
                  <>
                    <div
                      className="fixed inset-0 z-40"
                      onClick={() => setShowWalletTooltip(false)}
                    />
                    <div className="absolute right-0 top-full mt-2 w-64 bg-dark-secondary border border-dark-secondary rounded-input p-4 shadow-lg z-50">
                      <div className="text-sm font-semibold text-text-primary mb-3">Portfolio Virtuale</div>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-text-secondary">Totale Caricato:</span>
                          <span className="text-text-primary font-semibold">
                            € {Number(walletSummary?.total_loaded ?? 0).toLocaleString('it-IT', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-text-secondary">Rimanente:</span>
                          <span className="text-accent-blue font-semibold">
                            € {Number(walletSummary?.balance ?? 0).toLocaleString('it-IT', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                          </span>
                        </div>
                        <div className="pt-2 border-t border-dark-secondary">
                          <div className="flex justify-between">
                            <span className="text-text-secondary">Speso:</span>
                            <span className="text-text-primary">
                              € {Number(walletSummary?.total_spent ?? 0).toLocaleString('it-IT', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </>
                )}
              </div>

              {/* Notifiche */}
              <div className="relative">
                <button
                  className="relative p-2 rounded-input hover:bg-dark-secondary transition-colors"
                  title="Notifiche"
                >
                  <Bell className="w-5 h-5 text-text-secondary hover:text-text-primary" />
                  {notificationsCount > 0 && (
                    <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs font-bold rounded-full flex items-center justify-center">
                      {notificationsCount > 9 ? '9+' : notificationsCount}
                    </span>
                  )}
                </button>
              </div>

              {/* Avatar e Nome */}
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-accent-blue/20 border border-accent-blue flex items-center justify-center text-sm font-semibold">
                  {fullName.split(' ').map(n => n[0]).join('').toUpperCase()}
                </div>
                <div className="flex flex-col">
                  <div className="text-sm font-semibold">{fullName}</div>
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Content */}
        <main className="p-4 sm:p-6 lg:p-8 flex-1">{children}</main>
      </div>
    </div>
  );
}

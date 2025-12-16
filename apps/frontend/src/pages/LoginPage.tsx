import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Mail, Lock, LogIn, Eye, EyeOff } from 'lucide-react';
import { authApi } from '../lib/auth';
import BrandLogo from '../components/BrandLogo';

const loginSchema = z.object({
  email: z.string().email('Email non valida'),
  password: z.string().min(1, 'Password richiesta'),
});

type LoginFormData = z.infer<typeof loginSchema>;

export default function LoginPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(false);

  // Redirect to dashboard if already authenticated
  useEffect(() => {
    const accessToken = localStorage.getItem('access_token');
    if (accessToken) {
      navigate('/dashboard', { replace: true });
    }
  }, [navigate]);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  const loginMutation = useMutation({
    mutationFn: authApi.login,
    onSuccess: (data) => {
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
      // Invalida le query per ricaricare i dati utente dopo il login
      queryClient.invalidateQueries({ queryKey: ['userProfile'] });
      queryClient.invalidateQueries({ queryKey: ['currentUser'] });
      navigate('/dashboard');
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Errore durante il login');
    },
  });

  const onSubmit = (data: LoginFormData) => {
    setError(null);
    loginMutation.mutate({
      username: data.email,
      password: data.password,
    });
  };

  return (
    <div className="min-h-screen bg-dark-primary flex items-center justify-center p-4">
      <div className="card w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="flex justify-center mb-6">
            <BrandLogo className="h-16 w-auto" />
          </div>
          <p className="text-text-secondary">Inserisci le tue credenziali per accedere</p>
        </div>

        {/* Error message */}
        {error && (
          <div className="mb-4 p-4 bg-red-500/10 border border-red-500/50 rounded-input text-red-400 text-sm">
            {error}
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          {/* Email */}
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-text-secondary mb-2">
              Email
            </label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 text-text-secondary w-5 h-5" />
              <input
                id="email"
                type="email"
                {...register('email')}
                className="input-field pl-10"
                placeholder="nome@esempio.com"
              />
            </div>
            {errors.email && (
              <p className="mt-1 text-sm text-red-400">{errors.email.message}</p>
            )}
          </div>

          {/* Password */}
          <div>
            <label htmlFor="password" className="block text-sm font-medium text-text-secondary mb-2">
              Password
            </label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-text-secondary w-5 h-5" />
              <input
                id="password"
                type={showPassword ? "text" : "password"}
                {...register('password')}
                className="input-field pl-10 pr-10"
                placeholder="••••••••"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-text-secondary hover:text-text-primary transition-colors"
              >
                {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
              </button>
            </div>
            {errors.password && (
              <p className="mt-1 text-sm text-red-400">{errors.password.message}</p>
            )}
          </div>

          {/* Forgot Password Link */}
          <div className="flex justify-end">
            <Link
              to="/forgot-password"
              className="text-sm text-accent-blue hover:text-accent-blue/80 transition-colors"
            >
              Password dimenticata?
            </Link>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loginMutation.isPending}
            className="btn-primary w-full flex items-center justify-center gap-2"
          >
            {loginMutation.isPending ? (
              <>
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>Accesso in corso...</span>
              </>
            ) : (
              <>
                <LogIn className="w-5 h-5" />
                <span>Accedi</span>
              </>
            )}
          </button>
        </form>

        {/* Register Link */}
        <div className="mt-6 text-center">
          <p className="text-text-secondary text-sm">
            Non hai un account?{' '}
            <Link
              to="/register"
              className="text-accent-blue hover:text-accent-blue/80 font-medium transition-colors"
            >
              Registrati
            </Link>
          </p>
        </div>

        {/* Footer */}
        <div className="mt-8 text-center text-xs text-text-secondary">
          <p>Powered by AXDATA Srl</p>
        </div>
      </div>
    </div>
  );
}

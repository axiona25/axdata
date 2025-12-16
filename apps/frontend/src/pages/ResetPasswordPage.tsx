import { useState, useEffect } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMutation } from '@tanstack/react-query';
import { Lock, CheckCircle, ArrowLeft } from 'lucide-react';
import { authApi } from '../lib/auth';
import BrandLogo from '../components/BrandLogo';

const resetPasswordSchema = z
  .object({
    password: z
      .string()
      .min(8, 'Password deve contenere almeno 8 caratteri')
      .regex(/[A-Z]/, 'Password deve contenere almeno una lettera maiuscola')
      .regex(/[a-z]/, 'Password deve contenere almeno una lettera minuscola')
      .regex(/[0-9]/, 'Password deve contenere almeno un numero')
      .regex(/[^A-Za-z0-9]/, 'Password deve contenere almeno un carattere speciale'),
    confirm_password: z.string(),
  })
  .refine((data) => data.password === data.confirm_password, {
    message: 'Le password non corrispondono',
    path: ['confirm_password'],
  });

type ResetPasswordFormData = z.infer<typeof resetPasswordSchema>;

export default function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [token, setToken] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    const tokenParam = searchParams.get('token');
    if (!tokenParam) {
      // Redirect to forgot password if no token
      navigate('/forgot-password');
    } else {
      setToken(tokenParam);
    }
  }, [searchParams, navigate]);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<ResetPasswordFormData>({
    resolver: zodResolver(resetPasswordSchema),
  });

  const resetPasswordMutation = useMutation({
    mutationFn: ({ token, password }: { token: string; password: string }) =>
      authApi.resetPassword(token, password),
    onSuccess: () => {
      setSuccess(true);
      setTimeout(() => {
        navigate('/login');
      }, 3000);
    },
  });

  const onSubmit = (data: ResetPasswordFormData) => {
    if (token) {
      resetPasswordMutation.mutate({ token, password: data.password });
    }
  };

  const password = watch('password');

  const getPasswordStrength = (password: string) => {
    let strength = 0;
    if (password && password.length >= 8) strength++;
    if (password && /[A-Z]/.test(password)) strength++;
    if (password && /[a-z]/.test(password)) strength++;
    if (password && /[0-9]/.test(password)) strength++;
    if (password && /[^A-Za-z0-9]/.test(password)) strength++;
    return strength;
  };

  if (!token) {
    return null; // Will redirect
  }

  if (success) {
    return (
      <div className="min-h-screen bg-dark-primary flex items-center justify-center p-4">
        <div className="card w-full max-w-md text-center">
          <div className="w-16 h-16 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
            <CheckCircle className="w-8 h-8 text-green-500" />
          </div>
          <h2 className="text-2xl font-semibold text-text-primary mb-4">
            Password Reimpostata
          </h2>
          <p className="text-text-secondary mb-6">
            La tua password è stata reimpostata con successo. Verrai reindirizzato al login...
          </p>
          <Link to="/login" className="btn-primary w-full block text-center">
            Vai al Login
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-dark-primary flex items-center justify-center p-4">
      <div className="card w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="flex justify-center mb-4">
            <BrandLogo className="h-10 w-auto" />
          </div>
          <h2 className="text-2xl font-semibold text-text-primary mb-2">
            Reimposta Password
          </h2>
          <p className="text-text-secondary">
            Inserisci la tua nuova password
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          <div>
            <label htmlFor="password" className="block text-sm font-medium text-text-secondary mb-2">
              Nuova Password
            </label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-text-secondary w-5 h-5" />
              <input
                id="password"
                type="password"
                {...register('password')}
                className="input-field pl-10"
                placeholder="••••••••"
              />
            </div>
            {password && (
              <div className="mt-2">
                <div className="flex gap-1 mb-2">
                  {[1, 2, 3, 4, 5].map((level) => (
                    <div
                      key={level}
                      className={`h-1 flex-1 rounded ${
                        getPasswordStrength(password) >= level
                          ? 'bg-green-500'
                          : 'bg-dark-secondary'
                      }`}
                    />
                  ))}
                </div>
                <p className="text-xs text-text-secondary">
                  La password deve contenere: maiuscole, minuscole, numeri e caratteri speciali
                </p>
              </div>
            )}
            {errors.password && (
              <p className="mt-1 text-sm text-red-400">{errors.password.message}</p>
            )}
          </div>

          <div>
            <label htmlFor="confirm_password" className="block text-sm font-medium text-text-secondary mb-2">
              Conferma Password
            </label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-text-secondary w-5 h-5" />
              <input
                id="confirm_password"
                type="password"
                {...register('confirm_password')}
                className="input-field pl-10"
                placeholder="••••••••"
              />
            </div>
            {errors.confirm_password && (
              <p className="mt-1 text-sm text-red-400">
                {errors.confirm_password.message}
              </p>
            )}
          </div>

          {resetPasswordMutation.isError && (
            <div className="p-4 bg-red-500/10 border border-red-500/50 rounded-input text-red-400 text-sm">
              {(resetPasswordMutation.error as any)?.response?.data?.detail ||
                'Errore durante il reset della password'}
            </div>
          )}

          <button
            type="submit"
            disabled={resetPasswordMutation.isPending}
            className="btn-primary w-full"
          >
            {resetPasswordMutation.isPending ? (
              <>
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mx-auto" />
              </>
            ) : (
              'Conferma Cambio Password'
            )}
          </button>
        </form>

        {/* Back to Login */}
        <div className="mt-6 text-center">
          <Link
            to="/login"
            className="inline-flex items-center gap-2 text-sm text-accent-blue hover:text-accent-blue/80 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Torna al Login</span>
          </Link>
        </div>

        {/* Footer */}
        <div className="mt-8 text-center text-xs text-text-secondary">
          <p>Powered by AXDATA Srl</p>
        </div>
      </div>
    </div>
  );
}

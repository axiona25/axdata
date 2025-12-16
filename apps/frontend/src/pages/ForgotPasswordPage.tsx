import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMutation } from '@tanstack/react-query';
import { Mail, ArrowLeft } from 'lucide-react';
import { authApi } from '../lib/auth';
import BrandLogo from '../components/BrandLogo';

const forgotPasswordSchema = z.object({
  email: z.string().email('Email non valida'),
});

type ForgotPasswordFormData = z.infer<typeof forgotPasswordSchema>;

export default function ForgotPasswordPage() {
  const [emailSent, setEmailSent] = useState(false);
  const [email, setEmail] = useState('');

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ForgotPasswordFormData>({
    resolver: zodResolver(forgotPasswordSchema),
  });

  const requestResetMutation = useMutation({
    mutationFn: authApi.requestPasswordReset,
    onSuccess: () => {
      setEmailSent(true);
    },
  });

  const onSubmit = (data: ForgotPasswordFormData) => {
    setEmail(data.email);
    requestResetMutation.mutate(data.email);
  };

  return (
    <div className="min-h-screen bg-dark-primary flex items-center justify-center p-4">
      <div className="card w-full max-w-md">
        {!emailSent ? (
          <>
            {/* Logo */}
            <div className="text-center mb-8">
              <div className="flex justify-center mb-4">
                <BrandLogo className="h-10 w-auto" />
              </div>
              <h2 className="text-2xl font-semibold text-text-primary mb-2">
                Recupera Password
              </h2>
              <p className="text-text-secondary">
                Inserisci la tua email per ricevere il link di reset password
              </p>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
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

              <button
                type="submit"
                disabled={requestResetMutation.isPending}
                className="btn-primary w-full"
              >
                {requestResetMutation.isPending ? (
                  <>
                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mx-auto" />
                  </>
                ) : (
                  'Invia Link di Reset'
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
          </>
        ) : (
          <div className="text-center">
            <div className="w-16 h-16 bg-accent-blue/20 rounded-full flex items-center justify-center mx-auto mb-4">
              <Mail className="w-8 h-8 text-accent-blue" />
            </div>
            <h2 className="text-2xl font-semibold text-text-primary mb-4">
              Email Inviata
            </h2>
            <p className="text-text-secondary mb-6">
              Ti abbiamo inviato un link di reset password all'indirizzo{' '}
              <span className="text-accent-blue font-medium">{email}</span>.
              Controlla la tua casella di posta e clicca sul link per reimpostare la password.
            </p>
            <Link to="/login" className="btn-primary w-full block text-center">
              Torna al Login
            </Link>
          </div>
        )}

        {/* Footer */}
        <div className="mt-8 text-center text-xs text-text-secondary">
          <p>Powered by AXDATA Srl</p>
        </div>
      </div>
    </div>
  );
}

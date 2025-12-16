import { useState, useEffect } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { CheckCircle, XCircle, Mail } from 'lucide-react';
import { authApi } from '../lib/auth';
import BrandLogo from '../components/BrandLogo';

export default function VerifyEmailPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState<'verifying' | 'success' | 'error'>('verifying');
  const [error, setError] = useState<string | null>(null);
  const [email, setEmail] = useState<string>('');

  const verifyMutation = useMutation({
    mutationFn: authApi.verifyEmail,
    onSuccess: () => {
      // Clear pending verification email from localStorage
      localStorage.removeItem('pending_verification_email');
      setStatus('success');
      setTimeout(() => {
        navigate('/login');
      }, 3000);
    },
    onError: (err: any) => {
      setStatus('error');
      setError(err.response?.data?.detail || 'Errore durante la verifica');
    },
  });

  const [resendSuccess, setResendSuccess] = useState(false);

  const resendMutation = useMutation({
    mutationFn: authApi.resendVerificationEmail,
    onSuccess: () => {
      setResendSuccess(true);
      setError(null);
      // Clear success message after 5 seconds
      setTimeout(() => {
        setResendSuccess(false);
      }, 5000);
    },
    onError: (err: any) => {
      const errorMessage = err.response?.data?.detail || 'Errore durante l\'invio dell\'email';
      setError(errorMessage);
      setResendSuccess(false);
    },
  });

  useEffect(() => {
    const token = searchParams.get('token');
    const emailParam = searchParams.get('email');
    
    // Try to get email from URL, then from localStorage (from registration)
    if (emailParam) {
      setEmail(emailParam);
    } else {
      // Try to get email from localStorage (saved during registration)
      const savedEmail = localStorage.getItem('pending_verification_email');
      if (savedEmail) {
        setEmail(savedEmail);
      }
    }
    
    if (!token) {
      setStatus('error');
      setError('Token di verifica mancante');
    } else {
      verifyMutation.mutate(token);
    }
  }, [searchParams]);

  return (
    <div className="min-h-screen bg-dark-primary flex items-center justify-center p-4">
      <div className="card w-full max-w-md text-center">
        <div className="flex justify-center mb-6">
          <BrandLogo className="h-10 w-auto" />
        </div>
        {status === 'verifying' && (
          <>
            <div className="w-16 h-16 bg-accent-blue/20 rounded-full flex items-center justify-center mx-auto mb-4">
              <div className="w-8 h-8 border-4 border-accent-blue border-t-transparent rounded-full animate-spin" />
            </div>
            <h2 className="text-2xl font-semibold text-text-primary mb-4">
              Verifica in corso...
            </h2>
            <p className="text-text-secondary">
              Stiamo verificando il tuo account. Attendere prego.
            </p>
          </>
        )}

        {status === 'success' && (
          <>
            <div className="w-16 h-16 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
              <CheckCircle className="w-8 h-8 text-green-500" />
            </div>
            <h2 className="text-2xl font-semibold text-text-primary mb-4">
              Email Verificata
            </h2>
            <p className="text-text-secondary mb-6">
              Il tuo account è stato verificato con successo! Verrai reindirizzato al login...
            </p>
            <Link to="/login" className="btn-primary w-full block text-center">
              Vai al Login
            </Link>
          </>
        )}

        {status === 'error' && (
          <>
            <div className="w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
              <XCircle className="w-8 h-8 text-red-500" />
            </div>
            <h2 className="text-2xl font-semibold text-text-primary mb-4">
              Verifica Fallita
            </h2>
            <p className="text-text-secondary mb-6">
              {error || 'Il link di verifica non è valido o è scaduto.'}
            </p>
            <div className="space-y-4">
              <Link to="/login" className="btn-primary w-full block text-center">
                Vai al Login
              </Link>
              
              {/* Success message */}
              {resendSuccess && (
                <div className="p-4 bg-green-500/10 border border-green-500/50 rounded-input text-green-400 text-sm">
                  ✅ Email di verifica inviata con successo! Controlla la tua casella di posta.
                </div>
              )}
              
              <button
                onClick={() => {
                  // Try to get email from URL or localStorage if not already set
                  const emailParam = searchParams.get('email');
                  const savedEmail = localStorage.getItem('pending_verification_email');
                  const emailToUse = email || emailParam || savedEmail;
                  
                  if (!emailToUse) {
                    setError('Email non disponibile. Per favore, vai alla pagina di registrazione e richiedi un nuovo link di verifica.');
                    return;
                  }
                  
                  // Update email state if we found it
                  if (!email && emailToUse) {
                    setEmail(emailToUse);
                  }
                  
                  resendMutation.mutate(emailToUse);
                }}
                disabled={resendMutation.isPending}
                className="btn-outline w-full disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Mail className="w-4 h-4 inline mr-2" />
                {resendMutation.isPending ? 'Invio in corso...' : 'Invia di nuovo email di verifica'}
              </button>
            </div>
          </>
        )}

        {/* Footer */}
        <div className="mt-8 text-center text-xs text-text-secondary">
          <p>Powered by AXDATA Srl</p>
        </div>
      </div>
    </div>
  );
}

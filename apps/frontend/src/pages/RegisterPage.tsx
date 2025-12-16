import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import RegistrationWizard from '../components/RegistrationWizard';
import { authApi } from '../lib/auth';
import { Mail } from 'lucide-react';
import BrandLogo from '../components/BrandLogo';

export default function RegisterPage() {
  const [showWizard, setShowWizard] = useState(false);
  const [emailSent, setEmailSent] = useState(false);
  const [registeredEmail, setRegisteredEmail] = useState('');

  const resendEmailMutation = useMutation({
    mutationFn: authApi.resendVerificationEmail,
    onSuccess: () => {
      setEmailSent(true);
    },
  });

  const handleRegistrationSuccess = (email: string) => {
    setShowWizard(false);
    setEmailSent(true);
    setRegisteredEmail(email);
  };

  const handleResendEmail = () => {
    if (registeredEmail) {
      resendEmailMutation.mutate(registeredEmail);
    }
  };

  return (
    <div className="min-h-screen bg-dark-primary flex items-center justify-center p-4">
      {!emailSent ? (
        <div className="card w-full max-w-md">
          {/* Logo */}
          <div className="text-center mb-8">
            <div className="flex justify-center mb-4">
              <BrandLogo className="h-10 w-auto" />
            </div>
            <h2 className="text-2xl font-semibold text-text-primary mb-2">Crea un Account</h2>
            <p className="text-text-secondary">Registrati per iniziare</p>
          </div>

          {/* Register Button */}
          <button
            onClick={() => setShowWizard(true)}
            className="btn-primary w-full mb-4"
          >
            Inizia la Registrazione
          </button>

          {/* Login Link */}
          <div className="text-center">
            <p className="text-text-secondary text-sm">
              Hai già un account?{' '}
              <Link
                to="/login"
                className="text-accent-blue hover:text-accent-blue/80 font-medium transition-colors"
              >
                Accedi
              </Link>
            </p>
          </div>

          {/* Footer */}
          <div className="mt-8 text-center text-xs text-text-secondary">
            <p>Powered by AXDATA Srl</p>
          </div>
        </div>
      ) : (
        <div className="card w-full max-w-md">
          <div className="text-center">
            <div className="w-16 h-16 bg-accent-blue/20 rounded-full flex items-center justify-center mx-auto mb-4">
              <Mail className="w-8 h-8 text-accent-blue" />
            </div>
            <h2 className="text-2xl font-semibold text-text-primary mb-4">
              Email di Conferma Inviata
            </h2>
            <p className="text-text-secondary mb-6">
              Ti abbiamo inviato un'email di conferma all'indirizzo che hai fornito.
              Clicca sul link nell'email per attivare il tuo account.
            </p>
            <div className="space-y-4">
              <button
                onClick={handleResendEmail}
                disabled={resendEmailMutation.isPending}
                className="btn-outline w-full"
              >
                {resendEmailMutation.isPending ? 'Invio in corso...' : 'Invia di nuovo'}
              </button>
              <Link to="/login" className="block btn-primary w-full text-center">
                Vai al Login
              </Link>
            </div>
          </div>
        </div>
      )}

      {/* Registration Wizard Modal */}
      <RegistrationWizard
        isOpen={showWizard}
        onClose={() => setShowWizard(false)}
        onSuccess={handleRegistrationSuccess}
      />
    </div>
  );
}

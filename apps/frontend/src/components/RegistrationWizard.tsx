import { useState, useEffect, useRef } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { X, ChevronRight, ChevronLeft, Mail, Lock, User, Phone, Calendar, MapPin, Globe, CreditCard, Eye, EyeOff } from 'lucide-react';
import { authApi } from '../lib/auth';
import BrandLogo from './BrandLogo';

// Step 1 Schema
const step1Schema = z.object({
  first_name: z.string().min(2, 'Nome deve contenere almeno 2 caratteri'),
  last_name: z.string().min(2, 'Cognome deve contenere almeno 2 caratteri'),
  email: z.string().email('Email non valida'),
  phone: z.string().min(10, 'Numero di telefono non valido'),
  password: z
    .string()
    .min(8, 'Password deve contenere almeno 8 caratteri')
    .max(72, 'Password non può superare 72 caratteri')
    .regex(/[A-Z]/, 'Password deve contenere almeno una lettera maiuscola')
    .regex(/[a-z]/, 'Password deve contenere almeno una lettera minuscola')
    .regex(/[0-9]/, 'Password deve contenere almeno un numero')
    .regex(/[^A-Za-z0-9]/, 'Password deve contenere almeno un carattere speciale'),
  confirm_password: z.string(),
}).refine((data) => data.password === data.confirm_password, {
  message: 'Le password non corrispondono',
  path: ['confirm_password'],
});

// Step 2 Schema
const step2Schema = z.object({
  date_of_birth: z.string().min(1, 'Data di nascita richiesta'),
  address: z.string().min(5, 'Indirizzo completo richiesto'),
  country: z.string().min(1, 'Nazione richiesta'),
  language: z.string().min(1, 'Lingua parlata richiesta'),
});

// Step 3 Schema
const step3Schema = z.object({
  payment_method: z.string().min(1, 'Metodo di pagamento richiesto'),
});

type Step1Data = z.infer<typeof step1Schema>;
type Step2Data = z.infer<typeof step2Schema>;
type Step3Data = z.infer<typeof step3Schema>;

const europeanLanguages = [
  { value: 'it', label: 'Italiano' },
  { value: 'en', label: 'Inglese' },
  { value: 'es', label: 'Spagnolo' },
  { value: 'fr', label: 'Francese' },
  { value: 'de', label: 'Tedesco' },
  { value: 'pt', label: 'Portoghese' },
  { value: 'pl', label: 'Polacco' },
  { value: 'ro', label: 'Rumeno' },
  { value: 'nl', label: 'Olandese' },
  { value: 'el', label: 'Greco' },
  { value: 'cs', label: 'Ceco' },
  { value: 'sv', label: 'Svedese' },
  { value: 'hu', label: 'Ungherese' },
  { value: 'fi', label: 'Finlandese' },
  { value: 'da', label: 'Danese' },
];

const countries = [
  { value: 'IT', label: 'Italia' },
  { value: 'FR', label: 'Francia' },
  { value: 'DE', label: 'Germania' },
  { value: 'ES', label: 'Spagna' },
  { value: 'GB', label: 'Regno Unito' },
  { value: 'PT', label: 'Portogallo' },
  { value: 'NL', label: 'Paesi Bassi' },
  { value: 'BE', label: 'Belgio' },
  { value: 'AT', label: 'Austria' },
  { value: 'CH', label: 'Svizzera' },
  { value: 'SE', label: 'Svezia' },
  { value: 'NO', label: 'Norvegia' },
  { value: 'DK', label: 'Danimarca' },
  { value: 'FI', label: 'Finlandia' },
  { value: 'PL', label: 'Polonia' },
  { value: 'CZ', label: 'Repubblica Ceca' },
  { value: 'GR', label: 'Grecia' },
  { value: 'IE', label: 'Irlanda' },
  { value: 'LU', label: 'Lussemburgo' },
  { value: 'MT', label: 'Malta' },
];

interface RegistrationWizardProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (email: string) => void;
}

export default function RegistrationWizard({ isOpen, onClose, onSuccess }: RegistrationWizardProps) {
  const [currentStep, setCurrentStep] = useState(1);
  const [paymentMethods, setPaymentMethods] = useState<Array<{ id: string; name: string; provider: string }>>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const step1Form = useForm<Step1Data>({
    resolver: zodResolver(step1Schema),
  });

  const step2Form = useForm<Step2Data>({
    resolver: zodResolver(step2Schema),
  });

  const step3Form = useForm<Step3Data>({
    resolver: zodResolver(step3Schema),
  });

  const dateInputRef = useRef<HTMLInputElement>(null);

  // Load payment methods when reaching step 3
  useEffect(() => {
    if (isOpen && currentStep === 3 && paymentMethods.length === 0) {
      authApi.getPaymentMethods().then(setPaymentMethods);
    }
  }, [isOpen, currentStep]);

  if (!isOpen) return null;

  const handleStep1Submit = (_data: Step1Data) => {
    setError(null);
    setCurrentStep(2);
  };

  const handleStep2Submit = (_data: Step2Data) => {
    setError(null);
    setCurrentStep(3);
  };

  const handleStep3Submit = async (data: Step3Data) => {
    setError(null);
    setIsLoading(true);

    try {
      const step1Data = step1Form.getValues();
      const step2Data = step2Form.getValues();

      const registrationData = {
        email: step1Data.email,
        password: step1Data.password,
        first_name: step1Data.first_name,
        last_name: step1Data.last_name,
        phone: step1Data.phone,
        date_of_birth: step2Data.date_of_birth,
        address: step2Data.address,
        country: step2Data.country,
        language: step2Data.language,
        payment_method: data.payment_method,
      };

      await authApi.register(registrationData);
      // Save email to localStorage for verification page
      localStorage.setItem('pending_verification_email', step1Data.email);
      onSuccess(step1Data.email);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Errore durante la registrazione');
    } finally {
      setIsLoading(false);
    }
  };

  const getPasswordStrength = (password: string) => {
    let strength = 0;
    if (password.length >= 8) strength++;
    if (/[A-Z]/.test(password)) strength++;
    if (/[a-z]/.test(password)) strength++;
    if (/[0-9]/.test(password)) strength++;
    if (/[^A-Za-z0-9]/.test(password)) strength++;
    return strength;
  };

  const password = step1Form.watch('password');

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-700">
          <BrandLogo className="h-8 w-auto" />
          <button
            onClick={onClose}
            className="text-text-secondary hover:text-text-primary transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Progress Steps */}
        <div className="flex items-center justify-center p-6 border-b border-gray-700">
          {[1, 2, 3].map((step) => (
            <div key={step} className="flex items-center">
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold ${
                  currentStep >= step
                    ? 'bg-accent-blue text-white'
                    : 'bg-dark-secondary text-text-secondary'
                }`}
              >
                {step}
              </div>
              {step < 3 && (
                <div
                  className={`w-16 h-1 mx-2 ${
                    currentStep > step ? 'bg-accent-blue' : 'bg-dark-secondary'
                  }`}
                />
              )}
            </div>
          ))}
        </div>

        {/* Error message */}
        {error && (
          <div className="mx-6 mt-4 p-4 bg-red-500/10 border border-red-500/50 rounded-input text-red-400 text-sm">
            {error}
          </div>
        )}

        {/* Step Content */}
        <div className="p-6">
          {/* Step 1: Personal Info */}
          {currentStep === 1 && (
            <form onSubmit={step1Form.handleSubmit(handleStep1Submit)} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-2">
                    Nome *
                  </label>
                  <div className="relative">
                    <User className="absolute left-3 top-1/2 transform -translate-y-1/2 text-text-secondary w-5 h-5" />
                    <input
                      {...step1Form.register('first_name')}
                      className="input-field pl-10"
                      placeholder="Mario"
                    />
                  </div>
                  {step1Form.formState.errors.first_name && (
                    <p className="mt-1 text-sm text-red-400">
                      {step1Form.formState.errors.first_name.message}
                    </p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-2">
                    Cognome *
                  </label>
                  <div className="relative">
                    <User className="absolute left-3 top-1/2 transform -translate-y-1/2 text-text-secondary w-5 h-5" />
                    <input
                      {...step1Form.register('last_name')}
                      className="input-field pl-10"
                      placeholder="Rossi"
                    />
                  </div>
                  {step1Form.formState.errors.last_name && (
                    <p className="mt-1 text-sm text-red-400">
                      {step1Form.formState.errors.last_name.message}
                    </p>
                  )}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  Email *
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 text-text-secondary w-5 h-5" />
                  <input
                    type="email"
                    {...step1Form.register('email')}
                    className="input-field pl-10"
                    placeholder="nome@esempio.com"
                  />
                </div>
                {step1Form.formState.errors.email && (
                  <p className="mt-1 text-sm text-red-400">
                    {step1Form.formState.errors.email.message}
                  </p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  Cellulare *
                </label>
                <div className="relative">
                  <Phone className="absolute left-3 top-1/2 transform -translate-y-1/2 text-text-secondary w-5 h-5" />
                  <input
                    type="tel"
                    {...step1Form.register('phone')}
                    className="input-field pl-10"
                    placeholder="+39 123 456 7890"
                  />
                </div>
                {step1Form.formState.errors.phone && (
                  <p className="mt-1 text-sm text-red-400">
                    {step1Form.formState.errors.phone.message}
                  </p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  Password *
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-text-secondary w-5 h-5" />
                  <input
                    type={showPassword ? "text" : "password"}
                    {...step1Form.register('password')}
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
                {step1Form.formState.errors.password && (
                  <p className="mt-1 text-sm text-red-400">
                    {step1Form.formState.errors.password.message}
                  </p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  Conferma Password *
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-text-secondary w-5 h-5" />
                  <input
                    type={showConfirmPassword ? "text" : "password"}
                    {...step1Form.register('confirm_password')}
                    className="input-field pl-10 pr-10"
                    placeholder="••••••••"
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-text-secondary hover:text-text-primary transition-colors"
                  >
                    {showConfirmPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                  </button>
                </div>
                {step1Form.formState.errors.confirm_password && (
                  <p className="mt-1 text-sm text-red-400">
                    {step1Form.formState.errors.confirm_password.message}
                  </p>
                )}
              </div>

              <div className="flex justify-end pt-4">
                <button type="submit" className="btn-primary flex items-center gap-2">
                  <span>Avanti</span>
                  <ChevronRight className="w-5 h-5" />
                </button>
              </div>
            </form>
          )}

          {/* Step 2: Additional Info */}
          {currentStep === 2 && (
            <form onSubmit={step2Form.handleSubmit(handleStep2Submit)} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  Data di Nascita *
                </label>
                <div className="relative">
                  <Calendar 
                    className="absolute left-3 top-1/2 transform -translate-y-1/2 !text-white w-5 h-5 cursor-pointer z-10" 
                    style={{ color: '#FFFFFF' }}
                    onClick={() => {
                      dateInputRef.current?.showPicker?.();
                      dateInputRef.current?.focus();
                    }}
                  />
                  <input
                    type="date"
                    {...step2Form.register('date_of_birth', {
                      setValueAs: (value) => value,
                    })}
                    ref={(e) => {
                      const { ref } = step2Form.register('date_of_birth');
                      ref(e);
                      dateInputRef.current = e;
                    }}
                    className="input-field pl-10 [&::-webkit-calendar-picker-indicator]:hidden [&::-webkit-calendar-picker-indicator]:appearance-none"
                    style={{ 
                      colorScheme: 'dark',
                      WebkitAppearance: 'none',
                      MozAppearance: 'textfield'
                    }}
                  />
                </div>
                {step2Form.formState.errors.date_of_birth && (
                  <p className="mt-1 text-sm text-red-400">
                    {step2Form.formState.errors.date_of_birth.message}
                  </p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  Indirizzo Completo *
                </label>
                <div className="relative">
                  <MapPin className="absolute left-3 top-1/2 transform -translate-y-1/2 text-text-secondary w-5 h-5" />
                  <input
                    {...step2Form.register('address')}
                    className="input-field pl-10"
                    placeholder="Via, Numero Civico, Città"
                  />
                </div>
                {step2Form.formState.errors.address && (
                  <p className="mt-1 text-sm text-red-400">
                    {step2Form.formState.errors.address.message}
                  </p>
                )}
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-2">
                    Nazione *
                  </label>
                  <div className="relative">
                    <Globe className="absolute left-3 top-1/2 transform -translate-y-1/2 text-text-secondary w-5 h-5 pointer-events-none" />
                    <select
                      {...step2Form.register('country')}
                      className="input-field pl-10 appearance-none"
                    >
                      <option value="">Seleziona...</option>
                      {countries.map((country) => (
                        <option key={country.value} value={country.value}>
                          {country.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  {step2Form.formState.errors.country && (
                    <p className="mt-1 text-sm text-red-400">
                      {step2Form.formState.errors.country.message}
                    </p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-2">
                    Lingua Parlata *
                  </label>
                  <div className="relative">
                    <Globe className="absolute left-3 top-1/2 transform -translate-y-1/2 text-text-secondary w-5 h-5 pointer-events-none" />
                    <select
                      {...step2Form.register('language')}
                      className="input-field pl-10 appearance-none"
                    >
                      <option value="">Seleziona...</option>
                      {europeanLanguages.map((lang) => (
                        <option key={lang.value} value={lang.value}>
                          {lang.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  {step2Form.formState.errors.language && (
                    <p className="mt-1 text-sm text-red-400">
                      {step2Form.formState.errors.language.message}
                    </p>
                  )}
                </div>
              </div>

              <div className="flex justify-between pt-4">
                <button
                  type="button"
                  onClick={() => setCurrentStep(1)}
                  className="btn-outline flex items-center gap-2"
                >
                  <ChevronLeft className="w-5 h-5" />
                  <span>Indietro</span>
                </button>
                <button type="submit" className="btn-primary flex items-center gap-2">
                  <span>Avanti</span>
                  <ChevronRight className="w-5 h-5" />
                </button>
              </div>
            </form>
          )}

          {/* Step 3: Payment Method */}
          {currentStep === 3 && (
            <form onSubmit={step3Form.handleSubmit(handleStep3Submit)} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  Metodo di Pagamento *
                </label>
                <div className="relative">
                  <CreditCard className="absolute left-3 top-1/2 transform -translate-y-1/2 text-text-secondary w-5 h-5 pointer-events-none" />
                  <select
                    {...step3Form.register('payment_method')}
                    className="input-field pl-10 appearance-none"
                  >
                    <option value="">Seleziona...</option>
                    {paymentMethods.map((method) => (
                      <option key={method.id} value={method.id}>
                        {method.name}
                      </option>
                    ))}
                  </select>
                </div>
                {step3Form.formState.errors.payment_method && (
                  <p className="mt-1 text-sm text-red-400">
                    {step3Form.formState.errors.payment_method.message}
                  </p>
                )}
              </div>

              <div className="flex justify-between pt-4">
                <button
                  type="button"
                  onClick={() => setCurrentStep(2)}
                  className="btn-outline flex items-center gap-2"
                >
                  <ChevronLeft className="w-5 h-5" />
                  <span>Indietro</span>
                </button>
                <button
                  type="submit"
                  disabled={isLoading}
                  className="btn-primary flex items-center gap-2"
                >
                  {isLoading ? (
                    <>
                      <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      <span>Registrazione...</span>
                    </>
                  ) : (
                    <>
                      <span>Conferma Iscrizione</span>
                      <ChevronRight className="w-5 h-5" />
                    </>
                  )}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}

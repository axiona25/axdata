import { useState, useEffect, useRef } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import {
  User,
  Mail,
  Phone,
  Lock,
  Calendar,
  MapPin,
  Globe,
  Edit,
  Check,
  X,
  Eye,
  EyeOff,
} from 'lucide-react';
import Layout from '../components/Layout';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { authApi } from '../lib/auth';

// Schema di validazione
const profileSchema = z
  .object({
    first_name: z.string().min(2, 'Nome deve contenere almeno 2 caratteri'),
    last_name: z.string().min(2, 'Cognome deve contenere almeno 2 caratteri'),
    email: z.string().email('Email non valida'),
    phone: z.string().min(10, 'Numero di telefono non valido'),
    password: z.string().optional(),
    confirm_password: z.string().optional(),
    date_of_birth: z.string().min(1, 'Data di nascita richiesta'),
    address: z.string().min(5, 'Indirizzo completo richiesto'),
    country: z.string().min(1, 'Nazione richiesta'),
    language: z.string().min(1, 'Lingua parlata richiesta'),
  })
  .superRefine((data, ctx) => {
    // Valida password solo se è stata inserita
    if (data.password && data.password.length > 0) {
      if (data.password.length < 8) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: 'Password deve contenere almeno 8 caratteri',
          path: ['password'],
        });
      }
      if (data.password.length > 72) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: 'Password non può superare 72 caratteri',
          path: ['password'],
        });
      }
      if (!/[A-Z]/.test(data.password)) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: 'Password deve contenere almeno una lettera maiuscola',
          path: ['password'],
        });
      }
      if (!/[a-z]/.test(data.password)) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: 'Password deve contenere almeno una lettera minuscola',
          path: ['password'],
        });
      }
      if (!/[0-9]/.test(data.password)) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: 'Password deve contenere almeno un numero',
          path: ['password'],
        });
      }
      if (!/[^A-Za-z0-9]/.test(data.password)) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: 'Password deve contenere almeno un carattere speciale',
          path: ['password'],
        });
      }
      // Verifica che le password corrispondano
      if (data.password !== data.confirm_password) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: 'Le password non corrispondono',
          path: ['confirm_password'],
        });
      }
    }
  });

type ProfileFormData = z.infer<typeof profileSchema>;

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

export default function ProfilePage() {
  const [isEditing, setIsEditing] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const dateInputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();

  // Fetch user profile
  const { data: userProfile, isLoading: isLoadingProfile } = useQuery({
    queryKey: ['userProfile'],
    queryFn: authApi.getUserProfile,
    refetchOnMount: true,
    refetchOnWindowFocus: true,
  });

  // Fetch current user
  const { data: currentUser } = useQuery({
    queryKey: ['currentUser'],
    queryFn: authApi.getCurrentUser,
    refetchOnMount: true,
    refetchOnWindowFocus: true,
  });


  const form = useForm<ProfileFormData>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      first_name: '',
      last_name: '',
      email: '',
      phone: '',
      password: '',
      confirm_password: '',
      date_of_birth: '',
      address: '',
      country: '',
      language: '',
    },
  });

  // Populate form when profile data is loaded
  useEffect(() => {
    if (userProfile && currentUser) {
      const preferences = userProfile.preferences || {};
      form.reset({
        first_name: userProfile.first_name || '',
        last_name: userProfile.last_name || '',
        email: currentUser.email || '',
        phone: preferences.phone || '',
        password: '',
        confirm_password: '',
        date_of_birth: preferences.date_of_birth || '',
        address: preferences.address || '',
        country: preferences.country || '',
        language: preferences.language || '',
      });
    }
  }, [userProfile, currentUser, form]);

  const updateProfileMutation = useMutation({
    mutationFn: async (data: ProfileFormData) => {
      // Prepara i dati da inviare (escludi password se vuota)
      const updateData: any = {
        first_name: data.first_name,
        last_name: data.last_name,
        email: data.email,
        phone: data.phone,
        date_of_birth: data.date_of_birth,
        address: data.address,
        country: data.country,
        language: data.language,
      };

      // Aggiungi password solo se è stata modificata
      if (data.password && data.password.length > 0) {
        updateData.password = data.password;
      }

      // Qui chiameresti l'API per aggiornare il profilo
      // await authApi.updateProfile(updateData);
      // Per ora simuliamo con un delay
      await new Promise((resolve) => setTimeout(resolve, 1000));
      return updateData;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['userProfile'] });
      queryClient.invalidateQueries({ queryKey: ['currentUser'] });
      setIsEditing(false);
      // Reset password fields after save
      form.setValue('password', '');
      form.setValue('confirm_password', '');
    },
  });

  const handleSave = (data: ProfileFormData) => {
    updateProfileMutation.mutate(data);
  };

  const handleCancel = () => {
    // Reset form to original values
    if (userProfile && currentUser) {
      const preferences = userProfile.preferences || {};
      form.reset({
        first_name: userProfile.first_name || '',
        last_name: userProfile.last_name || '',
        email: currentUser.email || '',
        phone: preferences.phone || '',
        password: '',
        confirm_password: '',
        date_of_birth: preferences.date_of_birth || '',
        address: preferences.address || '',
        country: preferences.country || '',
        language: preferences.language || '',
      });
    }
    setIsEditing(false);
  };

  const password = form.watch('password');

  const getPasswordStrength = (password: string) => {
    if (!password) return 0;
    let strength = 0;
    if (password.length >= 8) strength++;
    if (/[A-Z]/.test(password)) strength++;
    if (/[a-z]/.test(password)) strength++;
    if (/[0-9]/.test(password)) strength++;
    if (/[^A-Za-z0-9]/.test(password)) strength++;
    return strength;
  };

  if (isLoadingProfile) {
    return (
      <Layout headerTitle="Profilo" headerSubtitle="Gestisci i tuoi dati personali">
        <div className="flex items-center justify-center h-64">
          <div className="text-text-secondary">Caricamento...</div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout headerTitle="Profilo" headerSubtitle="Gestisci i tuoi dati personali">
      <div className="space-y-6">
        <div className="card border" style={{ borderColor: '#007ed2' }}>
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-text-primary">Dati Personali</h3>
            {!isEditing && (
              <button
                onClick={() => setIsEditing(true)}
                className="flex items-center gap-2 px-3 py-1.5 rounded-input hover:bg-dark-secondary transition-colors text-sm text-text-secondary hover:text-text-primary"
              >
                <Edit className="w-4 h-4" />
                Modifica
              </button>
            )}
          </div>

          <form onSubmit={form.handleSubmit(handleSave)} className="space-y-6">
            {/* Campi principali in due colonne */}
            <div className="grid grid-cols-2 gap-6">
              {/* Colonna 1 */}
              <div className="space-y-4">
                {/* Nome */}
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-2">
                    Nome *
                  </label>
                  <div className="relative">
                    <User className="absolute left-3 top-1/2 transform -translate-y-1/2 text-text-secondary w-5 h-5" />
                    <input
                      {...form.register('first_name')}
                      disabled={!isEditing}
                      className="input-field pl-10 disabled:opacity-50 disabled:cursor-not-allowed"
                      placeholder="Mario"
                    />
                  </div>
                  {form.formState.errors.first_name && (
                    <p className="mt-1 text-sm text-red-400">
                      {form.formState.errors.first_name.message}
                    </p>
                  )}
                </div>

                {/* Cognome */}
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-2">
                    Cognome *
                  </label>
                  <div className="relative">
                    <User className="absolute left-3 top-1/2 transform -translate-y-1/2 text-text-secondary w-5 h-5" />
                    <input
                      {...form.register('last_name')}
                      disabled={!isEditing}
                      className="input-field pl-10 disabled:opacity-50 disabled:cursor-not-allowed"
                      placeholder="Rossi"
                    />
                  </div>
                  {form.formState.errors.last_name && (
                    <p className="mt-1 text-sm text-red-400">
                      {form.formState.errors.last_name.message}
                    </p>
                  )}
                </div>

                {/* Data di Nascita */}
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-2">
                    Data di Nascita *
                  </label>
                  <div className="relative">
                    <Calendar
                      className="absolute left-3 top-1/2 transform -translate-y-1/2 !text-white w-5 h-5 cursor-pointer z-10"
                      style={{ color: '#FFFFFF' }}
                      onClick={() => {
                        if (isEditing) {
                          dateInputRef.current?.showPicker?.();
                          dateInputRef.current?.focus();
                        }
                      }}
                    />
                    <input
                      type="date"
                      {...form.register('date_of_birth', {
                        setValueAs: (value) => value,
                      })}
                      ref={(e) => {
                        const { ref } = form.register('date_of_birth');
                        ref(e);
                        dateInputRef.current = e;
                      }}
                      disabled={!isEditing}
                      className="input-field pl-10 disabled:opacity-50 disabled:cursor-not-allowed [&::-webkit-calendar-picker-indicator]:hidden [&::-webkit-calendar-picker-indicator]:appearance-none"
                      style={{
                        colorScheme: 'dark',
                        WebkitAppearance: 'none',
                        MozAppearance: 'textfield',
                      }}
                    />
                  </div>
                  {form.formState.errors.date_of_birth && (
                    <p className="mt-1 text-sm text-red-400">
                      {form.formState.errors.date_of_birth.message}
                    </p>
                  )}
                </div>

                {/* Indirizzo */}
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-2">
                    Indirizzo Completo *
                  </label>
                  <div className="relative">
                    <MapPin className="absolute left-3 top-1/2 transform -translate-y-1/2 text-text-secondary w-5 h-5" />
                    <input
                      {...form.register('address')}
                      disabled={!isEditing}
                      className="input-field pl-10 disabled:opacity-50 disabled:cursor-not-allowed"
                      placeholder="Via, Numero Civico, Città"
                    />
                  </div>
                  {form.formState.errors.address && (
                    <p className="mt-1 text-sm text-red-400">
                      {form.formState.errors.address.message}
                    </p>
                  )}
                </div>
              </div>

              {/* Colonna 2 */}
              <div className="space-y-4">
                {/* Email */}
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-2">
                    Email *
                  </label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 text-text-secondary w-5 h-5" />
                    <input
                      type="email"
                      {...form.register('email')}
                      disabled={!isEditing}
                      className="input-field pl-10 disabled:opacity-50 disabled:cursor-not-allowed"
                      placeholder="nome@esempio.com"
                    />
                  </div>
                  {form.formState.errors.email && (
                    <p className="mt-1 text-sm text-red-400">
                      {form.formState.errors.email.message}
                    </p>
                  )}
                </div>

                {/* Cellulare */}
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-2">
                    Cellulare *
                  </label>
                  <div className="relative">
                    <Phone className="absolute left-3 top-1/2 transform -translate-y-1/2 text-text-secondary w-5 h-5" />
                    <input
                      type="tel"
                      {...form.register('phone')}
                      disabled={!isEditing}
                      className="input-field pl-10 disabled:opacity-50 disabled:cursor-not-allowed"
                      placeholder="+39 123 456 7890"
                    />
                  </div>
                  {form.formState.errors.phone && (
                    <p className="mt-1 text-sm text-red-400">
                      {form.formState.errors.phone.message}
                    </p>
                  )}
                </div>

                {/* Nazione */}
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-2">
                    Nazione *
                  </label>
                  <div className="relative">
                    <Globe className="absolute left-3 top-1/2 transform -translate-y-1/2 text-text-secondary w-5 h-5 pointer-events-none" />
                    <select
                      {...form.register('country')}
                      disabled={!isEditing}
                      className="input-field pl-10 appearance-none disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <option value="">Seleziona...</option>
                      {countries.map((country) => (
                        <option key={country.value} value={country.value}>
                          {country.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  {form.formState.errors.country && (
                    <p className="mt-1 text-sm text-red-400">
                      {form.formState.errors.country.message}
                    </p>
                  )}
                </div>

                {/* Lingua Parlata */}
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-2">
                    Lingua Parlata *
                  </label>
                  <div className="relative">
                    <Globe className="absolute left-3 top-1/2 transform -translate-y-1/2 text-text-secondary w-5 h-5 pointer-events-none" />
                    <select
                      {...form.register('language')}
                      disabled={!isEditing}
                      className="input-field pl-10 appearance-none disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <option value="">Seleziona...</option>
                      {europeanLanguages.map((lang) => (
                        <option key={lang.value} value={lang.value}>
                          {lang.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  {form.formState.errors.language && (
                    <p className="mt-1 text-sm text-red-400">
                      {form.formState.errors.language.message}
                    </p>
                  )}
                </div>
              </div>
            </div>

            {/* Password - solo in modalità modifica */}
            {isEditing && (
              <>
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-2">
                    Nuova Password (lascia vuoto per non modificare)
                  </label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-text-secondary w-5 h-5" />
                    <input
                      type={showPassword ? 'text' : 'password'}
                      {...form.register('password')}
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
                        La password deve contenere: maiuscole, minuscole, numeri e caratteri
                        speciali
                      </p>
                    </div>
                  )}
                  {form.formState.errors.password && (
                    <p className="mt-1 text-sm text-red-400">
                      {form.formState.errors.password.message}
                    </p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-2">
                    Conferma Password
                  </label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-text-secondary w-5 h-5" />
                    <input
                      type={showConfirmPassword ? 'text' : 'password'}
                      {...form.register('confirm_password')}
                      className="input-field pl-10 pr-10"
                      placeholder="••••••••"
                    />
                    <button
                      type="button"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      className="absolute right-3 top-1/2 transform -translate-y-1/2 text-text-secondary hover:text-text-primary transition-colors"
                    >
                      {showConfirmPassword ? (
                        <EyeOff className="w-5 h-5" />
                      ) : (
                        <Eye className="w-5 h-5" />
                      )}
                    </button>
                  </div>
                  {form.formState.errors.confirm_password && (
                    <p className="mt-1 text-sm text-red-400">
                      {form.formState.errors.confirm_password.message}
                    </p>
                  )}
                </div>
              </>
            )}

            {/* Action Buttons */}
            {isEditing && (
              <div className="flex gap-3 pt-4 border-t border-dark-secondary">
                <button
                  type="submit"
                  disabled={updateProfileMutation.isPending}
                  className="px-4 py-2 bg-accent-blue text-white rounded-input hover:bg-accent-blue/90 transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {updateProfileMutation.isPending ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      <span>Salvataggio...</span>
                    </>
                  ) : (
                    <>
                      <Check className="w-4 h-4" />
                      <span>Salva Modifiche</span>
                    </>
                  )}
                </button>
                <button
                  type="button"
                  onClick={handleCancel}
                  disabled={updateProfileMutation.isPending}
                  className="px-4 py-2 bg-dark-secondary text-text-primary rounded-input hover:bg-dark-secondary/80 transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <X className="w-4 h-4" />
                  <span>Annulla</span>
                </button>
              </div>
            )}
          </form>
        </div>
      </div>
    </Layout>
  );
}

import { Navigate } from 'react-router-dom';
import { ReactNode } from 'react';
import { useQuery } from '@tanstack/react-query';
import { authApi } from '../lib/auth';

interface ProtectedRouteProps {
  children: ReactNode;
}

export default function ProtectedRoute({ children }: ProtectedRouteProps) {
  // Check if user is authenticated by checking for access token
  const accessToken = localStorage.getItem('access_token');
  
  // If no token, redirect immediately
  if (!accessToken) {
    return <Navigate to="/login" replace />;
  }
  
  // Validate token by fetching user data
  const { isLoading, isError, error } = useQuery({
    queryKey: ['user'],
    queryFn: authApi.getCurrentUser,
    retry: false,
    staleTime: 5 * 60 * 1000, // 5 minutes
    enabled: !!accessToken, // Only run if token exists
  });
  
  // Show loading state while validating
  if (isLoading) {
    return (
      <div className="min-h-screen bg-dark-primary flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 bg-accent-blue/20 rounded-full flex items-center justify-center mx-auto mb-4">
            <div className="w-8 h-8 border-4 border-accent-blue border-t-transparent rounded-full animate-spin" />
          </div>
          <p className="text-text-secondary">Verifica autenticazione...</p>
        </div>
      </div>
    );
  }
  
  // If token is invalid or CORS/network error, redirect to login
  if (isError) {
    // Check if it's a CORS or network error (backend might not be running)
    const errorMessage = (error as any)?.message || '';
    if (errorMessage.includes('CORS') || errorMessage.includes('Network error') || errorMessage.includes('ERR_FAILED')) {
      console.error('Backend connection error:', errorMessage);
      // Don't clear tokens if it's just a connection issue
      // User can retry when backend is available
    } else {
      // Real auth error - clear tokens
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    }
    return <Navigate to="/login" replace />;
  }
  
  return <>{children}</>;
}

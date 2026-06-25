/**
 * Dev page : Auto-login with super_admin credentials for testing
 * DISABLED IN PRODUCTION
 */
import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { toast } from 'sonner';

export default function DevLogin() {
  const navigate = useNavigate();
  const { login, user, isLoading } = useAuth();

  // SECURITY: Block in production
  if (process.env.NODE_ENV === 'production') {
    return (
      <div style={{ padding: 40, textAlign: 'center' }}>
        <h2>404 — Page introuvable</h2>
        <a href="/login">Retour à la connexion</a>
      </div>
    );
  }

  useEffect(() => {
    if (user) {
      toast.success('✓ Logged in as ' + user.email);
      setTimeout(() => navigate('/dashboard'), 1000);
      return;
    }
    if (isLoading) return;
    const doLogin = async () => {
      try {
        await login('pissken@editionsfabsci.com', 'Admin@2027');
        toast.success('✓ Dev login successful');
        setTimeout(() => navigate('/dashboard'), 500);
      } catch (err) {
        toast.error('Login failed: ' + (err.response?.data?.detail || err.message));
      }
    };
    doLogin();
  }, [login, navigate, user, isLoading]);

  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', flexDirection: 'column', gap: 16 }}>
      <div style={{ fontSize: 32 }}>🔐</div>
      <p style={{ color: '#666' }}>Dev login en cours...</p>
    </div>
  );
}

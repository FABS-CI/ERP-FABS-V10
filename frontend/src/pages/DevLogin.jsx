/**
 * Dev page : Auto-login with super_admin credentials for testing
 * Access: http://localhost:3000/dev-login
 */
import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { toast } from 'sonner';

export default function DevLogin() {
  const navigate = useNavigate();
  const { login, user, isLoading } = useAuth();

  useEffect(() => {
    if (user) {
      // Already logged in
      toast.success('✓ Logged in as ' + user.email);
      setTimeout(() => navigate('/dashboard'), 1000);
      return;
    }

    if (isLoading) return;

    // Auto-login
    const doLogin = async () => {
      try {
        await login('pissken@editionsfabsci.com', 'Admin@2025');
        toast.success('✓ Dev login successful');
        setTimeout(() => navigate('/dashboard'), 500);
      } catch (err) {
        toast.error('Login failed: ' + (err.response?.data?.detail || err.message));
      }
    };

    doLogin();
  }, [login, navigate, user, isLoading]);

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      height: '100vh',
      background: '#0F172A',
      color: '#E2E8F0',
      fontSize: 16,
    }}>
      <div style={{ textAlign: 'center', gap: 16, display: 'flex', flexDirection: 'column' }}>
        <div style={{ fontSize: 24, fontWeight: 700 }}>FABS ERP</div>
        <div>Logging in as super_admin...</div>
        <div style={{ fontSize: 12, color: '#94A3B8' }}>
          Email: pissken@editionsfabsci.com
        </div>
      </div>
    </div>
  );
}

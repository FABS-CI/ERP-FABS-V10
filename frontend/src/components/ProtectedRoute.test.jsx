import React from 'react';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import ProtectedRoute from './ProtectedRoute';
import { AuthProvider } from '../hooks/useAuth';

// Mock useAuth hook
jest.mock('../hooks/useAuth', () => ({
  __esModule: true,
  useAuth: () => ({
    user: { role: 'super_admin' },
    isLoading: false,
  }),
  AuthProvider: ({ children }) => <div>{children}</div>,
}));

describe('ProtectedRoute', () => {
  it('renders children when user is authenticated', () => {
    render(
      <BrowserRouter>
        <AuthProvider>
          <ProtectedRoute>
            <div>Protected Content</div>
          </ProtectedRoute>
        </AuthProvider>
      </BrowserRouter>
    );
    expect(screen.getByText('Protected Content')).toBeInTheDocument();
  });
});

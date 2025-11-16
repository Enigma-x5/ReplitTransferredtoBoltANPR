import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { apiClient } from '@/api/client';
import { tokenStorage } from './tokenStorage';

interface AuthContextType {
  isAuthenticated: boolean;
  isLoading: boolean;
  user: { email?: string; role?: 'admin' | 'clerk' } | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [user, setUser] = useState<{ email?: string; role?: 'admin' | 'clerk' } | null>(null);

  useEffect(() => {
    // Check for existing token on mount
    const token = tokenStorage.getToken();
    const userInfo = tokenStorage.getUserInfo();
    
    if (token && userInfo && (userInfo.role === 'admin' || userInfo.role === 'clerk')) {
      setIsAuthenticated(true);
      setUser({ email: userInfo.email, role: userInfo.role });
    }
    
    setIsLoading(false);
  }, []);

  const login = async (email: string, password: string) => {
    const response = await apiClient.login(email, password);
    
    tokenStorage.setToken(response.access_token);
    
    // Extract role from token or fetch user info
    // For now, assume we get user info from a separate call or decode JWT
    const userInfo = { email, role: 'clerk' as 'admin' | 'clerk' }; // Will be enhanced
    tokenStorage.setUserInfo(userInfo);
    
    setIsAuthenticated(true);
    setUser(userInfo);
  };

  const logout = () => {
    tokenStorage.clearToken();
    setIsAuthenticated(false);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, isLoading, user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

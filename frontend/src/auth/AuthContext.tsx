import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { jwtDecode } from 'jwt-decode';
import { apiClient } from '@/api/client';
import { tokenStorage } from './tokenStorage';

interface JwtPayload {
  sub: string;
  role: 'admin' | 'clerk';
  exp: number;
}

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
    const token = tokenStorage.getToken();
    const userInfo = tokenStorage.getUserInfo();
    
    if (token) {
      try {
        const decoded = jwtDecode<JwtPayload>(token);
        const now = Date.now() / 1000;
        
        if (decoded.exp && decoded.exp > now) {
          const role: 'admin' | 'clerk' = decoded.role === 'admin' ? 'admin' : 'clerk';
          setIsAuthenticated(true);
          setUser({ email: userInfo?.email, role });
        } else {
          tokenStorage.clearToken();
          setIsAuthenticated(false);
          setUser(null);
        }
      } catch {
        tokenStorage.clearToken();
        setIsAuthenticated(false);
        setUser(null);
      }
    }
    
    setIsLoading(false);
  }, []);

  const login = async (email: string, password: string) => {
    const response = await apiClient.login(email, password);

    tokenStorage.setToken(response.access_token);

    const decoded = jwtDecode<JwtPayload>(response.access_token);
    const role: 'admin' | 'clerk' = decoded.role === 'admin' ? 'admin' : 'clerk';
    const userInfo = { email, role };
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

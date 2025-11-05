import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

export interface User {
  id: string;
  email: string;
  name: string | null;
  organization_id: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name: string, organizationName: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Load token from localStorage on mount
  useEffect(() => {
    const storedToken = localStorage.getItem('auth_token');
    const storedUser = localStorage.getItem('auth_user');
    
    if (storedToken && storedUser) {
      try {
        setToken(storedToken);
        setUser(JSON.parse(storedUser));
      } catch (e) {
        console.error('Failed to parse stored user:', e);
        localStorage.removeItem('auth_token');
        localStorage.removeItem('auth_user');
      }
    }
    setIsLoading(false);
  }, []);

  const login = async (email: string, password: string) => {
    let API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    // Override if pointing to Koyeb or production
    if (API_BASE_URL.includes('koyeb') || API_BASE_URL.includes('netlify') || API_BASE_URL.includes('production')) {
      API_BASE_URL = 'http://localhost:8000';
    }
    let baseUrl = API_BASE_URL;
    if (baseUrl && !baseUrl.startsWith('http://') && !baseUrl.startsWith('https://')) {
      baseUrl = `https://${baseUrl}`;
    }

    // Wake up backend with health check first (only on first attempt)
    try {
      const healthController = new AbortController();
      const healthTimeout = setTimeout(() => healthController.abort(), 30000); // 30s for health check
      await fetch(`${baseUrl}/healthz`, { 
        method: 'GET',
        signal: healthController.signal,
      }).catch(() => {
        // Ignore health check errors - backend might be waking up
      });
      clearTimeout(healthTimeout);
      // Small delay to let backend fully wake up
      await new Promise(resolve => setTimeout(resolve, 2000));
    } catch {
      // Continue anyway - health check is optional
    }

    // Retry logic for cold starts (up to 3 attempts with exponential backoff)
    let lastError: Error | null = null;
    let timeoutId: NodeJS.Timeout | null = null;
    
    for (let attempt = 0; attempt < 3; attempt++) {
      try {
        const controller = new AbortController();
        timeoutId = setTimeout(() => controller.abort(), 45000); // 45 seconds timeout

        const response = await fetch(`${baseUrl}/auth/login`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ email, password }),
          signal: controller.signal,
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
          const error = await response.json().catch(() => ({ detail: 'Login failed' }));
          throw new Error(error.detail || 'Invalid email or password');
        }

        const data = await response.json();
        const userData: User = {
          id: data.user_id,
          email: data.email,
          name: data.name,
          organization_id: data.organization_id,
        };

        setToken(data.access_token);
        setUser(userData);
        localStorage.setItem('auth_token', data.access_token);
        localStorage.setItem('auth_user', JSON.stringify(userData));
        if (timeoutId) clearTimeout(timeoutId);
        return; // Success, exit retry loop
      } catch (err) {
        if (timeoutId) clearTimeout(timeoutId);
        lastError = err instanceof Error ? err : new Error('Login failed');
        
        const isTimeout = lastError.message.includes('aborted') || 
                         lastError.message.includes('timeout') ||
                         lastError.message.includes('ERR_TIMED_OUT') ||
                         lastError.message.includes('Failed to fetch');
        
        if (!isTimeout || attempt === 2) {
          // Not a timeout error, or last attempt - throw immediately
          throw lastError;
        }
        
        // Wait before retry (exponential backoff: 2s, 4s)
        await new Promise(resolve => setTimeout(resolve, 2000 * Math.pow(2, attempt)));
        console.debug(`Login attempt ${attempt + 1} failed, retrying...`);
      }
    }
    
    throw lastError || new Error('Login failed after all retries');
  };

  const register = async (email: string, password: string, name: string, organizationName: string) => {
    let API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    // Override if pointing to Koyeb or production
    if (API_BASE_URL.includes('koyeb') || API_BASE_URL.includes('netlify') || API_BASE_URL.includes('production')) {
      API_BASE_URL = 'http://localhost:8000';
    }
    let baseUrl = API_BASE_URL;
    if (baseUrl && !baseUrl.startsWith('http://') && !baseUrl.startsWith('https://')) {
      baseUrl = `https://${baseUrl}`;
    }

    // Wake up backend with health check first (only on first attempt)
    try {
      const healthController = new AbortController();
      const healthTimeout = setTimeout(() => healthController.abort(), 30000); // 30s for health check
      await fetch(`${baseUrl}/healthz`, { 
        method: 'GET',
        signal: healthController.signal,
      }).catch(() => {
        // Ignore health check errors - backend might be waking up
      });
      clearTimeout(healthTimeout);
      // Small delay to let backend fully wake up
      await new Promise(resolve => setTimeout(resolve, 2000));
    } catch {
      // Continue anyway - health check is optional
    }

    // Retry logic for cold starts (up to 3 attempts with exponential backoff)
    let lastError: Error | null = null;
    let timeoutId: NodeJS.Timeout | null = null;
    
    for (let attempt = 0; attempt < 3; attempt++) {
      try {
        const controller = new AbortController();
        timeoutId = setTimeout(() => controller.abort(), 45000); // 45 seconds timeout

        const response = await fetch(`${baseUrl}/auth/register`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ 
            email, 
            password, 
            name,
            organization_name: organizationName,
          }),
          signal: controller.signal,
        });

        if (timeoutId) clearTimeout(timeoutId);

        if (!response.ok) {
          const error = await response.json().catch(() => ({ detail: 'Registration failed' }));
          throw new Error(error.detail || 'Registration failed');
        }

        const data = await response.json();
        const userData: User = {
          id: data.user_id,
          email: data.email,
          name: data.name,
          organization_id: data.organization_id,
        };

        setToken(data.access_token);
        setUser(userData);
        localStorage.setItem('auth_token', data.access_token);
        localStorage.setItem('auth_user', JSON.stringify(userData));
        return; // Success, exit retry loop
      } catch (err) {
        if (timeoutId) clearTimeout(timeoutId);
        lastError = err instanceof Error ? err : new Error('Registration failed');
        
        const isTimeout = lastError.message.includes('aborted') || 
                         lastError.message.includes('timeout') ||
                         lastError.message.includes('ERR_TIMED_OUT') ||
                         lastError.message.includes('Failed to fetch');
        
        if (!isTimeout || attempt === 2) {
          // Not a timeout error, or last attempt - throw immediately
          throw lastError;
        }
        
        // Wait before retry (exponential backoff: 2s, 4s)
        await new Promise(resolve => setTimeout(resolve, 2000 * Math.pow(2, attempt)));
        console.debug(`Registration attempt ${attempt + 1} failed, retrying...`);
      }
    }
    
    throw lastError || new Error('Registration failed after all retries');
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('auth_token');
    localStorage.removeItem('auth_user');
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        login,
        register,
        logout,
        isAuthenticated: !!token,
        isLoading,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};


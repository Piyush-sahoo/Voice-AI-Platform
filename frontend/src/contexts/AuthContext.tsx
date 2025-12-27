import { createContext, useContext, useState, useEffect, ReactNode } from "react";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

interface User {
  user_id: string;
  email: string;
  name: string;
  workspace_id: string;
  role: string;
}

interface Tokens {
  access_token: string;
  refresh_token: string;
  expires_in: number;
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string, name: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
  getAccessToken: () => string | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check for stored user and tokens on mount
    const storedUser = localStorage.getItem("voiceai_user");
    const storedTokens = localStorage.getItem("voiceai_tokens");
    
    if (storedUser && storedTokens) {
      setUser(JSON.parse(storedUser));
      // TODO: Validate token expiry and refresh if needed
    }
    setIsLoading(false);
  }, []);

  const login = async (email: string, password: string) => {
    setIsLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Login failed");
      }

      const data = await response.json();
      
      setUser(data.user);
      localStorage.setItem("voiceai_user", JSON.stringify(data.user));
      localStorage.setItem("voiceai_tokens", JSON.stringify(data.tokens));
    } finally {
      setIsLoading(false);
    }
  };

  const signup = async (email: string, password: string, name: string) => {
    setIsLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, name }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Signup failed");
      }

      const data = await response.json();
      
      setUser(data.user);
      localStorage.setItem("voiceai_user", JSON.stringify(data.user));
      localStorage.setItem("voiceai_tokens", JSON.stringify(data.tokens));
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem("voiceai_user");
    localStorage.removeItem("voiceai_tokens");
  };

  const getAccessToken = (): string | null => {
    const tokens = localStorage.getItem("voiceai_tokens");
    if (tokens) {
      const parsed: Tokens = JSON.parse(tokens);
      return parsed.access_token;
    }
    return null;
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        login,
        signup,
        logout,
        isAuthenticated: !!user,
        getAccessToken,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}

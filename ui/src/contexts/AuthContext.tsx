// ui/src/contexts/AuthContext.tsx
import React, { createContext, useState, useContext, useEffect, useCallback } from 'react';
import type { ReactNode } from 'react';
import type { User, UserLoginData, UserCreateData } from '../types/authTypes';
import authService from '../services/authService'; 

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  loginUser: (credentials: UserLoginData) => Promise<User>;
  signupUser: (userData: UserCreateData) => Promise<User>;
  logoutUser: () => Promise<void>;
  fetchCurrentUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true); // Start true to load initial user state

  const fetchCurrentUser = useCallback(async () => {
    setIsLoading(true);
    try {
      const currentUser = await authService.getCurrentUser();
      setUser(currentUser);
    } catch {
      // console.info('No active session or failed to fetch user.'); // Handled by authService
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);
  
  useEffect(() => {
    fetchCurrentUser();
  }, [fetchCurrentUser]);

  const loginUser = async (credentials: UserLoginData): Promise<User> => {
    setIsLoading(true);
    try {
      const loggedInUser = await authService.login(credentials);
      setUser(loggedInUser);
      setIsLoading(false);
      return loggedInUser;
    } catch (error) {
      setIsLoading(false);
      throw error; // Re-throw to be caught by the form
    }
  };

  const signupUser = async (userData: UserCreateData): Promise<User> => {
    setIsLoading(true);
    try {
      const signedUpUser = await authService.signup(userData);
      setUser(signedUpUser); // Automatically log in after signup
      setIsLoading(false);
      return signedUpUser;
    } catch (error) {
      setIsLoading(false);
      throw error; // Re-throw to be caught by the form
    }
  };

  const logoutUser = async () => {
    setIsLoading(true);
    try {
        await authService.logout();
        setUser(null);
    } catch (error) {
        console.error("Logout failed:", error);
        // Decide if you want to clear user state even if API fails
        // setUser(null); 
    } finally {
        setIsLoading(false);
    }
  };

  return (
    <AuthContext.Provider value={{ 
        user, 
        isLoading, 
        isAuthenticated: !!user, 
        loginUser, 
        signupUser, 
        logoutUser,
        fetchCurrentUser 
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
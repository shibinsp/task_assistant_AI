import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { authService } from '@/services/auth.service';
import { mapCurrentUserToFrontend, splitFullName } from '@/types/mappers';
import { queryClient } from '@/hooks/useApi';

export interface User {
  id: string;
  email: string;
  name: string;
  avatar?: string;
  role: 'admin' | 'manager' | 'member' | 'viewer';
  organizationId?: string;
}

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  googleLogin: (credential: string) => Promise<void>;
  signup: (email: string, password: string, name: string, company?: string, role?: string) => Promise<void>;
  logout: () => void;
  updateUser: (user: Partial<User>) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,

      login: async (email: string, password: string) => {
        set({ isLoading: true });
        try {
          const response = await authService.login(email, password);
          const frontendUser = mapCurrentUserToFrontend(response.user);
          set({
            user: frontendUser,
            accessToken: response.tokens.access_token,
            refreshToken: response.tokens.refresh_token,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },

      googleLogin: async (credential: string) => {
        set({ isLoading: true });
        try {
          const response = await authService.googleLogin(credential);
          const frontendUser = mapCurrentUserToFrontend(response.user);
          set({
            user: frontendUser,
            accessToken: response.tokens.access_token,
            refreshToken: response.tokens.refresh_token,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },

      signup: async (email: string, password: string, name: string, company?: string, role?: string) => {
        set({ isLoading: true });
        try {
          const { firstName, lastName } = splitFullName(name);
          const response = await authService.register(
            email,
            password,
            firstName,
            lastName,
            company || undefined,
            role || undefined
          );
          const frontendUser = mapCurrentUserToFrontend(response.user);
          set({
            user: frontendUser,
            accessToken: response.tokens.access_token,
            refreshToken: response.tokens.refresh_token,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },

      logout: () => {
        const { accessToken } = get();
        if (accessToken) {
          authService.logout().catch(() => {});
        }
        queryClient.clear();
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
        });
      },

      updateUser: (userData) => {
        set((state) => ({
          user: state.user ? { ...state.user, ...userData } : null,
        }));
      },
    }),
    {
      name: 'taskpulse-auth',
    }
  )
);

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { supabase } from '@/lib/supabase';
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
  oauthLogin: () => Promise<void>;
  signup: (email: string, password: string, name: string, company?: string, role?: string) => Promise<void>;
  logout: () => void;
  updateUser: (user: Partial<User>) => void;
  initAuth: () => () => void;
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
          const { data, error } = await supabase.auth.signInWithPassword({ email, password });
          if (error) throw error;

          // Fetch full user profile with RBAC data from backend
          const meResponse = await authService.getMe();
          const frontendUser = mapCurrentUserToFrontend(meResponse);

          set({
            user: frontendUser,
            accessToken: data.session?.access_token ?? null,
            refreshToken: data.session?.refresh_token ?? null,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },

      oauthLogin: async () => {
        set({ isLoading: true });
        try {
          const { error } = await supabase.auth.signInWithOAuth({
            provider: 'google',
            options: {
              redirectTo: window.location.origin + '/auth/callback',
            },
          });
          if (error) throw error;
          // OAuth redirects the browser; state is set via onAuthStateChange after redirect
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },

      signup: async (email: string, password: string, name: string, company?: string, role?: string) => {
        set({ isLoading: true });
        try {
          const { firstName, lastName } = splitFullName(name);

          // Sign up with Supabase Auth
          const { data, error } = await supabase.auth.signUp({
            email,
            password,
            options: {
              data: { first_name: firstName, last_name: lastName },
            },
          });
          if (error) throw error;

          // Create the local user record in backend (org, role, etc.)
          const registerResponse = await authService.register(
            email,
            password,
            firstName,
            lastName,
            company || undefined,
            role || undefined,
          );
          const frontendUser = mapCurrentUserToFrontend(registerResponse.user);

          set({
            user: frontendUser,
            accessToken: data.session?.access_token ?? null,
            refreshToken: data.session?.refresh_token ?? null,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },

      logout: () => {
        supabase.auth.signOut().catch(() => {});
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

      initAuth: () => {
        const { data: { subscription } } = supabase.auth.onAuthStateChange(
          async (event, session) => {
            if (event === 'SIGNED_IN' || event === 'TOKEN_REFRESHED') {
              if (session) {
                set({
                  accessToken: session.access_token,
                  refreshToken: session.refresh_token,
                });
                try {
                  const meResponse = await authService.getMe();
                  const frontendUser = mapCurrentUserToFrontend(meResponse);
                  set({
                    user: frontendUser,
                    isAuthenticated: true,
                    isLoading: false,
                  });
                } catch {
                  // Backend may not be reachable yet; tokens are stored,
                  // user profile will be fetched on next navigation
                }
              }
            } else if (event === 'SIGNED_OUT') {
              queryClient.clear();
              set({
                user: null,
                accessToken: null,
                refreshToken: null,
                isAuthenticated: false,
              });
            }
          },
        );

        // Return unsubscribe function for cleanup
        return () => {
          subscription.unsubscribe();
        };
      },
    }),
    {
      name: 'taskpulse-auth',
    }
  )
);

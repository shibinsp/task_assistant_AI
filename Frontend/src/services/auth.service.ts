import apiClient from '@/lib/api-client';
import type {
  ApiLoginResponse,
  ApiRegisterResponse,
  ApiTokenResponse,
  ApiCurrentUser,
  ApiPasswordChange,
  ApiUserUpdate,
  ApiConsentResponse,
  ApiConsentUpdate,
  ApiSession,
} from '@/types/api';

export const authService = {
  async login(email: string, password: string): Promise<ApiLoginResponse> {
    const { data } = await apiClient.post<ApiLoginResponse>('/auth/login', { email, password });
    return data;
  },

  async googleLogin(credential: string): Promise<ApiLoginResponse> {
    const { data } = await apiClient.post<ApiLoginResponse>('/auth/google', { credential });
    return data;
  },

  async register(
    email: string,
    password: string,
    firstName: string,
    lastName: string,
    orgName?: string,
    role?: string
  ): Promise<ApiRegisterResponse> {
    const { data } = await apiClient.post<ApiRegisterResponse>('/auth/register', {
      email,
      password,
      first_name: firstName,
      last_name: lastName,
      org_name: orgName || undefined,
      role: role || undefined,
    });
    return data;
  },

  async refresh(refreshToken: string): Promise<ApiTokenResponse> {
    const { data } = await apiClient.post<ApiTokenResponse>('/auth/refresh', {
      refresh_token: refreshToken,
    });
    return data;
  },

  async logout(): Promise<void> {
    await apiClient.post('/auth/logout');
  },

  async logoutAll(): Promise<{ message: string }> {
    const { data } = await apiClient.post<{ message: string }>('/auth/logout-all');
    return data;
  },

  async getMe(): Promise<ApiCurrentUser> {
    const { data } = await apiClient.get<ApiCurrentUser>('/auth/me');
    return data;
  },

  async changePassword(payload: ApiPasswordChange): Promise<void> {
    await apiClient.post('/auth/change-password', payload);
  },

  async updateProfile(userId: string, payload: ApiUserUpdate): Promise<void> {
    await apiClient.patch(`/users/${userId}`, payload);
  },

  async forgotPassword(email: string): Promise<{ message: string }> {
    const { data } = await apiClient.post<{ message: string }>('/auth/forgot-password', { email });
    return data;
  },

  async resetPassword(token: string, newPassword: string): Promise<{ message: string }> {
    const { data } = await apiClient.post<{ message: string }>('/auth/reset-password', {
      token,
      new_password: newPassword,
    });
    return data;
  },

  async getConsent(): Promise<ApiConsentResponse> {
    const { data } = await apiClient.get<ApiConsentResponse>('/auth/consent');
    return data;
  },

  async updateConsent(payload: ApiConsentUpdate): Promise<ApiConsentResponse> {
    const { data } = await apiClient.patch<ApiConsentResponse>('/auth/consent', payload);
    return data;
  },

  async getSessions(): Promise<ApiSession[]> {
    const { data } = await apiClient.get<ApiSession[]>('/auth/sessions');
    return data;
  },
};

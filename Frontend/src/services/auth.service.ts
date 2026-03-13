import apiClient from '@/lib/api-client';
import type {
  ApiRegisterResponse,
  ApiCurrentUser,
  ApiPasswordChange,
  ApiUserUpdate,
  ApiConsentResponse,
  ApiConsentUpdate,
} from '@/types/api';

export const authService = {
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

  async getConsent(): Promise<ApiConsentResponse> {
    const { data } = await apiClient.get<ApiConsentResponse>('/auth/consent');
    return data;
  },

  async updateConsent(payload: ApiConsentUpdate): Promise<ApiConsentResponse> {
    const { data } = await apiClient.patch<ApiConsentResponse>('/auth/consent', payload);
    return data;
  },
};

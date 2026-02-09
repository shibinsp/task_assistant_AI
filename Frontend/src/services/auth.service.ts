import apiClient from '@/lib/api-client';
import type {
  ApiLoginResponse,
  ApiRegisterResponse,
  ApiTokenResponse,
  ApiCurrentUser,
  ApiPasswordChange,
  ApiUserUpdate,
} from '@/types/api';

export const authService = {
  async login(email: string, password: string): Promise<ApiLoginResponse> {
    const { data } = await apiClient.post<ApiLoginResponse>('/auth/login', { email, password });
    return data;
  },

  async register(
    email: string,
    password: string,
    firstName: string,
    lastName: string,
    orgName?: string
  ): Promise<ApiRegisterResponse> {
    const { data } = await apiClient.post<ApiRegisterResponse>('/auth/register', {
      email,
      password,
      first_name: firstName,
      last_name: lastName,
      org_name: orgName || undefined,
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
};

import { authService } from './auth.service';
import { notificationsService } from './notifications.service';
import type { ApiPasswordChange, ApiUserUpdate, ApiNotificationPreferencesUpdate } from '@/types/api';

export const settingsService = {
  updateProfile: (userId: string, payload: ApiUserUpdate) =>
    authService.updateProfile(userId, payload),

  changePassword: (payload: ApiPasswordChange) =>
    authService.changePassword(payload),

  getNotificationPreferences: () =>
    notificationsService.getPreferences(),

  updateNotificationPreferences: (payload: ApiNotificationPreferencesUpdate) =>
    notificationsService.updatePreferences(payload),
};

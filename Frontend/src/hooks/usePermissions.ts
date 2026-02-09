import { useAuthStore } from '@/store/authStore';

export function usePermissions() {
  const { user } = useAuthStore();
  const role = user?.role;

  return {
    isAdmin: role === 'admin',
    isManager: role === 'admin' || role === 'manager',
    isMember: role === 'admin' || role === 'manager' || role === 'member',

    // Page access
    canViewAdmin: role === 'admin',
    canViewWorkforce: role === 'admin' || role === 'manager',
    canViewPredictions: role === 'admin' || role === 'manager',
    canViewOrganization: role === 'admin',
    canViewIntegrations: role === 'admin',
    canViewTeam: role === 'admin' || role === 'manager',

    // Feature access
    canManageUsers: role === 'admin',
    canManageCheckinConfig: role === 'admin',
    canViewManagerFeed: role === 'admin' || role === 'manager',
    canApproveAgents: role === 'admin',
    canCreateSkills: role === 'admin',
    canRunSimulations: role === 'admin' || role === 'manager',
  };
}

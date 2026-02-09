import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Building2,
  Settings,
  CreditCard,
  BarChart3,
  Save,
  Loader2,
  Users,
  CheckSquare,
  HardDrive,
  Sparkles,
  CheckCircle2,
  XCircle,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
import { toast } from 'sonner';
import DashboardLayout from '@/components/layout/DashboardLayout';
import { organizationsService } from '@/services/organizations.service';
import { queryKeys } from '@/hooks/useApi';
import { getApiErrorMessage } from '@/lib/api-client';
import type {
  ApiOrganizationDetail,
  ApiOrganizationSettings,
  ApiOrganizationStats,
} from '@/types/api';

// ─── Animation variants ─────────────────────────────────────────────

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.08 },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 12 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.35 } },
};

// ─── Profile Tab ────────────────────────────────────────────────────

function ProfileSection({ org }: { org: ApiOrganizationDetail }) {
  const queryClient = useQueryClient();
  const [formData, setFormData] = useState({
    name: org.name ?? '',
    description: org.description ?? '',
  });

  useEffect(() => {
    setFormData({
      name: org.name ?? '',
      description: org.description ?? '',
    });
  }, [org]);

  const updateMutation = useMutation({
    mutationFn: () =>
      organizationsService.update(org.id, {
        name: formData.name || undefined,
        description: formData.description || undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.organizations.current });
      toast.success('Organization profile updated');
    },
    onError: (err) => toast.error(getApiErrorMessage(err)),
  });

  const hasChanges =
    formData.name !== (org.name ?? '') ||
    formData.description !== (org.description ?? '');

  return (
    <motion.div variants={containerVariants} initial="hidden" animate="visible" className="space-y-6">
      <motion.div variants={itemVariants}>
        <Card>
          <CardHeader>
            <CardTitle>Organization Profile</CardTitle>
            <CardDescription>Update your organization's public information</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="org-name">Organization Name</Label>
                <Input
                  id="org-name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="Your organization name"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="org-slug">Slug</Label>
                <Input id="org-slug" value={org.slug} disabled className="opacity-60" />
                <p className="text-xs text-muted-foreground">The slug cannot be changed</p>
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="org-description">Description</Label>
              <Textarea
                id="org-description"
                placeholder="Brief description of your organization..."
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                rows={3}
              />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Plan</Label>
                <div>
                  <Badge variant="secondary" className="capitalize">
                    {org.plan.replace('_', ' ')}
                  </Badge>
                </div>
              </div>
              <div className="space-y-2">
                <Label>Members</Label>
                <p className="text-sm text-muted-foreground">
                  {org.member_count} / {org.max_users} users
                </p>
              </div>
            </div>
            <Button
              onClick={() => updateMutation.mutate()}
              className="gap-2"
              disabled={updateMutation.isPending || !hasChanges}
            >
              {updateMutation.isPending ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Save className="w-4 h-4" />
              )}
              Save Changes
            </Button>
          </CardContent>
        </Card>
      </motion.div>
    </motion.div>
  );
}

// ─── Plan & Features Tab ────────────────────────────────────────────

function PlanFeaturesSection({ orgId }: { orgId: string }) {
  const { data: features, isLoading } = useQuery({
    queryKey: queryKeys.organizations.features(orgId),
    queryFn: () => organizationsService.getFeatures(orgId),
    enabled: !!orgId,
  });

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-48" />
            <Skeleton className="h-4 w-72 mt-1" />
          </CardHeader>
          <CardContent className="space-y-4">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!features) return null;

  const featureEntries = Object.entries(features.features);

  return (
    <motion.div variants={containerVariants} initial="hidden" animate="visible" className="space-y-6">
      {/* Current Plan */}
      <motion.div variants={itemVariants}>
        <Card>
          <CardHeader>
            <CardTitle>Current Plan</CardTitle>
            <CardDescription>Your organization's subscription details</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-4 p-4 rounded-lg bg-primary/5 border border-primary/10">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary to-primary/60 flex items-center justify-center">
                <CreditCard className="w-6 h-6 text-white" />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold capitalize">
                  {features.plan.replace('_', ' ')} Plan
                </h3>
                <p className="text-sm text-muted-foreground">
                  Up to {features.max_users} users, {features.max_agents} agents,{' '}
                  {features.max_integrations} integrations
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Feature Flags */}
      <motion.div variants={itemVariants}>
        <Card>
          <CardHeader>
            <CardTitle>Feature Flags</CardTitle>
            <CardDescription>Features available on your current plan</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {featureEntries.map(([key, enabled]) => (
                <div
                  key={key}
                  className="flex items-center justify-between p-3 rounded-lg border border-border/50 hover:bg-muted/30 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    {enabled ? (
                      <CheckCircle2 className="w-5 h-5 text-emerald-500 flex-shrink-0" />
                    ) : (
                      <XCircle className="w-5 h-5 text-muted-foreground/50 flex-shrink-0" />
                    )}
                    <span className="text-sm font-medium capitalize">
                      {key.replace(/_/g, ' ')}
                    </span>
                  </div>
                  <Badge variant={enabled ? 'default' : 'secondary'}>
                    {enabled ? 'Enabled' : 'Disabled'}
                  </Badge>
                </div>
              ))}
              {featureEntries.length === 0 && (
                <p className="text-sm text-muted-foreground text-center py-4">
                  No features configured for this plan.
                </p>
              )}
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </motion.div>
  );
}

// ─── Settings Tab ───────────────────────────────────────────────────

const settingsDefinitions = [
  {
    key: 'ai_monitoring_enabled',
    label: 'AI Monitoring',
    description: 'Enable AI-powered monitoring and analysis of task patterns',
  },
  {
    key: 'skill_tracking_enabled',
    label: 'Skill Tracking',
    description: 'Automatically track and evolve team member skill profiles',
  },
  {
    key: 'checkin_enabled',
    label: 'Require Check-Ins',
    description: 'Enable scheduled check-ins for task progress updates',
  },
  {
    key: 'automation_enabled',
    label: 'Auto Assignment',
    description: 'Allow AI agents to automatically assign and manage tasks',
  },
  {
    key: 'require_consent',
    label: 'Require User Consent',
    description: 'Require explicit user consent for AI features and data collection',
  },
] as const;

function OrgSettingsSection({ orgId }: { orgId: string }) {
  const queryClient = useQueryClient();

  const { data: settings, isLoading } = useQuery({
    queryKey: queryKeys.organizations.settings(orgId),
    queryFn: () => organizationsService.getSettings(orgId),
    enabled: !!orgId,
  });

  const updateMutation = useMutation({
    mutationFn: (payload: Partial<ApiOrganizationSettings>) =>
      organizationsService.updateSettings(orgId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.organizations.settings(orgId) });
      toast.success('Settings updated');
    },
    onError: (err) => toast.error(getApiErrorMessage(err)),
  });

  const handleToggle = (key: string, newValue: boolean) => {
    updateMutation.mutate({ [key]: newValue });
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-48" />
            <Skeleton className="h-4 w-72 mt-1" />
          </CardHeader>
          <CardContent className="space-y-4">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="flex items-center justify-between">
                <div className="space-y-1">
                  <Skeleton className="h-4 w-32" />
                  <Skeleton className="h-3 w-56" />
                </div>
                <Skeleton className="h-6 w-10 rounded-full" />
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!settings) return null;

  return (
    <motion.div variants={containerVariants} initial="hidden" animate="visible" className="space-y-6">
      <motion.div variants={itemVariants}>
        <Card>
          <CardHeader>
            <CardTitle>Organization Settings</CardTitle>
            <CardDescription>
              Configure organization-wide preferences and feature toggles
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            {settingsDefinitions.map((def) => {
              const value = settings[def.key];
              const isBoolean = typeof value === 'boolean';

              return (
                <div key={def.key} className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">{def.label}</p>
                    <p className="text-sm text-muted-foreground">{def.description}</p>
                  </div>
                  {isBoolean && (
                    <Switch
                      checked={value}
                      onCheckedChange={(checked) => handleToggle(def.key, checked)}
                      disabled={updateMutation.isPending}
                    />
                  )}
                </div>
              );
            })}
          </CardContent>
        </Card>
      </motion.div>

      {/* Default Check-In Interval */}
      {settings.default_checkin_interval_hours !== undefined && (
        <motion.div variants={itemVariants}>
          <Card>
            <CardHeader>
              <CardTitle>Check-In Interval</CardTitle>
              <CardDescription>
                Default interval (in hours) between automatic check-ins
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-4">
                <Input
                  type="number"
                  min={1}
                  max={168}
                  value={settings.default_checkin_interval_hours}
                  onChange={(e) => {
                    const hours = parseInt(e.target.value, 10);
                    if (!isNaN(hours) && hours >= 1) {
                      updateMutation.mutate({ default_checkin_interval_hours: hours });
                    }
                  }}
                  className="w-28"
                />
                <span className="text-sm text-muted-foreground">hours</span>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}
    </motion.div>
  );
}

// ─── Usage Tab ──────────────────────────────────────────────────────

const statCards = [
  {
    key: 'total_members',
    label: 'Total Users',
    icon: Users,
    color: 'text-blue-500',
    bg: 'bg-blue-500/10',
  },
  {
    key: 'active_members',
    label: 'Active Users',
    icon: Users,
    color: 'text-emerald-500',
    bg: 'bg-emerald-500/10',
  },
  {
    key: 'total_tasks',
    label: 'Total Tasks',
    icon: CheckSquare,
    color: 'text-violet-500',
    bg: 'bg-violet-500/10',
  },
  {
    key: 'completed_tasks',
    label: 'Completed Tasks',
    icon: CheckCircle2,
    color: 'text-emerald-500',
    bg: 'bg-emerald-500/10',
  },
  {
    key: 'active_agents',
    label: 'Active Agents',
    icon: Sparkles,
    color: 'text-amber-500',
    bg: 'bg-amber-500/10',
  },
  {
    key: 'integrations_connected',
    label: 'Integrations',
    icon: HardDrive,
    color: 'text-cyan-500',
    bg: 'bg-cyan-500/10',
  },
] as const;

function UsageSection({ orgId }: { orgId: string }) {
  const { data: stats, isLoading } = useQuery({
    queryKey: queryKeys.organizations.stats(orgId),
    queryFn: () => organizationsService.getStats(orgId),
    enabled: !!orgId,
  });

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <Card key={i}>
            <CardContent className="p-6">
              <div className="flex items-center gap-4">
                <Skeleton className="w-12 h-12 rounded-xl" />
                <div className="space-y-2">
                  <Skeleton className="h-7 w-16" />
                  <Skeleton className="h-3 w-24" />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (!stats) return null;

  return (
    <motion.div variants={containerVariants} initial="hidden" animate="visible" className="space-y-6">
      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {statCards.map((card) => {
          const Icon = card.icon;
          const value = stats[card.key as keyof ApiOrganizationStats];

          return (
            <motion.div key={card.key} variants={itemVariants}>
              <Card className="hover:shadow-md transition-shadow">
                <CardContent className="p-6">
                  <div className="flex items-center gap-4">
                    <div
                      className={`w-12 h-12 rounded-xl ${card.bg} flex items-center justify-center`}
                    >
                      <Icon className={`w-6 h-6 ${card.color}`} />
                    </div>
                    <div>
                      <p className="text-2xl font-bold">
                        {typeof value === 'number' ? value.toLocaleString() : '\u2014'}
                      </p>
                      <p className="text-sm text-muted-foreground">{card.label}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          );
        })}
      </div>

      {/* Roles Distribution */}
      {stats.roles_distribution && Object.keys(stats.roles_distribution).length > 0 && (
        <motion.div variants={itemVariants}>
          <Card>
            <CardHeader>
              <CardTitle>Roles Distribution</CardTitle>
              <CardDescription>Breakdown of users by role</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
                {Object.entries(stats.roles_distribution).map(([role, count]) => (
                  <div
                    key={role}
                    className="flex items-center justify-between p-3 rounded-lg border border-border/50 bg-muted/20"
                  >
                    <span className="text-sm font-medium capitalize">
                      {role.replace('_', ' ')}
                    </span>
                    <Badge variant="secondary">{count}</Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}
    </motion.div>
  );
}

// ─── Main Page ──────────────────────────────────────────────────────

export default function OrganizationSettingsPage() {
  const { data: org, isLoading: orgLoading } = useQuery({
    queryKey: queryKeys.organizations.current,
    queryFn: () => organizationsService.getCurrent(),
  });

  const orgId = org?.id ?? '';

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35 }}
        >
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
              <Building2 className="w-5 h-5 text-primary" />
            </div>
            <div>
              <h1 className="text-2xl lg:text-3xl font-bold">Organization Settings</h1>
              {orgLoading ? (
                <Skeleton className="h-4 w-48 mt-1" />
              ) : (
                <p className="text-muted-foreground mt-1">
                  Manage settings for{' '}
                  <span className="font-medium text-foreground">{org?.name}</span>
                </p>
              )}
            </div>
          </div>
        </motion.div>

        {/* Tabs */}
        <Tabs defaultValue="profile" className="space-y-6">
          <TabsList className="grid grid-cols-2 lg:grid-cols-4 w-full lg:w-auto">
            <TabsTrigger value="profile" className="gap-2">
              <Building2 className="w-4 h-4" />
              <span className="hidden sm:inline">Profile</span>
            </TabsTrigger>
            <TabsTrigger value="plan" className="gap-2">
              <CreditCard className="w-4 h-4" />
              <span className="hidden sm:inline">Plan & Features</span>
            </TabsTrigger>
            <TabsTrigger value="settings" className="gap-2">
              <Settings className="w-4 h-4" />
              <span className="hidden sm:inline">Settings</span>
            </TabsTrigger>
            <TabsTrigger value="usage" className="gap-2">
              <BarChart3 className="w-4 h-4" />
              <span className="hidden sm:inline">Usage</span>
            </TabsTrigger>
          </TabsList>

          <TabsContent value="profile">
            {orgLoading ? (
              <div className="space-y-6">
                <Card>
                  <CardHeader>
                    <Skeleton className="h-6 w-48" />
                    <Skeleton className="h-4 w-72 mt-1" />
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <Skeleton className="h-10 w-full" />
                      <Skeleton className="h-10 w-full" />
                    </div>
                    <Skeleton className="h-20 w-full" />
                    <Skeleton className="h-10 w-32" />
                  </CardContent>
                </Card>
              </div>
            ) : org ? (
              <ProfileSection org={org} />
            ) : null}
          </TabsContent>

          <TabsContent value="plan">
            {orgId ? (
              <PlanFeaturesSection orgId={orgId} />
            ) : (
              <Card>
                <CardContent className="p-6">
                  <Skeleton className="h-6 w-full" />
                </CardContent>
              </Card>
            )}
          </TabsContent>

          <TabsContent value="settings">
            {orgId ? (
              <OrgSettingsSection orgId={orgId} />
            ) : (
              <Card>
                <CardContent className="p-6">
                  <Skeleton className="h-6 w-full" />
                </CardContent>
              </Card>
            )}
          </TabsContent>

          <TabsContent value="usage">
            {orgId ? (
              <UsageSection orgId={orgId} />
            ) : (
              <Card>
                <CardContent className="p-6">
                  <Skeleton className="h-6 w-full" />
                </CardContent>
              </Card>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </DashboardLayout>
  );
}

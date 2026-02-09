import { useState } from 'react';
import { motion } from 'framer-motion';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  MessageCircle,
  Clock,
  CheckCircle2,
  AlertTriangle,
  SkipForward,
  Send,
  Settings2,
  Plus,
  Pencil,
  Trash2,
  Filter,
  RefreshCw,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Skeleton } from '@/components/ui/skeleton';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import DashboardLayout from '@/components/layout/DashboardLayout';
import { checkinsService } from '@/services/checkins.service';
import { queryKeys } from '@/hooks/useApi';
import { usePermissions } from '@/hooks/usePermissions';
import { getApiErrorMessage } from '@/lib/api-client';
import { toast } from 'sonner';
import type {
  ApiCheckIn,
  ApiCheckInConfig,
  ApiCheckInConfigCreate,
  ApiCheckInSubmit,
  ApiCheckInSkip,
  ApiCheckInStatistics,
  ApiCheckInFeedItem,
} from '@/types/api';

// ─── Stat Card Item ─────────────────────────────────────────────────

interface StatCardItem {
  title: string;
  value: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
  subtitle?: string;
}

function buildStatCards(stats: ApiCheckInStatistics | undefined): StatCardItem[] {
  return [
    {
      title: 'Total Check-Ins',
      value: stats?.total_checkins?.toLocaleString() ?? '0',
      icon: MessageCircle,
      color: 'from-blue-500 to-cyan-500',
      subtitle: `${stats?.responded ?? 0} responded`,
    },
    {
      title: 'Response Rate',
      value: stats ? `${Math.round(stats.response_rate)}%` : '0%',
      icon: CheckCircle2,
      color: 'from-emerald-500 to-teal-500',
      subtitle: `${stats?.skipped ?? 0} skipped`,
    },
    {
      title: 'Avg Response Time',
      value: stats?.avg_response_time_minutes
        ? `${Math.round(stats.avg_response_time_minutes)} min`
        : 'N/A',
      icon: Clock,
      color: 'from-violet-500 to-purple-500',
      subtitle: `${stats?.expired ?? 0} expired`,
    },
    {
      title: 'Escalations',
      value: stats?.escalated?.toLocaleString() ?? '0',
      icon: AlertTriangle,
      color: 'from-amber-500 to-orange-500',
      subtitle: `${stats?.friction_detected_count ?? 0} friction detected`,
    },
  ];
}

// ─── Status badge helper ────────────────────────────────────────────

function statusVariant(status: string): 'default' | 'secondary' | 'destructive' | 'outline' {
  switch (status) {
    case 'responded':
      return 'default';
    case 'pending':
      return 'secondary';
    case 'escalated':
      return 'destructive';
    default:
      return 'outline';
  }
}

// ─── Main Page ──────────────────────────────────────────────────────

export default function CheckInsPage() {
  const queryClient = useQueryClient();
  const { canViewManagerFeed, canManageCheckinConfig } = usePermissions();

  const [activeTab, setActiveTab] = useState('my-checkins');
  const [feedFilter, setFeedFilter] = useState<'all' | 'attention'>('all');

  // ─── Respond / Skip state ────────────────────────────────────────
  const [respondingId, setRespondingId] = useState<string | null>(null);
  const [respondForm, setRespondForm] = useState<ApiCheckInSubmit>({
    progress_indicator: '',
    progress_notes: '',
    blockers_reported: '',
  });
  const [skipDialogId, setSkipDialogId] = useState<string | null>(null);
  const [skipReason, setSkipReason] = useState('');

  // ─── Config dialog state ─────────────────────────────────────────
  const [configDialogOpen, setConfigDialogOpen] = useState(false);
  const [editingConfig, setEditingConfig] = useState<ApiCheckInConfig | null>(null);
  const [configForm, setConfigForm] = useState<ApiCheckInConfigCreate>({
    interval_hours: 24,
    enabled: true,
    max_daily_checkins: 3,
    work_start_hour: 9,
    work_end_hour: 17,
    auto_escalate_after_missed: 3,
    escalate_to_manager: true,
    ai_suggestions_enabled: true,
    ai_sentiment_analysis: true,
  });
  const [deleteDialogId, setDeleteDialogId] = useState<string | null>(null);

  // ─── Queries ─────────────────────────────────────────────────────
  const { data: statistics, isLoading: statsLoading } = useQuery({
    queryKey: queryKeys.checkins.statistics(),
    queryFn: () => checkinsService.getStatistics(),
  });

  const { data: pendingCheckins, isLoading: pendingLoading } = useQuery({
    queryKey: queryKeys.checkins.pending,
    queryFn: () => checkinsService.getPending(),
  });

  const { data: recentData, isLoading: recentLoading } = useQuery({
    queryKey: queryKeys.checkins.list({ status: 'responded', limit: 10 }),
    queryFn: () => checkinsService.list({ status: 'responded', limit: 10 }),
  });

  const { data: feedData, isLoading: feedLoading } = useQuery({
    queryKey: queryKeys.checkins.feed({ needs_attention: feedFilter === 'attention' || undefined }),
    queryFn: () =>
      checkinsService.getManagerFeed({
        needs_attention: feedFilter === 'attention' ? true : undefined,
      }),
    enabled: canViewManagerFeed,
  });

  const { data: configs, isLoading: configsLoading } = useQuery({
    queryKey: queryKeys.checkins.configs,
    queryFn: () => checkinsService.getConfigs(),
    enabled: canManageCheckinConfig,
  });

  // ─── Mutations ───────────────────────────────────────────────────

  const respondMutation = useMutation({
    mutationFn: ({ checkinId, payload }: { checkinId: string; payload: ApiCheckInSubmit }) =>
      checkinsService.respond(checkinId, payload),
    onSuccess: () => {
      toast.success('Check-in response submitted');
      setRespondingId(null);
      setRespondForm({ progress_indicator: '', progress_notes: '', blockers_reported: '' });
      queryClient.invalidateQueries({ queryKey: queryKeys.checkins.pending });
      queryClient.invalidateQueries({ queryKey: queryKeys.checkins.list({ status: 'responded', limit: 10 }) });
      queryClient.invalidateQueries({ queryKey: queryKeys.checkins.statistics() });
    },
    onError: (error) => {
      toast.error(getApiErrorMessage(error));
    },
  });

  const skipMutation = useMutation({
    mutationFn: ({ checkinId, payload }: { checkinId: string; payload: ApiCheckInSkip }) =>
      checkinsService.skip(checkinId, payload),
    onSuccess: () => {
      toast.success('Check-in skipped');
      setSkipDialogId(null);
      setSkipReason('');
      queryClient.invalidateQueries({ queryKey: queryKeys.checkins.pending });
      queryClient.invalidateQueries({ queryKey: queryKeys.checkins.statistics() });
    },
    onError: (error) => {
      toast.error(getApiErrorMessage(error));
    },
  });

  const createConfigMutation = useMutation({
    mutationFn: (payload: ApiCheckInConfigCreate) => checkinsService.createConfig(payload),
    onSuccess: () => {
      toast.success('Configuration created');
      setConfigDialogOpen(false);
      resetConfigForm();
      queryClient.invalidateQueries({ queryKey: queryKeys.checkins.configs });
    },
    onError: (error) => {
      toast.error(getApiErrorMessage(error));
    },
  });

  const updateConfigMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: ApiCheckInConfigCreate }) =>
      checkinsService.updateConfig(id, payload),
    onSuccess: () => {
      toast.success('Configuration updated');
      setConfigDialogOpen(false);
      setEditingConfig(null);
      resetConfigForm();
      queryClient.invalidateQueries({ queryKey: queryKeys.checkins.configs });
    },
    onError: (error) => {
      toast.error(getApiErrorMessage(error));
    },
  });

  const deleteConfigMutation = useMutation({
    mutationFn: (id: string) => checkinsService.deleteConfig(id),
    onSuccess: () => {
      toast.success('Configuration deleted');
      setDeleteDialogId(null);
      queryClient.invalidateQueries({ queryKey: queryKeys.checkins.configs });
    },
    onError: (error) => {
      toast.error(getApiErrorMessage(error));
    },
  });

  // ─── Helpers ─────────────────────────────────────────────────────

  function resetConfigForm() {
    setConfigForm({
      interval_hours: 24,
      enabled: true,
      max_daily_checkins: 3,
      work_start_hour: 9,
      work_end_hour: 17,
      auto_escalate_after_missed: 3,
      escalate_to_manager: true,
      ai_suggestions_enabled: true,
      ai_sentiment_analysis: true,
    });
  }

  function openEditConfig(config: ApiCheckInConfig) {
    setEditingConfig(config);
    setConfigForm({
      interval_hours: config.interval_hours,
      enabled: config.enabled,
      max_daily_checkins: config.max_daily_checkins,
      work_start_hour: config.work_start_hour,
      work_end_hour: config.work_end_hour,
      auto_escalate_after_missed: config.auto_escalate_after_missed,
      escalate_to_manager: config.escalate_to_manager,
      ai_suggestions_enabled: config.ai_suggestions_enabled,
      ai_sentiment_analysis: config.ai_sentiment_analysis,
    });
    setConfigDialogOpen(true);
  }

  function handleSaveConfig() {
    if (editingConfig) {
      updateConfigMutation.mutate({ id: editingConfig.id, payload: configForm });
    } else {
      createConfigMutation.mutate(configForm);
    }
  }

  function handleRespond(checkinId: string) {
    if (!respondForm.progress_indicator.trim()) {
      toast.error('Please provide a progress indicator');
      return;
    }
    respondMutation.mutate({ checkinId, payload: respondForm });
  }

  function handleSkip(checkinId: string) {
    skipMutation.mutate({ checkinId, payload: { reason: skipReason || undefined } });
  }

  const statCards = buildStatCards(statistics);
  const recentCheckins = recentData?.checkins ?? [];
  const feedItems: ApiCheckInFeedItem[] = feedData?.items ?? [];

  // ─── Determine available tabs ────────────────────────────────────

  const availableTabs = [
    { value: 'my-checkins', label: 'My Check-Ins' },
    ...(canViewManagerFeed ? [{ value: 'manager-feed', label: 'Manager Feed' }] : []),
    ...(canManageCheckinConfig ? [{ value: 'configuration', label: 'Configuration' }] : []),
  ];

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <h1 className="text-2xl lg:text-3xl font-bold">Check-Ins</h1>
            <p className="text-muted-foreground mt-1">
              Track progress updates and stay aligned with your team
            </p>
          </div>
          <Button
            variant="outline"
            size="sm"
            className="gap-2 w-fit"
            onClick={() => {
              queryClient.invalidateQueries({ queryKey: queryKeys.checkins.pending });
              queryClient.invalidateQueries({ queryKey: queryKeys.checkins.statistics() });
            }}
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </Button>
        </div>

        {/* Stats Row */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {statsLoading
            ? Array.from({ length: 4 }).map((_, i) => (
                <Card key={i}>
                  <CardContent className="p-4 lg:p-6">
                    <Skeleton className="h-10 w-10 rounded-xl mb-4" />
                    <Skeleton className="h-8 w-20 mb-1" />
                    <Skeleton className="h-4 w-28" />
                  </CardContent>
                </Card>
              ))
            : statCards.map((card, index) => {
                const Icon = card.icon;
                return (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                  >
                    <Card className="hover-lift">
                      <CardContent className="p-4 lg:p-6">
                        <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${card.color} flex items-center justify-center`}>
                          <Icon className="w-5 h-5 text-white" />
                        </div>
                        <div className="mt-4">
                          <p className="text-2xl lg:text-3xl font-bold">{card.value}</p>
                          <p className="text-sm text-muted-foreground">{card.title}</p>
                          {card.subtitle && (
                            <p className="text-xs text-muted-foreground mt-0.5">{card.subtitle}</p>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  </motion.div>
                );
              })}
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList>
            {availableTabs.map((tab) => (
              <TabsTrigger key={tab.value} value={tab.value}>
                {tab.label}
              </TabsTrigger>
            ))}
          </TabsList>

          {/* ─── My Check-Ins Tab ──────────────────────────────────── */}
          <TabsContent value="my-checkins" className="space-y-6">
            {/* Pending Check-Ins */}
            <div>
              <h2 className="text-lg font-semibold mb-3">Pending Check-Ins</h2>
              {pendingLoading ? (
                <div className="space-y-3">
                  {Array.from({ length: 2 }).map((_, i) => (
                    <Card key={i}>
                      <CardContent className="p-4">
                        <Skeleton className="h-5 w-48 mb-2" />
                        <Skeleton className="h-4 w-32" />
                      </CardContent>
                    </Card>
                  ))}
                </div>
              ) : !pendingCheckins || pendingCheckins.length === 0 ? (
                <Card>
                  <CardContent className="p-8 text-center">
                    <CheckCircle2 className="w-10 h-10 text-emerald-500 mx-auto mb-3" />
                    <p className="text-muted-foreground">No pending check-ins. You're all caught up!</p>
                  </CardContent>
                </Card>
              ) : (
                <div className="space-y-3">
                  {pendingCheckins.map((checkin: ApiCheckIn) => (
                    <motion.div
                      key={checkin.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                    >
                      <Card>
                        <CardContent className="p-4">
                          <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-3">
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-1">
                                <h3 className="font-medium">
                                  {checkin.task_title ?? `Task ${checkin.task_id.slice(0, 8)}`}
                                </h3>
                                <Badge variant={statusVariant(checkin.status)}>
                                  {checkin.status}
                                </Badge>
                                <Badge variant="outline">Cycle {checkin.cycle_number}</Badge>
                              </div>
                              <p className="text-sm text-muted-foreground">
                                Scheduled: {new Date(checkin.scheduled_at).toLocaleString()}
                              </p>
                              {checkin.ai_suggestion && (
                                <p className="text-sm text-blue-600 dark:text-blue-400 mt-1">
                                  AI Suggestion: {checkin.ai_suggestion}
                                </p>
                              )}
                            </div>

                            {respondingId !== checkin.id && (
                              <div className="flex gap-2 shrink-0">
                                <Button
                                  size="sm"
                                  className="gap-1"
                                  onClick={() => setRespondingId(checkin.id)}
                                >
                                  <Send className="w-3.5 h-3.5" />
                                  Respond
                                </Button>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  className="gap-1"
                                  onClick={() => setSkipDialogId(checkin.id)}
                                >
                                  <SkipForward className="w-3.5 h-3.5" />
                                  Skip
                                </Button>
                              </div>
                            )}
                          </div>

                          {/* Respond Form */}
                          {respondingId === checkin.id && (
                            <motion.div
                              initial={{ opacity: 0, height: 0 }}
                              animate={{ opacity: 1, height: 'auto' }}
                              className="mt-4 space-y-3 border-t pt-4"
                            >
                              <div className="space-y-2">
                                <Label>Progress Indicator *</Label>
                                <Select
                                  value={respondForm.progress_indicator}
                                  onValueChange={(val) =>
                                    setRespondForm((f) => ({ ...f, progress_indicator: val }))
                                  }
                                >
                                  <SelectTrigger className="w-full">
                                    <SelectValue placeholder="Select progress status" />
                                  </SelectTrigger>
                                  <SelectContent>
                                    <SelectItem value="on_track">On Track</SelectItem>
                                    <SelectItem value="at_risk">At Risk</SelectItem>
                                    <SelectItem value="blocked">Blocked</SelectItem>
                                    <SelectItem value="completed">Completed</SelectItem>
                                  </SelectContent>
                                </Select>
                              </div>
                              <div className="space-y-2">
                                <Label>Progress Notes</Label>
                                <Textarea
                                  placeholder="Share an update on your progress..."
                                  value={respondForm.progress_notes ?? ''}
                                  onChange={(e) =>
                                    setRespondForm((f) => ({ ...f, progress_notes: e.target.value }))
                                  }
                                  rows={3}
                                />
                              </div>
                              <div className="space-y-2">
                                <Label>Completed Since Last Check-In</Label>
                                <Textarea
                                  placeholder="What have you completed?"
                                  value={respondForm.completed_since_last ?? ''}
                                  onChange={(e) =>
                                    setRespondForm((f) => ({
                                      ...f,
                                      completed_since_last: e.target.value,
                                    }))
                                  }
                                  rows={2}
                                />
                              </div>
                              <div className="space-y-2">
                                <Label>Blockers</Label>
                                <Textarea
                                  placeholder="Any blockers or challenges?"
                                  value={respondForm.blockers_reported ?? ''}
                                  onChange={(e) =>
                                    setRespondForm((f) => ({
                                      ...f,
                                      blockers_reported: e.target.value,
                                    }))
                                  }
                                  rows={2}
                                />
                              </div>
                              <div className="flex gap-2 justify-end">
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => {
                                    setRespondingId(null);
                                    setRespondForm({
                                      progress_indicator: '',
                                      progress_notes: '',
                                      blockers_reported: '',
                                    });
                                  }}
                                >
                                  Cancel
                                </Button>
                                <Button
                                  size="sm"
                                  className="gap-1"
                                  disabled={respondMutation.isPending}
                                  onClick={() => handleRespond(checkin.id)}
                                >
                                  {respondMutation.isPending ? (
                                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                                  ) : (
                                    <Send className="w-3.5 h-3.5" />
                                  )}
                                  Submit Response
                                </Button>
                              </div>
                            </motion.div>
                          )}
                        </CardContent>
                      </Card>
                    </motion.div>
                  ))}
                </div>
              )}
            </div>

            {/* Recent Check-Ins */}
            <div>
              <h2 className="text-lg font-semibold mb-3">Recent Check-Ins</h2>
              {recentLoading ? (
                <div className="space-y-2">
                  {Array.from({ length: 3 }).map((_, i) => (
                    <Card key={i}>
                      <CardContent className="p-4">
                        <Skeleton className="h-4 w-40 mb-2" />
                        <Skeleton className="h-3 w-60" />
                      </CardContent>
                    </Card>
                  ))}
                </div>
              ) : recentCheckins.length === 0 ? (
                <Card>
                  <CardContent className="p-8 text-center">
                    <p className="text-muted-foreground">No recent check-ins found.</p>
                  </CardContent>
                </Card>
              ) : (
                <div className="space-y-2">
                  {recentCheckins.map((checkin: ApiCheckIn) => (
                    <Card key={checkin.id}>
                      <CardContent className="p-4">
                        <div className="flex items-center justify-between">
                          <div>
                            <div className="flex items-center gap-2 mb-1">
                              <h3 className="font-medium text-sm">
                                {checkin.task_title ?? `Task ${checkin.task_id.slice(0, 8)}`}
                              </h3>
                              <Badge variant={statusVariant(checkin.status)} className="text-xs">
                                {checkin.status}
                              </Badge>
                              {checkin.progress_indicator && (
                                <Badge variant="outline" className="text-xs">
                                  {checkin.progress_indicator.replace(/_/g, ' ')}
                                </Badge>
                              )}
                            </div>
                            {checkin.progress_notes && (
                              <p className="text-sm text-muted-foreground line-clamp-2">
                                {checkin.progress_notes}
                              </p>
                            )}
                            <p className="text-xs text-muted-foreground mt-1">
                              Responded: {checkin.responded_at ? new Date(checkin.responded_at).toLocaleString() : 'N/A'}
                            </p>
                          </div>
                          {checkin.friction_detected && (
                            <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0" />
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </div>
          </TabsContent>

          {/* ─── Manager Feed Tab ──────────────────────────────────── */}
          {canViewManagerFeed && (
            <TabsContent value="manager-feed" className="space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold">Team Check-In Feed</h2>
                <div className="flex items-center gap-2">
                  <Filter className="w-4 h-4 text-muted-foreground" />
                  <Select
                    value={feedFilter}
                    onValueChange={(val) => setFeedFilter(val as 'all' | 'attention')}
                  >
                    <SelectTrigger className="w-[160px]">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Check-Ins</SelectItem>
                      <SelectItem value="attention">Needs Attention</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {feedData?.needs_attention_count != null && feedData.needs_attention_count > 0 && (
                <Card className="border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-950/20">
                  <CardContent className="p-4 flex items-center gap-3">
                    <AlertTriangle className="w-5 h-5 text-amber-600" />
                    <p className="text-sm font-medium text-amber-800 dark:text-amber-200">
                      {feedData.needs_attention_count} check-in{feedData.needs_attention_count > 1 ? 's' : ''} need
                      your attention
                    </p>
                  </CardContent>
                </Card>
              )}

              {feedLoading ? (
                <div className="space-y-3">
                  {Array.from({ length: 3 }).map((_, i) => (
                    <Card key={i}>
                      <CardContent className="p-4">
                        <Skeleton className="h-5 w-48 mb-2" />
                        <Skeleton className="h-4 w-64" />
                      </CardContent>
                    </Card>
                  ))}
                </div>
              ) : feedItems.length === 0 ? (
                <Card>
                  <CardContent className="p-8 text-center">
                    <p className="text-muted-foreground">No check-ins in the feed.</p>
                  </CardContent>
                </Card>
              ) : (
                <div className="space-y-3">
                  {feedItems.map((item: ApiCheckInFeedItem) => (
                    <Card
                      key={item.checkin.id}
                      className={
                        item.needs_attention
                          ? 'border-amber-200 dark:border-amber-800'
                          : ''
                      }
                    >
                      <CardContent className="p-4">
                        <div className="flex items-start justify-between gap-3">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1 flex-wrap">
                              <h3 className="font-medium text-sm">
                                {item.checkin.user_name ?? 'Team Member'}
                              </h3>
                              <span className="text-muted-foreground text-sm">--</span>
                              <span className="text-sm">
                                {item.checkin.task_title ?? `Task ${item.checkin.task_id.slice(0, 8)}`}
                              </span>
                              <Badge variant={statusVariant(item.checkin.status)} className="text-xs">
                                {item.checkin.status}
                              </Badge>
                              {item.needs_attention && (
                                <Badge variant="destructive" className="text-xs">
                                  Needs Attention
                                </Badge>
                              )}
                            </div>
                            {item.checkin.progress_notes && (
                              <p className="text-sm text-muted-foreground mt-1">
                                {item.checkin.progress_notes}
                              </p>
                            )}
                            {item.checkin.blockers_reported && (
                              <p className="text-sm text-red-600 dark:text-red-400 mt-1">
                                Blocker: {item.checkin.blockers_reported}
                              </p>
                            )}
                            {item.attention_reason && (
                              <p className="text-xs text-amber-600 dark:text-amber-400 mt-1">
                                {item.attention_reason}
                              </p>
                            )}
                            <p className="text-xs text-muted-foreground mt-1">
                              {item.checkin.responded_at
                                ? new Date(item.checkin.responded_at).toLocaleString()
                                : new Date(item.checkin.scheduled_at).toLocaleString()}
                            </p>
                          </div>
                          {item.checkin.sentiment_score != null && (
                            <div className="text-right shrink-0">
                              <p className="text-xs text-muted-foreground">Sentiment</p>
                              <p
                                className={`text-sm font-medium ${
                                  item.checkin.sentiment_score >= 0.6
                                    ? 'text-emerald-600'
                                    : item.checkin.sentiment_score >= 0.3
                                      ? 'text-amber-600'
                                      : 'text-red-600'
                                }`}
                              >
                                {Math.round(item.checkin.sentiment_score * 100)}%
                              </p>
                            </div>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </TabsContent>
          )}

          {/* ─── Configuration Tab ─────────────────────────────────── */}
          {canManageCheckinConfig && (
            <TabsContent value="configuration" className="space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold">Check-In Configurations</h2>
                <Button
                  size="sm"
                  className="gap-1"
                  onClick={() => {
                    setEditingConfig(null);
                    resetConfigForm();
                    setConfigDialogOpen(true);
                  }}
                >
                  <Plus className="w-4 h-4" />
                  New Config
                </Button>
              </div>

              {configsLoading ? (
                <div className="space-y-3">
                  {Array.from({ length: 2 }).map((_, i) => (
                    <Card key={i}>
                      <CardContent className="p-4">
                        <Skeleton className="h-5 w-32 mb-2" />
                        <Skeleton className="h-4 w-48" />
                      </CardContent>
                    </Card>
                  ))}
                </div>
              ) : !configs || configs.length === 0 ? (
                <Card>
                  <CardContent className="p-8 text-center">
                    <Settings2 className="w-10 h-10 text-muted-foreground mx-auto mb-3" />
                    <p className="text-muted-foreground">
                      No configurations yet. Create one to start scheduling check-ins.
                    </p>
                  </CardContent>
                </Card>
              ) : (
                <div className="space-y-3">
                  {configs.map((config: ApiCheckInConfig) => (
                    <Card key={config.id}>
                      <CardContent className="p-4">
                        <div className="flex items-start justify-between gap-3">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              <Badge variant={config.enabled ? 'default' : 'secondary'}>
                                {config.enabled ? 'Active' : 'Disabled'}
                              </Badge>
                              {config.ai_suggestions_enabled && (
                                <Badge variant="outline" className="text-xs">AI Suggestions</Badge>
                              )}
                              {config.escalate_to_manager && (
                                <Badge variant="outline" className="text-xs">Auto-Escalate</Badge>
                              )}
                            </div>
                            <div className="grid grid-cols-2 lg:grid-cols-4 gap-x-6 gap-y-1 text-sm">
                              <div>
                                <span className="text-muted-foreground">Interval:</span>{' '}
                                <span className="font-medium">{config.interval_hours}h</span>
                              </div>
                              <div>
                                <span className="text-muted-foreground">Max Daily:</span>{' '}
                                <span className="font-medium">{config.max_daily_checkins}</span>
                              </div>
                              <div>
                                <span className="text-muted-foreground">Work Hours:</span>{' '}
                                <span className="font-medium">
                                  {config.work_start_hour}:00 - {config.work_end_hour}:00
                                </span>
                              </div>
                              <div>
                                <span className="text-muted-foreground">Escalate After:</span>{' '}
                                <span className="font-medium">{config.auto_escalate_after_missed} missed</span>
                              </div>
                            </div>
                            <p className="text-xs text-muted-foreground mt-2">
                              Created: {new Date(config.created_at).toLocaleDateString()}
                            </p>
                          </div>
                          <div className="flex gap-1 shrink-0">
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => openEditConfig(config)}
                            >
                              <Pencil className="w-4 h-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => setDeleteDialogId(config.id)}
                            >
                              <Trash2 className="w-4 h-4 text-destructive" />
                            </Button>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </TabsContent>
          )}
        </Tabs>

        {/* ─── Skip Dialog ──────────────────────────────────────────── */}
        <Dialog open={skipDialogId !== null} onOpenChange={(open) => { if (!open) { setSkipDialogId(null); setSkipReason(''); } }}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Skip Check-In</DialogTitle>
              <DialogDescription>
                Provide an optional reason for skipping this check-in.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-2">
              <Label>Reason (optional)</Label>
              <Textarea
                placeholder="Why are you skipping this check-in?"
                value={skipReason}
                onChange={(e) => setSkipReason(e.target.value)}
                rows={3}
              />
            </div>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => {
                  setSkipDialogId(null);
                  setSkipReason('');
                }}
              >
                Cancel
              </Button>
              <Button
                disabled={skipMutation.isPending}
                onClick={() => {
                  if (skipDialogId) handleSkip(skipDialogId);
                }}
              >
                {skipMutation.isPending ? 'Skipping...' : 'Skip Check-In'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* ─── Config Create/Edit Dialog ────────────────────────────── */}
        <Dialog
          open={configDialogOpen}
          onOpenChange={(open) => {
            if (!open) {
              setConfigDialogOpen(false);
              setEditingConfig(null);
              resetConfigForm();
            }
          }}
        >
          <DialogContent className="max-w-lg max-h-[85vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>{editingConfig ? 'Edit Configuration' : 'New Configuration'}</DialogTitle>
              <DialogDescription>
                {editingConfig
                  ? 'Update the check-in configuration settings.'
                  : 'Create a new check-in schedule configuration.'}
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Interval (hours)</Label>
                  <Input
                    type="number"
                    min={1}
                    value={configForm.interval_hours ?? 24}
                    onChange={(e) =>
                      setConfigForm((f) => ({ ...f, interval_hours: parseInt(e.target.value) || 24 }))
                    }
                  />
                </div>
                <div className="space-y-2">
                  <Label>Max Daily Check-Ins</Label>
                  <Input
                    type="number"
                    min={1}
                    max={10}
                    value={configForm.max_daily_checkins ?? 3}
                    onChange={(e) =>
                      setConfigForm((f) => ({ ...f, max_daily_checkins: parseInt(e.target.value) || 3 }))
                    }
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Work Start Hour</Label>
                  <Input
                    type="number"
                    min={0}
                    max={23}
                    value={configForm.work_start_hour ?? 9}
                    onChange={(e) =>
                      setConfigForm((f) => ({ ...f, work_start_hour: parseInt(e.target.value) || 9 }))
                    }
                  />
                </div>
                <div className="space-y-2">
                  <Label>Work End Hour</Label>
                  <Input
                    type="number"
                    min={0}
                    max={23}
                    value={configForm.work_end_hour ?? 17}
                    onChange={(e) =>
                      setConfigForm((f) => ({ ...f, work_end_hour: parseInt(e.target.value) || 17 }))
                    }
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label>Auto-Escalate After Missed</Label>
                <Input
                  type="number"
                  min={1}
                  max={10}
                  value={configForm.auto_escalate_after_missed ?? 3}
                  onChange={(e) =>
                    setConfigForm((f) => ({
                      ...f,
                      auto_escalate_after_missed: parseInt(e.target.value) || 3,
                    }))
                  }
                />
              </div>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <Label>Enabled</Label>
                  <Switch
                    checked={configForm.enabled ?? true}
                    onCheckedChange={(checked) =>
                      setConfigForm((f) => ({ ...f, enabled: checked }))
                    }
                  />
                </div>
                <div className="flex items-center justify-between">
                  <Label>Escalate to Manager</Label>
                  <Switch
                    checked={configForm.escalate_to_manager ?? true}
                    onCheckedChange={(checked) =>
                      setConfigForm((f) => ({ ...f, escalate_to_manager: checked }))
                    }
                  />
                </div>
                <div className="flex items-center justify-between">
                  <Label>AI Suggestions</Label>
                  <Switch
                    checked={configForm.ai_suggestions_enabled ?? true}
                    onCheckedChange={(checked) =>
                      setConfigForm((f) => ({ ...f, ai_suggestions_enabled: checked }))
                    }
                  />
                </div>
                <div className="flex items-center justify-between">
                  <Label>AI Sentiment Analysis</Label>
                  <Switch
                    checked={configForm.ai_sentiment_analysis ?? true}
                    onCheckedChange={(checked) =>
                      setConfigForm((f) => ({ ...f, ai_sentiment_analysis: checked }))
                    }
                  />
                </div>
              </div>
            </div>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => {
                  setConfigDialogOpen(false);
                  setEditingConfig(null);
                  resetConfigForm();
                }}
              >
                Cancel
              </Button>
              <Button
                disabled={createConfigMutation.isPending || updateConfigMutation.isPending}
                onClick={handleSaveConfig}
              >
                {createConfigMutation.isPending || updateConfigMutation.isPending
                  ? 'Saving...'
                  : editingConfig
                    ? 'Update'
                    : 'Create'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* ─── Delete Confirmation Dialog ───────────────────────────── */}
        <Dialog open={deleteDialogId !== null} onOpenChange={(open) => { if (!open) setDeleteDialogId(null); }}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Delete Configuration</DialogTitle>
              <DialogDescription>
                Are you sure you want to delete this configuration? This action cannot be undone.
              </DialogDescription>
            </DialogHeader>
            <DialogFooter>
              <Button variant="outline" onClick={() => setDeleteDialogId(null)}>
                Cancel
              </Button>
              <Button
                variant="destructive"
                disabled={deleteConfigMutation.isPending}
                onClick={() => {
                  if (deleteDialogId) deleteConfigMutation.mutate(deleteDialogId);
                }}
              >
                {deleteConfigMutation.isPending ? 'Deleting...' : 'Delete'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </DashboardLayout>
  );
}

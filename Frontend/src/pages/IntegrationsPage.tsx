import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Plug,
  Github,
  MessageSquare,
  LayoutGrid,
  Calendar,
  Minus,
  RefreshCw,
  Link2,
  Unlink,
  Plus,
  Webhook,
  Send,
  Pencil,
  Trash2,
  ChevronDown,
  ChevronRight,
  RotateCcw,
  Eye,
  EyeOff,
  Copy,
  Loader2,
} from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Skeleton } from '@/components/ui/skeleton';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import DashboardLayout from '@/components/layout/DashboardLayout';
import { integrationsService } from '@/services/integrations.service';
import { queryKeys } from '@/hooks/useApi';
import type {
  ApiIntegration,
  ApiIntegrationType,
  ApiWebhook,
  ApiWebhookCreate,
  ApiWebhookUpdate,
} from '@/types/api';

// ─── Constants ──────────────────────────────────────────────────────────

const AVAILABLE_PROVIDERS: Array<{
  type: ApiIntegrationType;
  name: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
  bgColor: string;
}> = [
  { type: 'github', name: 'GitHub', icon: Github, color: 'text-gray-900 dark:text-white', bgColor: 'bg-gray-100 dark:bg-gray-800' },
  { type: 'slack', name: 'Slack', icon: MessageSquare, color: 'text-purple-600', bgColor: 'bg-purple-50 dark:bg-purple-950' },
  { type: 'jira', name: 'Jira', icon: LayoutGrid, color: 'text-blue-600', bgColor: 'bg-blue-50 dark:bg-blue-950' },
  { type: 'confluence', name: 'Google Calendar', icon: Calendar, color: 'text-emerald-600', bgColor: 'bg-emerald-50 dark:bg-emerald-950' },
  { type: 'notion', name: 'Linear', icon: Minus, color: 'text-indigo-600', bgColor: 'bg-indigo-50 dark:bg-indigo-950' },
];

const WEBHOOK_EVENTS = [
  'task.created',
  'task.updated',
  'task.completed',
  'task.deleted',
  'task.assigned',
  'task.status_changed',
  'checkin.submitted',
  'checkin.skipped',
  'checkin.escalated',
  'team.member_added',
  'team.member_removed',
  'automation.triggered',
  'automation.completed',
];

// ─── Helpers ────────────────────────────────────────────────────────────

function formatDate(dateStr?: string | null): string {
  if (!dateStr) return 'Never';
  const d = new Date(dateStr);
  return d.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function maskUrl(url: string): string {
  try {
    const parsed = new URL(url);
    const host = parsed.hostname;
    const path = parsed.pathname;
    const maskedPath = path.length > 10
      ? path.substring(0, 8) + '...' + path.substring(path.length - 4)
      : path;
    return `${parsed.protocol}//${host}${maskedPath}`;
  } catch {
    return url.length > 40 ? url.substring(0, 37) + '...' : url;
  }
}

// ─── Integration Tile ───────────────────────────────────────────────────

function IntegrationTile({
  provider,
  integration,
  onConnect,
  onSync,
  onDisconnect,
  isSyncing,
  isConnecting,
}: {
  provider: typeof AVAILABLE_PROVIDERS[number];
  integration?: ApiIntegration;
  onConnect: () => void;
  onSync: () => void;
  onDisconnect: () => void;
  isSyncing: boolean;
  isConnecting: boolean;
}) {
  const [showDisconnectConfirm, setShowDisconnectConfirm] = useState(false);
  const isConnected = !!integration?.is_active;
  const Icon = provider.icon;

  return (
    <>
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <Card className="hover:shadow-md transition-shadow h-full">
          <CardContent className="p-5">
            <div className="flex items-start justify-between mb-4">
              <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${provider.bgColor}`}>
                <Icon className={`w-6 h-6 ${provider.color}`} />
              </div>
              <Badge
                variant={isConnected ? 'default' : 'outline'}
                className={isConnected
                  ? 'bg-emerald-500/10 text-emerald-600 border-emerald-500/20 hover:bg-emerald-500/10'
                  : 'text-muted-foreground'
                }
              >
                {isConnected ? 'Connected' : 'Disconnected'}
              </Badge>
            </div>

            <h3 className="font-semibold text-base">{provider.name}</h3>

            {isConnected && integration && (
              <div className="mt-2 space-y-1">
                <p className="text-xs text-muted-foreground">
                  Last synced: {formatDate(integration.last_sync_at)}
                </p>
                {integration.last_sync_status && (
                  <p className="text-xs text-muted-foreground">
                    Status: {integration.last_sync_status}
                  </p>
                )}
                {integration.sync_error && (
                  <p className="text-xs text-destructive">{integration.sync_error}</p>
                )}
              </div>
            )}

            <div className="flex items-center gap-2 mt-4">
              {isConnected ? (
                <>
                  <Button
                    variant="outline"
                    size="sm"
                    className="gap-1.5 flex-1"
                    onClick={onSync}
                    disabled={isSyncing}
                  >
                    {isSyncing ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <RefreshCw className="w-3.5 h-3.5" />
                    )}
                    Sync
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    className="gap-1.5 flex-1 text-destructive hover:text-destructive"
                    onClick={() => setShowDisconnectConfirm(true)}
                  >
                    <Unlink className="w-3.5 h-3.5" />
                    Disconnect
                  </Button>
                </>
              ) : (
                <Button
                  size="sm"
                  className="gap-1.5 w-full"
                  onClick={onConnect}
                  disabled={isConnecting}
                >
                  {isConnecting ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <Link2 className="w-3.5 h-3.5" />
                  )}
                  Connect
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      </motion.div>

      <AlertDialog open={showDisconnectConfirm} onOpenChange={setShowDisconnectConfirm}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Disconnect {provider.name}?</AlertDialogTitle>
            <AlertDialogDescription>
              This will remove the {provider.name} integration and stop all data syncing.
              Any previously synced data will remain, but no new data will be imported.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              onClick={() => {
                onDisconnect();
                setShowDisconnectConfirm(false);
              }}
            >
              Disconnect
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}

// ─── Integrations Tab Content ───────────────────────────────────────────

function IntegrationsTabContent() {
  const queryClient = useQueryClient();
  const [connectingProvider, setConnectingProvider] = useState<string | null>(null);
  const [syncingId, setSyncingId] = useState<string | null>(null);

  const { data: integrations, isLoading } = useQuery({
    queryKey: queryKeys.integrations.all,
    queryFn: () => integrationsService.list(),
  });

  const connectMutation = useMutation({
    mutationFn: async (providerType: string) => {
      setConnectingProvider(providerType);
      const result = await integrationsService.initiateOAuth(
        providerType,
        `${window.location.origin}/integrations/oauth/callback`
      );
      return result;
    },
    onSuccess: (data) => {
      window.open(data.auth_url, '_blank', 'noopener,noreferrer');
      toast.success('OAuth flow initiated. Complete authorization in the new tab.');
    },
    onError: () => {
      toast.error('Failed to initiate connection. Please try again.');
    },
    onSettled: () => {
      setConnectingProvider(null);
    },
  });

  const syncMutation = useMutation({
    mutationFn: async (integrationId: string) => {
      setSyncingId(integrationId);
      return integrationsService.sync(integrationId);
    },
    onSuccess: (data) => {
      toast.success(data.message || 'Sync completed successfully.');
      queryClient.invalidateQueries({ queryKey: queryKeys.integrations.all });
    },
    onError: () => {
      toast.error('Sync failed. Please try again.');
    },
    onSettled: () => {
      setSyncingId(null);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (integrationId: string) => integrationsService.delete(integrationId),
    onSuccess: () => {
      toast.success('Integration disconnected successfully.');
      queryClient.invalidateQueries({ queryKey: queryKeys.integrations.all });
    },
    onError: () => {
      toast.error('Failed to disconnect integration.');
    },
  });

  const getIntegrationForProvider = (type: ApiIntegrationType): ApiIntegration | undefined => {
    return integrations?.find((i) => i.integration_type === type && i.is_active);
  };

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {Array.from({ length: 5 }).map((_, i) => (
          <Card key={i}>
            <CardContent className="p-5 space-y-4">
              <div className="flex items-start justify-between">
                <Skeleton className="w-12 h-12 rounded-xl" />
                <Skeleton className="w-24 h-5 rounded-full" />
              </div>
              <Skeleton className="w-32 h-5" />
              <Skeleton className="w-full h-4" />
              <div className="flex gap-2">
                <Skeleton className="w-full h-8" />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {AVAILABLE_PROVIDERS.map((provider) => {
        const integration = getIntegrationForProvider(provider.type);
        return (
          <IntegrationTile
            key={provider.type}
            provider={provider}
            integration={integration}
            onConnect={() => connectMutation.mutate(provider.type)}
            onSync={() => integration && syncMutation.mutate(integration.id)}
            onDisconnect={() => integration && deleteMutation.mutate(integration.id)}
            isSyncing={syncingId === integration?.id}
            isConnecting={connectingProvider === provider.type}
          />
        );
      })}
    </div>
  );
}

// ─── Webhook Deliveries Panel ───────────────────────────────────────────

function WebhookDeliveriesPanel({ webhookId }: { webhookId: string }) {
  const queryClient = useQueryClient();

  const { data: deliveries, isLoading } = useQuery({
    queryKey: queryKeys.integrations.deliveries(webhookId),
    queryFn: () => integrationsService.getWebhookDeliveries(webhookId, 20),
  });

  const retryMutation = useMutation({
    mutationFn: (deliveryId: string) => integrationsService.retryDelivery(deliveryId),
    onSuccess: (data) => {
      toast.success(data.message || 'Delivery retry initiated.');
      queryClient.invalidateQueries({ queryKey: queryKeys.integrations.deliveries(webhookId) });
    },
    onError: () => {
      toast.error('Failed to retry delivery.');
    },
  });

  if (isLoading) {
    return (
      <div className="p-4 space-y-2">
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="w-full h-10" />
        ))}
      </div>
    );
  }

  if (!deliveries?.length) {
    return (
      <div className="p-6 text-center text-sm text-muted-foreground">
        No deliveries recorded yet.
      </div>
    );
  }

  return (
    <div className="border rounded-lg overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-[100px]">Delivery ID</TableHead>
            <TableHead>Event</TableHead>
            <TableHead className="w-[80px]">Status</TableHead>
            <TableHead className="w-[80px]">Time (ms)</TableHead>
            <TableHead>Date</TableHead>
            <TableHead className="w-[80px]">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {deliveries.map((delivery) => (
            <TableRow key={delivery.id}>
              <TableCell className="font-mono text-xs">
                {delivery.id.substring(0, 8)}...
              </TableCell>
              <TableCell>
                <Badge variant="outline" className="text-xs font-mono">
                  {delivery.event_type}
                </Badge>
              </TableCell>
              <TableCell>
                {delivery.is_successful ? (
                  <Badge className="bg-emerald-500/10 text-emerald-600 border-emerald-500/20 hover:bg-emerald-500/10">
                    {delivery.response_status ?? 200}
                  </Badge>
                ) : (
                  <Badge variant="destructive" className="font-mono">
                    {delivery.response_status ?? 'ERR'}
                  </Badge>
                )}
              </TableCell>
              <TableCell className="text-xs text-muted-foreground">
                {delivery.response_time_ms != null ? `${delivery.response_time_ms}ms` : '--'}
              </TableCell>
              <TableCell className="text-xs text-muted-foreground">
                {formatDate(delivery.attempted_at)}
              </TableCell>
              <TableCell>
                {!delivery.is_successful && (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="gap-1 h-7 text-xs"
                    onClick={() => retryMutation.mutate(delivery.id)}
                    disabled={retryMutation.isPending}
                  >
                    <RotateCcw className="w-3 h-3" />
                    Retry
                  </Button>
                )}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

// ─── Webhook Row ────────────────────────────────────────────────────────

function WebhookRow({
  webhook,
  onEdit,
  onDelete,
  onTest,
  onToggle,
}: {
  webhook: ApiWebhook;
  onEdit: () => void;
  onDelete: () => void;
  onTest: () => void;
  onToggle: (active: boolean) => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const [showUrl, setShowUrl] = useState(false);

  return (
    <div className="border rounded-lg overflow-hidden">
      <div className="p-4">
        <div className="flex items-start justify-between gap-4">
          {/* Left: Info */}
          <div className="flex-1 min-w-0 space-y-2">
            <div className="flex items-center gap-2">
              <Webhook className="w-4 h-4 text-muted-foreground flex-shrink-0" />
              <h4 className="font-semibold text-sm truncate">{webhook.name}</h4>
            </div>

            <div className="flex items-center gap-1.5">
              <code className="text-xs bg-muted px-2 py-0.5 rounded font-mono truncate max-w-[300px]">
                {showUrl ? webhook.url : maskUrl(webhook.url)}
              </code>
              <Button
                variant="ghost"
                size="sm"
                className="h-6 w-6 p-0"
                onClick={() => setShowUrl(!showUrl)}
              >
                {showUrl ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="h-6 w-6 p-0"
                onClick={() => {
                  navigator.clipboard.writeText(webhook.url);
                  toast.success('URL copied to clipboard.');
                }}
              >
                <Copy className="w-3 h-3" />
              </Button>
            </div>

            <div className="flex flex-wrap gap-1">
              {webhook.events.map((event) => (
                <Badge key={event} variant="secondary" className="text-[10px] font-mono px-1.5">
                  {event}
                </Badge>
              ))}
            </div>

            <p className="text-xs text-muted-foreground">
              Created {formatDate(webhook.created_at)}
              {webhook.last_delivery_at && (
                <> &middot; Last delivery {formatDate(webhook.last_delivery_at)}</>
              )}
              {webhook.total_deliveries > 0 && (
                <> &middot; {webhook.successful_deliveries}/{webhook.total_deliveries} successful</>
              )}
            </p>
          </div>

          {/* Right: Actions */}
          <div className="flex items-center gap-2 flex-shrink-0">
            <Switch
              checked={webhook.is_active}
              onCheckedChange={onToggle}
            />
            <Button variant="outline" size="sm" className="gap-1 h-8" onClick={onTest}>
              <Send className="w-3 h-3" />
              Test
            </Button>
            <Button variant="ghost" size="sm" className="h-8 w-8 p-0" onClick={onEdit}>
              <Pencil className="w-3.5 h-3.5" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="h-8 w-8 p-0 text-destructive hover:text-destructive"
              onClick={onDelete}
            >
              <Trash2 className="w-3.5 h-3.5" />
            </Button>
          </div>
        </div>

        {/* Deliveries Toggle */}
        <Button
          variant="ghost"
          size="sm"
          className="gap-1 mt-2 h-7 text-xs text-muted-foreground px-1"
          onClick={() => setExpanded(!expanded)}
        >
          {expanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
          View Deliveries
        </Button>
      </div>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden border-t"
          >
            <div className="p-4 bg-muted/30">
              <WebhookDeliveriesPanel webhookId={webhook.id} />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ─── Create/Edit Webhook Dialog ─────────────────────────────────────────

function WebhookFormDialog({
  open,
  onOpenChange,
  webhook,
  onSubmit,
  isSubmitting,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  webhook?: ApiWebhook | null;
  onSubmit: (data: ApiWebhookCreate | ApiWebhookUpdate) => void;
  isSubmitting: boolean;
}) {
  const isEditing = !!webhook;
  const [name, setName] = useState(webhook?.name ?? '');
  const [url, setUrl] = useState(webhook?.url ?? '');
  const [secret, setSecret] = useState('');
  const [selectedEvents, setSelectedEvents] = useState<string[]>(webhook?.events ?? []);

  const handleToggleEvent = (event: string) => {
    setSelectedEvents((prev) =>
      prev.includes(event) ? prev.filter((e) => e !== event) : [...prev, event]
    );
  };

  const handleSubmit = () => {
    if (!name.trim()) {
      toast.error('Webhook name is required.');
      return;
    }
    if (!isEditing && !url.trim()) {
      toast.error('Webhook URL is required.');
      return;
    }
    if (selectedEvents.length === 0) {
      toast.error('Select at least one event.');
      return;
    }

    if (isEditing) {
      const payload: ApiWebhookUpdate = {
        name: name.trim(),
        url: url.trim() || undefined,
        events: selectedEvents,
      };
      onSubmit(payload);
    } else {
      const payload: ApiWebhookCreate = {
        name: name.trim(),
        url: url.trim(),
        events: selectedEvents,
        secret: secret.trim() || undefined,
      };
      onSubmit(payload);
    }
  };

  // Reset form when dialog opens with new data
  const handleOpenChange = (nextOpen: boolean) => {
    if (nextOpen) {
      setName(webhook?.name ?? '');
      setUrl(webhook?.url ?? '');
      setSecret('');
      setSelectedEvents(webhook?.events ?? []);
    }
    onOpenChange(nextOpen);
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>{isEditing ? 'Edit Webhook' : 'Create Webhook'}</DialogTitle>
          <DialogDescription>
            {isEditing
              ? 'Update the webhook configuration.'
              : 'Set up a new webhook to receive real-time event notifications.'}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-2">
          <div className="space-y-2">
            <Label htmlFor="webhook-name">Name</Label>
            <Input
              id="webhook-name"
              placeholder="My Webhook"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="webhook-url">Payload URL</Label>
            <Input
              id="webhook-url"
              placeholder="https://example.com/webhooks"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
            />
          </div>

          {!isEditing && (
            <div className="space-y-2">
              <Label htmlFor="webhook-secret">Secret (optional)</Label>
              <Input
                id="webhook-secret"
                placeholder="whsec_..."
                type="password"
                value={secret}
                onChange={(e) => setSecret(e.target.value)}
              />
              <p className="text-xs text-muted-foreground">
                Used to verify webhook signatures. Store this securely.
              </p>
            </div>
          )}

          <div className="space-y-2">
            <Label>Events</Label>
            <p className="text-xs text-muted-foreground mb-2">
              Select which events should trigger this webhook.
            </p>
            <div className="grid grid-cols-2 gap-1.5 max-h-48 overflow-y-auto pr-1">
              {WEBHOOK_EVENTS.map((event) => {
                const isSelected = selectedEvents.includes(event);
                return (
                  <button
                    key={event}
                    type="button"
                    onClick={() => handleToggleEvent(event)}
                    className={`text-left px-2.5 py-1.5 rounded-md border text-xs font-mono transition-colors ${
                      isSelected
                        ? 'bg-primary/10 border-primary/30 text-primary'
                        : 'border-border hover:bg-muted text-muted-foreground'
                    }`}
                  >
                    {event}
                  </button>
                );
              })}
            </div>
            {selectedEvents.length > 0 && (
              <p className="text-xs text-muted-foreground">
                {selectedEvents.length} event{selectedEvents.length !== 1 ? 's' : ''} selected
              </p>
            )}
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={isSubmitting}>
            {isSubmitting && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
            {isEditing ? 'Save Changes' : 'Create Webhook'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ─── Webhooks Tab Content ───────────────────────────────────────────────

function WebhooksTabContent() {
  const queryClient = useQueryClient();
  const [formOpen, setFormOpen] = useState(false);
  const [editingWebhook, setEditingWebhook] = useState<ApiWebhook | null>(null);
  const [deletingWebhook, setDeletingWebhook] = useState<ApiWebhook | null>(null);

  const { data: webhooks, isLoading } = useQuery({
    queryKey: queryKeys.integrations.webhooks,
    queryFn: () => integrationsService.listWebhooks(),
  });

  const createMutation = useMutation({
    mutationFn: (payload: ApiWebhookCreate) => integrationsService.createWebhook(payload),
    onSuccess: () => {
      toast.success('Webhook created successfully.');
      queryClient.invalidateQueries({ queryKey: queryKeys.integrations.webhooks });
      setFormOpen(false);
    },
    onError: () => {
      toast.error('Failed to create webhook.');
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: ApiWebhookUpdate }) =>
      integrationsService.updateWebhook(id, payload),
    onSuccess: () => {
      toast.success('Webhook updated successfully.');
      queryClient.invalidateQueries({ queryKey: queryKeys.integrations.webhooks });
      setEditingWebhook(null);
    },
    onError: () => {
      toast.error('Failed to update webhook.');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (webhookId: string) => integrationsService.deleteWebhook(webhookId),
    onSuccess: () => {
      toast.success('Webhook deleted.');
      queryClient.invalidateQueries({ queryKey: queryKeys.integrations.webhooks });
      setDeletingWebhook(null);
    },
    onError: () => {
      toast.error('Failed to delete webhook.');
    },
  });

  const testMutation = useMutation({
    mutationFn: (webhookId: string) => integrationsService.testWebhook(webhookId),
    onSuccess: (data) => {
      if (data.status === 'success' || data.message?.toLowerCase().includes('success')) {
        toast.success('Webhook test successful!');
      } else {
        toast.error(`Webhook test returned: ${data.message || data.status}`);
      }
    },
    onError: () => {
      toast.error('Webhook test failed.');
    },
  });

  const toggleMutation = useMutation({
    mutationFn: ({ id, active }: { id: string; active: boolean }) =>
      integrationsService.updateWebhook(id, { is_active: active }),
    onSuccess: (_, variables) => {
      toast.success(variables.active ? 'Webhook activated.' : 'Webhook paused.');
      queryClient.invalidateQueries({ queryKey: queryKeys.integrations.webhooks });
    },
    onError: () => {
      toast.error('Failed to update webhook status.');
    },
  });

  const handleFormSubmit = (data: ApiWebhookCreate | ApiWebhookUpdate) => {
    if (editingWebhook) {
      updateMutation.mutate({ id: editingWebhook.id, payload: data as ApiWebhookUpdate });
    } else {
      createMutation.mutate(data as ApiWebhookCreate);
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <Card key={i}>
            <CardContent className="p-5 space-y-3">
              <Skeleton className="w-48 h-5" />
              <Skeleton className="w-64 h-4" />
              <div className="flex gap-1">
                <Skeleton className="w-20 h-5 rounded-full" />
                <Skeleton className="w-24 h-5 rounded-full" />
                <Skeleton className="w-20 h-5 rounded-full" />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <>
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-muted-foreground">
              {webhooks?.length ?? 0} webhook{(webhooks?.length ?? 0) !== 1 ? 's' : ''} configured
            </p>
          </div>
          <Button
            size="sm"
            className="gap-1.5"
            onClick={() => {
              setEditingWebhook(null);
              setFormOpen(true);
            }}
          >
            <Plus className="w-4 h-4" />
            Create Webhook
          </Button>
        </div>

        {/* Webhook List */}
        {webhooks && webhooks.length > 0 ? (
          <div className="space-y-3">
            {webhooks.map((webhook) => (
              <WebhookRow
                key={webhook.id}
                webhook={webhook}
                onEdit={() => {
                  setEditingWebhook(webhook);
                  setFormOpen(true);
                }}
                onDelete={() => setDeletingWebhook(webhook)}
                onTest={() => testMutation.mutate(webhook.id)}
                onToggle={(active) => toggleMutation.mutate({ id: webhook.id, active })}
              />
            ))}
          </div>
        ) : (
          <Card className="py-16">
            <CardContent className="text-center">
              <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mx-auto mb-4">
                <Webhook className="w-8 h-8 text-muted-foreground" />
              </div>
              <h3 className="text-lg font-medium mb-2">No webhooks yet</h3>
              <p className="text-muted-foreground mb-4">
                Create a webhook to receive real-time notifications when events occur.
              </p>
              <Button
                onClick={() => {
                  setEditingWebhook(null);
                  setFormOpen(true);
                }}
              >
                <Plus className="w-4 h-4 mr-2" />
                Create Webhook
              </Button>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Create / Edit Dialog */}
      <WebhookFormDialog
        open={formOpen}
        onOpenChange={(open) => {
          setFormOpen(open);
          if (!open) setEditingWebhook(null);
        }}
        webhook={editingWebhook}
        onSubmit={handleFormSubmit}
        isSubmitting={createMutation.isPending || updateMutation.isPending}
      />

      {/* Delete Confirmation */}
      <AlertDialog
        open={!!deletingWebhook}
        onOpenChange={(open) => { if (!open) setDeletingWebhook(null); }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete webhook?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently delete the webhook &ldquo;{deletingWebhook?.name}&rdquo; and all
              its delivery history. This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              onClick={() => deletingWebhook && deleteMutation.mutate(deletingWebhook.id)}
            >
              {deleteMutation.isPending ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : null}
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}

// ─── Main Page ──────────────────────────────────────────────────────────

export default function IntegrationsPage() {
  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Page Header */}
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Integrations</h1>
          <p className="text-muted-foreground mt-1">
            Connect your tools and configure webhooks to streamline your workflow.
          </p>
        </div>

        {/* Tabs */}
        <Tabs defaultValue="integrations">
          <TabsList>
            <TabsTrigger value="integrations" className="gap-1.5">
              <Plug className="w-4 h-4" />
              Integrations
            </TabsTrigger>
            <TabsTrigger value="webhooks" className="gap-1.5">
              <Webhook className="w-4 h-4" />
              Webhooks
            </TabsTrigger>
          </TabsList>

          <TabsContent value="integrations" className="mt-4">
            <IntegrationsTabContent />
          </TabsContent>

          <TabsContent value="webhooks" className="mt-4">
            <WebhooksTabContent />
          </TabsContent>
        </Tabs>
      </div>
    </DashboardLayout>
  );
}

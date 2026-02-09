import { useState } from 'react';
import { motion } from 'framer-motion';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  ShieldCheck,
  Activity,
  Database,
  Server,
  Brain,
  HardDrive,
  Cog,
  FileDown,
  Trash2,
  Key,
  Plus,
  Copy,
  Filter,
  ChevronLeft,
  ChevronRight,
  AlertTriangle,
  Loader2,
  BarChart3,
  TrendingUp,
  Zap,
} from 'lucide-react';
import { toast } from 'sonner';
import DashboardLayout from '@/components/layout/DashboardLayout';
import { adminService } from '@/services/admin.service';
import { queryKeys } from '@/hooks/useApi';
import { getApiErrorMessage } from '@/lib/api-client';
import type {
  ApiAuditLog,
  ApiAuditAction,
  ApiAPIKey,
  ApiAPIKeyCreatedResponse,
} from '@/types/api';

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
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
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';

// ─── Helpers ────────────────────────────────────────────────────────────

function formatTimestamp(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function formatRelativeTime(iso: string | undefined | null): string {
  if (!iso) return 'Never';
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60_000);
  if (mins < 1) return 'Just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}

function formatUptime(seconds: number): string {
  const d = Math.floor(seconds / 86400);
  const h = Math.floor((seconds % 86400) / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  if (d > 0) return `${d}d ${h}h`;
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m`;
}

function formatBytes(mb: number): string {
  if (mb >= 1024) return `${(mb / 1024).toFixed(1)} GB`;
  return `${Math.round(mb)} MB`;
}

const AUDIT_ACTIONS: ApiAuditAction[] = [
  'CREATE',
  'UPDATE',
  'DELETE',
  'LOGIN',
  'LOGOUT',
  'ACCESS',
  'EXPORT',
  'IMPORT',
];

const PAGE_SIZE = 15;

// ─── 1. Audit Logs Tab ─────────────────────────────────────────────────

function AuditLogsSection() {
  const [actionFilter, setActionFilter] = useState<string>('all');
  const [page, setPage] = useState(0);

  const filters: Record<string, unknown> = {
    skip: page * PAGE_SIZE,
    limit: PAGE_SIZE,
    ...(actionFilter !== 'all' && { action: actionFilter }),
  };

  const { data, isLoading } = useQuery({
    queryKey: queryKeys.admin.auditLogs(filters),
    queryFn: () =>
      adminService.getAuditLogs({
        skip: page * PAGE_SIZE,
        limit: PAGE_SIZE,
        ...(actionFilter !== 'all' && { action: actionFilter }),
      }),
    placeholderData: (prev) => prev,
  });

  const logs = data?.logs ?? [];
  const total = data?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  const actionBadgeVariant = (action: string) => {
    switch (action) {
      case 'CREATE':
        return 'default';
      case 'DELETE':
        return 'destructive';
      case 'LOGIN':
      case 'LOGOUT':
        return 'secondary';
      default:
        return 'outline';
    }
  };

  return (
    <div className="space-y-4">
      {/* Filter bar */}
      <div className="flex items-center gap-3">
        <Filter className="w-4 h-4 text-muted-foreground" />
        <Select value={actionFilter} onValueChange={(v) => { setActionFilter(v); setPage(0); }}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Filter by action" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Actions</SelectItem>
            {AUDIT_ACTIONS.map((a) => (
              <SelectItem key={a} value={a}>
                {a}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <span className="text-sm text-muted-foreground ml-auto">
          {total} total entries
        </span>
      </div>

      {/* Table */}
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Timestamp</TableHead>
                <TableHead>User</TableHead>
                <TableHead>Action</TableHead>
                <TableHead>Resource</TableHead>
                <TableHead>Details</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading
                ? Array.from({ length: 8 }).map((_, i) => (
                    <TableRow key={i}>
                      {Array.from({ length: 5 }).map((__, j) => (
                        <TableCell key={j}>
                          <Skeleton className="h-4 w-full" />
                        </TableCell>
                      ))}
                    </TableRow>
                  ))
                : logs.map((log: ApiAuditLog) => (
                    <TableRow key={log.id}>
                      <TableCell className="text-muted-foreground text-xs">
                        {formatTimestamp(log.timestamp)}
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-col">
                          <span className="font-medium text-sm">{log.actor_name}</span>
                          <span className="text-xs text-muted-foreground">{log.actor_type}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant={actionBadgeVariant(log.action) as 'default' | 'destructive' | 'secondary' | 'outline'}>
                          {log.action}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-sm">
                        {log.resource_type}
                        {log.resource_id && (
                          <span className="text-muted-foreground ml-1 text-xs">
                            #{log.resource_id.slice(0, 8)}
                          </span>
                        )}
                      </TableCell>
                      <TableCell className="max-w-[260px] truncate text-sm text-muted-foreground">
                        {log.description}
                      </TableCell>
                    </TableRow>
                  ))}
              {!isLoading && logs.length === 0 && (
                <TableRow>
                  <TableCell colSpan={5} className="text-center py-12 text-muted-foreground">
                    No audit logs found
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Pagination */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          Page {page + 1} of {totalPages}
        </p>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={page === 0}
            onClick={() => setPage((p) => Math.max(0, p - 1))}
          >
            <ChevronLeft className="w-4 h-4 mr-1" />
            Previous
          </Button>
          <Button
            variant="outline"
            size="sm"
            disabled={page >= totalPages - 1}
            onClick={() => setPage((p) => p + 1)}
          >
            Next
            <ChevronRight className="w-4 h-4 ml-1" />
          </Button>
        </div>
      </div>
    </div>
  );
}

// ─── 2. System Health Tab ───────────────────────────────────────────────

function SystemHealthSection() {
  const { data: health, isLoading } = useQuery({
    queryKey: queryKeys.admin.systemHealth,
    queryFn: () => adminService.getSystemHealth(),
    refetchInterval: 30_000,
  });

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {Array.from({ length: 5 }).map((_, i) => (
          <Card key={i}>
            <CardContent className="p-6 space-y-3">
              <Skeleton className="h-5 w-32" />
              <Skeleton className="h-8 w-24" />
              <Skeleton className="h-4 w-48" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (!health) return null;

  const dbConnected = health.status === 'healthy' || health.db_connections_active > 0;
  const errorRate = health.api_error_rate;
  const uptimePercent = errorRate != null ? (100 - errorRate).toFixed(2) : '99.99';

  const cards: {
    title: string;
    icon: React.ElementType;
    color: string;
    content: React.ReactNode;
  }[] = [
    {
      title: 'Database',
      icon: Database,
      color: 'from-blue-500 to-cyan-500',
      content: (
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Badge variant={dbConnected ? 'default' : 'destructive'}>
              {dbConnected ? 'Connected' : 'Disconnected'}
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground">
            Avg query: <span className="font-medium text-foreground">{health.db_query_avg_ms.toFixed(1)} ms</span>
          </p>
          <p className="text-sm text-muted-foreground">
            Active connections: <span className="font-medium text-foreground">{health.db_connections_active}</span>
          </p>
        </div>
      ),
    },
    {
      title: 'API Service',
      icon: Server,
      color: 'from-violet-500 to-purple-500',
      content: (
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <span className="text-2xl font-bold">{uptimePercent}%</span>
            <span className="text-sm text-muted-foreground">uptime</span>
          </div>
          <p className="text-sm text-muted-foreground">
            P50 latency: <span className="font-medium text-foreground">{health.api_latency_p50_ms} ms</span>
          </p>
          <p className="text-sm text-muted-foreground">
            P99 latency: <span className="font-medium text-foreground">{health.api_latency_p99_ms} ms</span>
          </p>
          <p className="text-sm text-muted-foreground">
            Requests/min: <span className="font-medium text-foreground">{health.api_requests_per_minute}</span>
          </p>
        </div>
      ),
    },
    {
      title: 'AI Service',
      icon: Brain,
      color: 'from-emerald-500 to-teal-500',
      content: (
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Badge variant={health.ai_avg_latency_ms < 5000 ? 'default' : 'destructive'}>
              {health.ai_avg_latency_ms < 5000 ? 'Healthy' : 'Degraded'}
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground">
            Avg latency: <span className="font-medium text-foreground">{health.ai_avg_latency_ms} ms</span>
          </p>
          <p className="text-sm text-muted-foreground">
            Requests/hr: <span className="font-medium text-foreground">{health.ai_requests_per_hour}</span>
          </p>
          <p className="text-sm text-muted-foreground">
            Cache hit rate: <span className="font-medium text-foreground">{(health.ai_cache_hit_rate * 100).toFixed(1)}%</span>
          </p>
        </div>
      ),
    },
    {
      title: 'Background Jobs',
      icon: Cog,
      color: 'from-amber-500 to-orange-500',
      content: (
        <div className="space-y-2">
          <div className="flex items-center gap-4">
            <div>
              <p className="text-2xl font-bold">{health.jobs_pending}</p>
              <p className="text-xs text-muted-foreground">Pending</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-destructive">{health.jobs_failed}</p>
              <p className="text-xs text-muted-foreground">Failed</p>
            </div>
          </div>
          {health.jobs_failed > 0 && (
            <div className="flex items-center gap-1 text-destructive text-sm">
              <AlertTriangle className="w-3.5 h-3.5" />
              <span>{health.jobs_failed} failed jobs need attention</span>
            </div>
          )}
        </div>
      ),
    },
    {
      title: 'Storage',
      icon: HardDrive,
      color: 'from-pink-500 to-rose-500',
      content: (
        <div className="space-y-2">
          <p className="text-2xl font-bold">{formatBytes(health.storage_used_mb)}</p>
          <p className="text-sm text-muted-foreground">Storage used</p>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-4">
      {/* Overall status */}
      <div className="flex items-center gap-3">
        <Badge
          variant={health.status === 'healthy' ? 'default' : 'destructive'}
          className="text-sm px-3 py-1"
        >
          {health.status === 'healthy' ? 'All Systems Operational' : 'Issues Detected'}
        </Badge>
        <span className="text-sm text-muted-foreground">
          Uptime: {formatUptime(health.uptime_seconds)}
        </span>
      </div>

      {/* Active alerts */}
      {health.active_alerts.length > 0 && (
        <Card className="border-destructive/50">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-2">
              <AlertTriangle className="w-4 h-4 text-destructive" />
              <span className="font-medium text-destructive">Active Alerts</span>
            </div>
            <ul className="space-y-1">
              {health.active_alerts.map((alert, i) => (
                <li key={i} className="text-sm text-muted-foreground">
                  {alert}
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* Health cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {cards.map((card, index) => {
          const Icon = card.icon;
          return (
            <motion.div
              key={card.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.07 }}
            >
              <Card className="h-full">
                <CardHeader className="pb-2">
                  <div className="flex items-center gap-3">
                    <div
                      className={`w-9 h-9 rounded-lg bg-gradient-to-br ${card.color} flex items-center justify-center`}
                    >
                      <Icon className="w-4.5 h-4.5 text-white" />
                    </div>
                    <CardTitle className="text-base">{card.title}</CardTitle>
                  </div>
                </CardHeader>
                <CardContent>{card.content}</CardContent>
              </Card>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}

// ─── 3. GDPR Tab ────────────────────────────────────────────────────────

function GDPRSection() {
  const [exportUserId, setExportUserId] = useState('');
  const [erasureUserId, setErasureUserId] = useState('');

  const exportMutation = useMutation({
    mutationFn: (userId: string) => adminService.requestGDPRExport(userId),
    onSuccess: (res) => {
      toast.success(res.message || 'Data export requested successfully');
      setExportUserId('');
    },
    onError: (err) => toast.error(getApiErrorMessage(err)),
  });

  const erasureMutation = useMutation({
    mutationFn: (userId: string) => adminService.requestGDPRErasure(userId),
    onSuccess: (res) => {
      toast.success(res.message || 'Data erasure request submitted');
      setErasureUserId('');
    },
    onError: (err) => toast.error(getApiErrorMessage(err)),
  });

  return (
    <div className="grid md:grid-cols-2 gap-6">
      {/* Data Export */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center">
              <FileDown className="w-4.5 h-4.5 text-white" />
            </div>
            <div>
              <CardTitle className="text-base">Data Export</CardTitle>
              <CardDescription>Export all user data (GDPR Art. 20)</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium" htmlFor="export-user-id">
              User ID or Email
            </label>
            <Input
              id="export-user-id"
              placeholder="Enter user ID or email address"
              value={exportUserId}
              onChange={(e) => setExportUserId(e.target.value)}
            />
          </div>
          <Button
            className="gap-2 w-full"
            disabled={!exportUserId.trim() || exportMutation.isPending}
            onClick={() => exportMutation.mutate(exportUserId.trim())}
          >
            {exportMutation.isPending ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <FileDown className="w-4 h-4" />
            )}
            Request Export
          </Button>
        </CardContent>
      </Card>

      {/* Data Erasure */}
      <Card className="border-destructive/30">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-red-500 to-rose-500 flex items-center justify-center">
              <Trash2 className="w-4.5 h-4.5 text-white" />
            </div>
            <div>
              <CardTitle className="text-base">Data Erasure</CardTitle>
              <CardDescription>Permanently delete user data (GDPR Art. 17)</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium" htmlFor="erasure-user-id">
              User ID or Email
            </label>
            <Input
              id="erasure-user-id"
              placeholder="Enter user ID or email address"
              value={erasureUserId}
              onChange={(e) => setErasureUserId(e.target.value)}
            />
          </div>

          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button
                variant="destructive"
                className="gap-2 w-full"
                disabled={!erasureUserId.trim() || erasureMutation.isPending}
              >
                {erasureMutation.isPending ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Trash2 className="w-4 h-4" />
                )}
                Request Erasure
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Confirm Data Erasure</AlertDialogTitle>
                <AlertDialogDescription>
                  This action is <strong>irreversible</strong>. All data associated with
                  user <strong>{erasureUserId}</strong> will be permanently deleted in
                  compliance with GDPR Article 17. This includes personal data, activity
                  history, and all associated records.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction
                  className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                  onClick={() => erasureMutation.mutate(erasureUserId.trim())}
                >
                  Permanently Delete Data
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </CardContent>
      </Card>
    </div>
  );
}

// ─── 4. API Keys Tab ────────────────────────────────────────────────────

function APIKeysSection() {
  const queryClient = useQueryClient();
  const [createOpen, setCreateOpen] = useState(false);
  const [newKeyName, setNewKeyName] = useState('');
  const [createdKey, setCreatedKey] = useState<ApiAPIKeyCreatedResponse | null>(null);

  const { data: apiKeys, isLoading } = useQuery({
    queryKey: queryKeys.admin.apiKeys,
    queryFn: () => adminService.listAPIKeys(),
  });

  const createMutation = useMutation({
    mutationFn: (name: string) => adminService.createAPIKey({ name }),
    onSuccess: (res) => {
      setCreatedKey(res);
      setNewKeyName('');
      queryClient.invalidateQueries({ queryKey: queryKeys.admin.apiKeys });
      toast.success('API key created');
    },
    onError: (err) => toast.error(getApiErrorMessage(err)),
  });

  const revokeMutation = useMutation({
    mutationFn: (keyId: string) => adminService.revokeAPIKey(keyId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.admin.apiKeys });
      toast.success('API key revoked');
    },
    onError: (err) => toast.error(getApiErrorMessage(err)),
  });

  const handleCopyKey = (key: string) => {
    navigator.clipboard.writeText(key);
    toast.success('API key copied to clipboard');
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          Manage API keys for programmatic access
        </p>
        <Dialog
          open={createOpen}
          onOpenChange={(open) => {
            setCreateOpen(open);
            if (!open) {
              setCreatedKey(null);
              setNewKeyName('');
            }
          }}
        >
          <DialogTrigger asChild>
            <Button className="gap-2">
              <Plus className="w-4 h-4" />
              Create Key
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>
                {createdKey ? 'API Key Created' : 'Create New API Key'}
              </DialogTitle>
              <DialogDescription>
                {createdKey
                  ? 'Copy this key now. You will not be able to see it again.'
                  : 'Give your new API key a descriptive name.'}
              </DialogDescription>
            </DialogHeader>

            {createdKey ? (
              <div className="space-y-3">
                <div className="flex items-center gap-2 p-3 rounded-lg bg-muted font-mono text-sm break-all">
                  <span className="flex-1">{createdKey.key}</span>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleCopyKey(createdKey.key)}
                  >
                    <Copy className="w-4 h-4" />
                  </Button>
                </div>
                <DialogFooter>
                  <Button onClick={() => { setCreateOpen(false); setCreatedKey(null); }}>
                    Done
                  </Button>
                </DialogFooter>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium" htmlFor="api-key-name">
                    Key Name
                  </label>
                  <Input
                    id="api-key-name"
                    placeholder="e.g. Production API, CI/CD Pipeline"
                    value={newKeyName}
                    onChange={(e) => setNewKeyName(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && newKeyName.trim()) {
                        createMutation.mutate(newKeyName.trim());
                      }
                    }}
                  />
                </div>
                <DialogFooter>
                  <Button
                    disabled={!newKeyName.trim() || createMutation.isPending}
                    onClick={() => createMutation.mutate(newKeyName.trim())}
                    className="gap-2"
                  >
                    {createMutation.isPending && (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    )}
                    Create Key
                  </Button>
                </DialogFooter>
              </div>
            )}
          </DialogContent>
        </Dialog>
      </div>

      {/* Keys list */}
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Key Prefix</TableHead>
                <TableHead>Created</TableHead>
                <TableHead>Last Used</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading
                ? Array.from({ length: 4 }).map((_, i) => (
                    <TableRow key={i}>
                      {Array.from({ length: 6 }).map((__, j) => (
                        <TableCell key={j}>
                          <Skeleton className="h-4 w-full" />
                        </TableCell>
                      ))}
                    </TableRow>
                  ))
                : (apiKeys ?? []).map((apiKey: ApiAPIKey) => (
                    <TableRow key={apiKey.id}>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Key className="w-4 h-4 text-muted-foreground" />
                          <span className="font-medium">{apiKey.name}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <code className="text-sm bg-muted px-2 py-0.5 rounded">
                          {apiKey.key_prefix}••••••••
                        </code>
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {formatTimestamp(apiKey.created_at)}
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {formatRelativeTime(apiKey.last_used_at)}
                      </TableCell>
                      <TableCell>
                        <Badge variant={apiKey.is_active ? 'default' : 'secondary'}>
                          {apiKey.is_active ? 'Active' : 'Revoked'}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        {apiKey.is_active && (
                          <AlertDialog>
                            <AlertDialogTrigger asChild>
                              <Button
                                variant="ghost"
                                size="sm"
                                className="text-destructive hover:text-destructive"
                                disabled={revokeMutation.isPending}
                              >
                                Revoke
                              </Button>
                            </AlertDialogTrigger>
                            <AlertDialogContent>
                              <AlertDialogHeader>
                                <AlertDialogTitle>Revoke API Key</AlertDialogTitle>
                                <AlertDialogDescription>
                                  Are you sure you want to revoke the API key{' '}
                                  <strong>{apiKey.name}</strong>? Any applications
                                  using this key will lose access immediately.
                                </AlertDialogDescription>
                              </AlertDialogHeader>
                              <AlertDialogFooter>
                                <AlertDialogCancel>Cancel</AlertDialogCancel>
                                <AlertDialogAction
                                  className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                                  onClick={() => revokeMutation.mutate(apiKey.id)}
                                >
                                  Revoke Key
                                </AlertDialogAction>
                              </AlertDialogFooter>
                            </AlertDialogContent>
                          </AlertDialog>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
              {!isLoading && (apiKeys ?? []).length === 0 && (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-12 text-muted-foreground">
                    No API keys yet. Create one to get started.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}

// ─── 5. AI Governance Tab ───────────────────────────────────────────────

function AIGovernanceSection() {
  const { data: governance, isLoading } = useQuery({
    queryKey: queryKeys.admin.aiGovernance,
    queryFn: () => adminService.getAIGovernance(),
  });

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <Card key={i}>
            <CardContent className="p-6 space-y-3">
              <Skeleton className="h-5 w-28" />
              <Skeleton className="h-10 w-20" />
              <Skeleton className="h-4 w-40" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (!governance) return null;

  const statsCards: {
    title: string;
    value: string;
    subtitle: string;
    icon: React.ElementType;
    color: string;
  }[] = [
    {
      title: 'Total AI Queries',
      value: governance.total_ai_requests.toLocaleString(),
      subtitle: 'All-time AI requests',
      icon: Brain,
      color: 'from-violet-500 to-purple-500',
    },
    {
      title: 'Avg Quality Score',
      value: `${(governance.quality_metrics.avg_confidence * 100).toFixed(1)}%`,
      subtitle: `Helpful rate: ${(governance.quality_metrics.helpful_rate * 100).toFixed(1)}%`,
      icon: BarChart3,
      color: 'from-emerald-500 to-teal-500',
    },
    {
      title: 'Escalation Rate',
      value: `${(governance.quality_metrics.escalation_rate * 100).toFixed(1)}%`,
      subtitle: 'Queries escalated to human',
      icon: TrendingUp,
      color: 'from-amber-500 to-orange-500',
    },
    {
      title: 'Avg Response Time',
      value: `${governance.avg_response_time_ms} ms`,
      subtitle: `Cache hit rate: ${(governance.cache_hit_rate * 100).toFixed(1)}%`,
      icon: Zap,
      color: 'from-blue-500 to-cyan-500',
    },
    {
      title: 'Tokens Used',
      value: governance.total_tokens_used.toLocaleString(),
      subtitle: `Estimated cost: $${governance.estimated_cost.toFixed(2)}`,
      icon: Activity,
      color: 'from-pink-500 to-rose-500',
    },
    {
      title: 'Model',
      value: governance.model,
      subtitle: `Provider: ${governance.provider}`,
      icon: Server,
      color: 'from-indigo-500 to-blue-500',
    },
  ];

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {statsCards.map((card, index) => {
          const Icon = card.icon;
          return (
            <motion.div
              key={card.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.07 }}
            >
              <Card className="h-full">
                <CardContent className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div
                      className={`w-10 h-10 rounded-xl bg-gradient-to-br ${card.color} flex items-center justify-center`}
                    >
                      <Icon className="w-5 h-5 text-white" />
                    </div>
                  </div>
                  <p className="text-2xl font-bold">{card.value}</p>
                  <p className="text-sm font-medium mt-1">{card.title}</p>
                  <p className="text-xs text-muted-foreground mt-0.5">{card.subtitle}</p>
                </CardContent>
              </Card>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}

// ─── Page Component ─────────────────────────────────────────────────────

export default function AdminPage() {
  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Administration</h1>
          <p className="text-muted-foreground mt-1">
            System monitoring, compliance, and platform management
          </p>
        </div>

        {/* Tabs */}
        <Tabs defaultValue="audit-logs" className="space-y-6">
          <TabsList className="grid grid-cols-2 lg:grid-cols-5 w-full lg:w-auto">
            <TabsTrigger value="audit-logs" className="gap-2">
              <ShieldCheck className="w-4 h-4" />
              <span className="hidden sm:inline">Audit Logs</span>
            </TabsTrigger>
            <TabsTrigger value="system-health" className="gap-2">
              <Activity className="w-4 h-4" />
              <span className="hidden sm:inline">System Health</span>
            </TabsTrigger>
            <TabsTrigger value="gdpr" className="gap-2">
              <FileDown className="w-4 h-4" />
              <span className="hidden sm:inline">GDPR</span>
            </TabsTrigger>
            <TabsTrigger value="api-keys" className="gap-2">
              <Key className="w-4 h-4" />
              <span className="hidden sm:inline">API Keys</span>
            </TabsTrigger>
            <TabsTrigger value="ai-governance" className="gap-2">
              <Brain className="w-4 h-4" />
              <span className="hidden sm:inline">AI Governance</span>
            </TabsTrigger>
          </TabsList>

          <TabsContent value="audit-logs">
            <AuditLogsSection />
          </TabsContent>

          <TabsContent value="system-health">
            <SystemHealthSection />
          </TabsContent>

          <TabsContent value="gdpr">
            <GDPRSection />
          </TabsContent>

          <TabsContent value="api-keys">
            <APIKeysSection />
          </TabsContent>

          <TabsContent value="ai-governance">
            <AIGovernanceSection />
          </TabsContent>
        </Tabs>
      </div>
    </DashboardLayout>
  );
}

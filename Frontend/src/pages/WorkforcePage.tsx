import { useState } from 'react';
import { motion } from 'framer-motion';
import { useQuery, useMutation } from '@tanstack/react-query';
import {
  Heart,
  Users,
  Trophy,
  AlertTriangle,
  FlaskConical,
  Briefcase,
  Medal,
  TrendingUp,
  TrendingDown,
  Minus,
  ArrowUpRight,
  Loader2,
  Plus,
  ChevronUp,
  ChevronDown,
  Info,
} from 'lucide-react';
import { toast } from 'sonner';
import {
  RadialBarChart,
  RadialBar,
  ResponsiveContainer,
  PolarAngleAxis,
} from 'recharts';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Skeleton } from '@/components/ui/skeleton';
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
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

import DashboardLayout from '@/components/layout/DashboardLayout';
import { workforceService } from '@/services/workforce.service';
import { queryKeys } from '@/hooks/useApi';
import { getApiErrorMessage } from '@/lib/api-client';

// ─── Helpers ────────────────────────────────────────────────────────

function scoreColor(score: number): string {
  if (score > 80) return 'text-emerald-500';
  if (score >= 60) return 'text-amber-500';
  return 'text-red-500';
}

function riskBadgeColor(level: string): string {
  switch (level) {
    case 'critical':
      return 'bg-red-600 text-white';
    case 'high':
      return 'bg-red-500/15 text-red-500';
    case 'medium':
      return 'bg-amber-500/15 text-amber-500';
    case 'low':
      return 'bg-emerald-500/15 text-emerald-500';
    default:
      return 'bg-muted text-muted-foreground';
  }
}

function riskProgressColor(level: string): string {
  switch (level) {
    case 'critical':
    case 'high':
      return '[&>div]:bg-red-500';
    case 'medium':
      return '[&>div]:bg-amber-500';
    case 'low':
      return '[&>div]:bg-emerald-500';
    default:
      return '';
  }
}

function urgencyBadgeColor(urgency: string): string {
  switch (urgency) {
    case 'critical':
      return 'bg-red-600 text-white';
    case 'high':
      return 'bg-red-500/15 text-red-500';
    case 'medium':
      return 'bg-amber-500/15 text-amber-500';
    case 'low':
      return 'bg-emerald-500/15 text-emerald-500';
    default:
      return 'bg-muted text-muted-foreground';
  }
}

function trendIcon(trend: string) {
  if (trend === 'improving') return <TrendingUp className="w-4 h-4 text-emerald-500" />;
  if (trend === 'declining') return <TrendingDown className="w-4 h-4 text-red-500" />;
  return <Minus className="w-4 h-4 text-muted-foreground" />;
}

// ─── Gauge Component ────────────────────────────────────────────────

function HealthGauge({ value, label }: { value: number; label: string }) {
  const fillColor = value > 80 ? '#10b981' : value >= 60 ? '#f59e0b' : '#ef4444';
  const gaugeData = [{ name: label, value, fill: fillColor }];

  return (
    <div className="relative flex flex-col items-center">
      <div className="w-48 h-48">
        <ResponsiveContainer width="100%" height="100%">
          <RadialBarChart
            cx="50%"
            cy="50%"
            innerRadius="70%"
            outerRadius="100%"
            barSize={14}
            data={gaugeData}
            startAngle={210}
            endAngle={-30}
          >
            <PolarAngleAxis type="number" domain={[0, 100]} angleAxisId={0} tick={false} />
            <RadialBar
              background={{ fill: 'hsl(var(--muted))' }}
              dataKey="value"
              cornerRadius={8}
              angleAxisId={0}
            />
          </RadialBarChart>
        </ResponsiveContainer>
      </div>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className={`text-4xl font-bold ${scoreColor(value)}`}>{value}</span>
        <span className="text-sm text-muted-foreground">{label}</span>
      </div>
    </div>
  );
}

// ─── Org Health Tab ─────────────────────────────────────────────────

function OrgHealthTab() {
  const { data: orgHealth, isLoading } = useQuery({
    queryKey: queryKeys.workforce.orgHealth,
    queryFn: () => workforceService.getOrgHealth(),
  });

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex justify-center">
          <Skeleton className="w-48 h-48 rounded-full" />
        </div>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-28 rounded-xl" />
          ))}
        </div>
      </div>
    );
  }

  if (!orgHealth) return null;

  const dimensions = [
    {
      label: 'Productivity',
      value: orgHealth.productivity_index,
      icon: TrendingUp,
      color: 'from-blue-500 to-cyan-500',
    },
    {
      label: 'Skill Coverage',
      value: orgHealth.skill_coverage_index,
      icon: Users,
      color: 'from-violet-500 to-purple-500',
    },
    {
      label: 'Management Quality',
      value: orgHealth.management_quality_index,
      icon: Trophy,
      color: 'from-amber-500 to-orange-500',
    },
    {
      label: 'Delivery Predictability',
      value: orgHealth.delivery_predictability_index,
      icon: ArrowUpRight,
      color: 'from-emerald-500 to-teal-500',
    },
  ];

  const riskAreas: string[] = [];
  if (orgHealth.high_attrition_risk_count > 0)
    riskAreas.push(`${orgHealth.high_attrition_risk_count} high attrition risk`);
  if (orgHealth.high_burnout_risk_count > 0)
    riskAreas.push(`${orgHealth.high_burnout_risk_count} high burnout risk`);
  if (orgHealth.blocked_tasks > 0)
    riskAreas.push(`${orgHealth.blocked_tasks} blocked tasks`);
  if (orgHealth.overdue_tasks > 0)
    riskAreas.push(`${orgHealth.overdue_tasks} overdue tasks`);

  return (
    <div className="space-y-6">
      {/* Central Gauge */}
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
      >
        <Card>
          <CardContent className="py-8 flex flex-col items-center">
            <HealthGauge value={orgHealth.overall_health_score} label="Overall Health" />
            <div className="mt-4 flex gap-6 text-sm text-muted-foreground">
              <span>{orgHealth.total_employees} employees</span>
              <span>{orgHealth.active_tasks} active tasks</span>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Dimension Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {dimensions.map((dim, index) => {
          const Icon = dim.icon;
          return (
            <motion.div
              key={dim.label}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <Card className="hover-lift">
                <CardContent className="p-4 lg:p-6">
                  <div className="flex items-center gap-3 mb-3">
                    <div
                      className={`w-9 h-9 rounded-lg bg-gradient-to-br ${dim.color} flex items-center justify-center`}
                    >
                      <Icon className="w-4 h-4 text-white" />
                    </div>
                    <span className="text-sm font-medium">{dim.label}</span>
                  </div>
                  <p className={`text-2xl font-bold mb-2 ${scoreColor(dim.value)}`}>
                    {dim.value}
                  </p>
                  <Progress
                    value={dim.value}
                    className={`h-2 ${dim.value > 80 ? '[&>div]:bg-emerald-500' : dim.value >= 60 ? '[&>div]:bg-amber-500' : '[&>div]:bg-red-500'}`}
                  />
                </CardContent>
              </Card>
            </motion.div>
          );
        })}
      </div>

      {/* Automation Maturity */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Automation Maturity</CardTitle>
          <CardDescription>Organization automation adoption index</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4">
            <Progress
              value={orgHealth.automation_maturity_index}
              className="flex-1 h-3 [&>div]:bg-violet-500"
            />
            <span className="text-lg font-bold">{orgHealth.automation_maturity_index}%</span>
          </div>
        </CardContent>
      </Card>

      {/* Risk Areas */}
      {riskAreas.length > 0 && (
        <Card className="border-amber-500/30">
          <CardHeader className="pb-3">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-amber-500" />
              <CardTitle className="text-lg">Risk Areas</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {riskAreas.map((area) => (
                <Badge key={area} variant="secondary" className="bg-amber-500/10 text-amber-500">
                  <AlertTriangle className="w-3 h-3 mr-1" />
                  {area}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// ─── Workforce Scores Tab ───────────────────────────────────────────

function WorkforceScoresTab() {
  const [sortBy, setSortBy] = useState<'overall_score' | 'velocity_score' | 'quality_score' | 'collaboration_score' | 'learning_score'>('overall_score');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');
  const [selectedUser, setSelectedUser] = useState<string | null>(null);

  const { data: scores, isLoading } = useQuery({
    queryKey: queryKeys.workforce.scores({ sort_by: sortBy }),
    queryFn: () => workforceService.getScores({ limit: 100 }),
  });

  const { data: userDetail, isLoading: detailLoading } = useQuery({
    queryKey: queryKeys.workforce.userScore(selectedUser ?? ''),
    queryFn: () => workforceService.getUserScore(selectedUser!),
    enabled: !!selectedUser,
  });

  const sortedScores = [...(scores ?? [])].sort((a, b) => {
    const aVal = a[sortBy] ?? 0;
    const bVal = b[sortBy] ?? 0;
    return sortDir === 'desc' ? bVal - aVal : aVal - bVal;
  });

  function handleSort(col: typeof sortBy) {
    if (sortBy === col) {
      setSortDir((d) => (d === 'desc' ? 'asc' : 'desc'));
    } else {
      setSortBy(col);
      setSortDir('desc');
    }
  }

  function SortIcon({ col }: { col: typeof sortBy }) {
    if (sortBy !== col) return null;
    return sortDir === 'desc' ? (
      <ChevronDown className="w-3 h-3 ml-1 inline" />
    ) : (
      <ChevronUp className="w-3 h-3 ml-1 inline" />
    );
  }

  if (isLoading) {
    return (
      <Card>
        <CardContent className="py-8">
          <div className="space-y-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-12 w-full rounded-lg" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <Card>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead
                className="cursor-pointer select-none"
                onClick={() => handleSort('overall_score')}
              >
                Overall Score
                <SortIcon col="overall_score" />
              </TableHead>
              <TableHead
                className="cursor-pointer select-none"
                onClick={() => handleSort('velocity_score')}
              >
                Productivity
                <SortIcon col="velocity_score" />
              </TableHead>
              <TableHead
                className="cursor-pointer select-none"
                onClick={() => handleSort('quality_score')}
              >
                Quality
                <SortIcon col="quality_score" />
              </TableHead>
              <TableHead
                className="cursor-pointer select-none"
                onClick={() => handleSort('collaboration_score')}
              >
                Collaboration
                <SortIcon col="collaboration_score" />
              </TableHead>
              <TableHead
                className="cursor-pointer select-none"
                onClick={() => handleSort('learning_score')}
              >
                Growth
                <SortIcon col="learning_score" />
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {sortedScores.map((s) => (
              <TableRow
                key={s.user_id}
                className="cursor-pointer hover:bg-muted/50 transition-colors"
                onClick={() => setSelectedUser(s.user_id)}
              >
                <TableCell className="font-medium">{s.user_name}</TableCell>
                <TableCell>
                  <span className={`font-bold ${scoreColor(s.overall_score)}`}>
                    {s.overall_score}
                  </span>
                </TableCell>
                <TableCell>
                  <span className={scoreColor(s.velocity_score)}>{s.velocity_score}</span>
                </TableCell>
                <TableCell>
                  <span className={scoreColor(s.quality_score)}>{s.quality_score}</span>
                </TableCell>
                <TableCell>
                  <span className={scoreColor(s.collaboration_score)}>{s.collaboration_score}</span>
                </TableCell>
                <TableCell>
                  <span className={scoreColor(s.learning_score)}>{s.learning_score}</span>
                </TableCell>
              </TableRow>
            ))}
            {sortedScores.length === 0 && (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-12 text-muted-foreground">
                  No workforce scores available
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </Card>

      {/* User Detail Dialog */}
      <Dialog open={!!selectedUser} onOpenChange={(open) => !open && setSelectedUser(null)}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>
              {detailLoading ? (
                <Skeleton className="h-6 w-40" />
              ) : (
                userDetail?.user_name ?? 'User Score Detail'
              )}
            </DialogTitle>
          </DialogHeader>
          {detailLoading ? (
            <div className="space-y-4 pt-2">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-8 w-full" />
              ))}
            </div>
          ) : userDetail ? (
            <div className="space-y-4 pt-2">
              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">Trend:</span>
                {trendIcon(userDetail.score_trend)}
                <span className="text-sm capitalize">{userDetail.score_trend}</span>
              </div>
              <div className="flex items-center justify-center">
                <HealthGauge value={userDetail.overall_score} label="Overall" />
              </div>
              {[
                { label: 'Velocity', value: userDetail.velocity_score },
                { label: 'Quality', value: userDetail.quality_score },
                { label: 'Collaboration', value: userDetail.collaboration_score },
                { label: 'Learning', value: userDetail.learning_score },
                { label: 'Self-Sufficiency', value: userDetail.self_sufficiency_score },
              ].map((dim) => (
                <div key={dim.label}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium">{dim.label}</span>
                    <span className={`text-sm font-bold ${scoreColor(dim.value)}`}>
                      {dim.value}
                    </span>
                  </div>
                  <Progress
                    value={dim.value}
                    className={`h-2 ${dim.value > 80 ? '[&>div]:bg-emerald-500' : dim.value >= 60 ? '[&>div]:bg-amber-500' : '[&>div]:bg-red-500'}`}
                  />
                </div>
              ))}
              <div className="flex gap-3 pt-2">
                <div className="flex-1 text-center p-3 rounded-lg bg-muted/50">
                  <p className="text-xs text-muted-foreground">Percentile</p>
                  <p className="text-lg font-bold">{userDetail.percentile_rank}%</p>
                </div>
                <div className="flex-1 text-center p-3 rounded-lg bg-muted/50">
                  <p className="text-xs text-muted-foreground">Attrition Risk</p>
                  <p className={`text-lg font-bold ${scoreColor(100 - userDetail.attrition_risk_score)}`}>
                    {userDetail.attrition_risk_score}
                  </p>
                </div>
                <div className="flex-1 text-center p-3 rounded-lg bg-muted/50">
                  <p className="text-xs text-muted-foreground">Burnout Risk</p>
                  <p className={`text-lg font-bold ${scoreColor(100 - userDetail.burnout_risk_score)}`}>
                    {userDetail.burnout_risk_score}
                  </p>
                </div>
              </div>
            </div>
          ) : null}
        </DialogContent>
      </Dialog>
    </div>
  );
}

// ─── Manager Rankings Tab ───────────────────────────────────────────

function ManagerRankingsTab() {
  const { data: rankings, isLoading } = useQuery({
    queryKey: queryKeys.workforce.managerRankings,
    queryFn: () => workforceService.getManagerRankings(),
  });

  if (isLoading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-20 w-full rounded-xl" />
        ))}
      </div>
    );
  }

  const sorted = [...(rankings ?? [])].sort(
    (a, b) => b.effectiveness_score - a.effectiveness_score
  );

  function medalIcon(rank: number) {
    if (rank === 0) return <Medal className="w-6 h-6 text-amber-400" />;
    if (rank === 1) return <Medal className="w-6 h-6 text-slate-400" />;
    if (rank === 2) return <Medal className="w-6 h-6 text-amber-700" />;
    return (
      <span className="w-6 h-6 flex items-center justify-center text-sm font-bold text-muted-foreground">
        {rank + 1}
      </span>
    );
  }

  return (
    <div className="space-y-3">
      {sorted.map((mgr, index) => (
        <motion.div
          key={mgr.manager_id}
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: index * 0.05 }}
        >
          <Card
            className={`transition-shadow hover:shadow-md ${index < 3 ? 'border-amber-500/20' : ''}`}
          >
            <CardContent className="p-4 flex items-center gap-4">
              <div className="flex-shrink-0">{medalIcon(index)}</div>
              <div className="flex-1 min-w-0">
                <p className="font-semibold truncate">{mgr.manager_name}</p>
                <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-muted-foreground mt-1">
                  <span>Team: {mgr.team_size}</span>
                  <span>Velocity: {mgr.team_velocity_avg.toFixed(1)}</span>
                  <span>Quality: {mgr.team_quality_avg.toFixed(1)}</span>
                </div>
              </div>
              <div className="flex-shrink-0 text-right">
                <p className={`text-xl font-bold ${scoreColor(mgr.effectiveness_score)}`}>
                  {mgr.effectiveness_score}
                </p>
                <p className="text-xs text-muted-foreground">Effectiveness</p>
              </div>
              <div className="flex-shrink-0 text-right hidden sm:block">
                <p className="text-sm font-medium">
                  {(mgr.escalation_resolution_rate * 100).toFixed(0)}%
                </p>
                <p className="text-xs text-muted-foreground">Resolution Rate</p>
              </div>
              <div className="flex-shrink-0 text-right hidden md:block">
                <p className="text-sm font-medium">
                  {mgr.team_satisfaction_score.toFixed(1)}
                </p>
                <p className="text-xs text-muted-foreground">Satisfaction</p>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      ))}
      {sorted.length === 0 && (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            No manager rankings available
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// ─── Attrition Risk Tab ─────────────────────────────────────────────

function AttritionRiskTab() {
  const [riskLevel, setRiskLevel] = useState<string>('all');

  const { data: risks, isLoading } = useQuery({
    queryKey: queryKeys.workforce.attritionRisk(riskLevel === 'all' ? undefined : riskLevel),
    queryFn: () =>
      workforceService.getAttritionRisk(riskLevel === 'all' ? undefined : riskLevel),
  });

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-10 w-48" />
        <div className="grid md:grid-cols-2 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-36 rounded-xl" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Filter */}
      <div className="flex items-center gap-3">
        <Label className="text-sm font-medium">Risk Level:</Label>
        <Select value={riskLevel} onValueChange={setRiskLevel}>
          <SelectTrigger className="w-40">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Levels</SelectItem>
            <SelectItem value="critical">Critical</SelectItem>
            <SelectItem value="high">High</SelectItem>
            <SelectItem value="medium">Medium</SelectItem>
            <SelectItem value="low">Low</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Risk Cards */}
      <div className="grid md:grid-cols-2 gap-4">
        {(risks ?? []).map((risk, index) => (
          <motion.div
            key={risk.user_id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
          >
            <Card>
              <CardContent className="p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <p className="font-semibold">{risk.user_name}</p>
                  <Badge className={riskBadgeColor(risk.risk_level)}>
                    {risk.risk_level}
                  </Badge>
                </div>
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm text-muted-foreground">Risk Score</span>
                    <span className="text-sm font-bold">{risk.risk_score}</span>
                  </div>
                  <Progress
                    value={risk.risk_score}
                    className={`h-2 ${riskProgressColor(risk.risk_level)}`}
                  />
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {risk.risk_factors.map((factor) => (
                    <Badge key={factor} variant="outline" className="text-xs">
                      {factor}
                    </Badge>
                  ))}
                </div>
                {risk.recommended_actions.length > 0 && (
                  <div className="pt-1 border-t">
                    <p className="text-xs text-muted-foreground mb-1">Recommended Actions:</p>
                    <ul className="text-xs space-y-0.5">
                      {risk.recommended_actions.slice(0, 3).map((action) => (
                        <li key={action} className="flex items-start gap-1">
                          <Info className="w-3 h-3 mt-0.5 flex-shrink-0 text-blue-400" />
                          {action}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>

      {(risks ?? []).length === 0 && (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            No attrition risks found for the selected filter
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// ─── Simulations Tab ────────────────────────────────────────────────

function SimulationsTab() {
  const [dialogOpen, setDialogOpen] = useState(false);
  type ScenarioType = 'team_merge' | 'role_change' | 'automation_replace' | 'reduction';
  const [scenarioType, setScenarioType] = useState<ScenarioType>('team_merge');
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');

  const { data: simulations, isLoading, refetch } = useQuery({
    queryKey: ['workforce', 'simulations'],
    queryFn: () => workforceService.getSimulations(),
  });

  const createMutation = useMutation({
    mutationFn: () =>
      workforceService.createSimulation({
        name,
        description: description || undefined,
        scenario_type: scenarioType,
        config: {},
      }),
    onSuccess: () => {
      toast.success('Simulation created successfully');
      setDialogOpen(false);
      setName('');
      setDescription('');
      refetch();
    },
    onError: (err) => toast.error(getApiErrorMessage(err)),
  });

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-10 w-48" />
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-24 w-full rounded-xl" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* New Simulation Button */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogTrigger asChild>
          <Button className="gap-2">
            <Plus className="w-4 h-4" />
            New Simulation
          </Button>
        </DialogTrigger>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create Workforce Simulation</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 pt-4">
            <div>
              <Label className="text-sm font-medium mb-2 block">Simulation Name</Label>
              <Input
                placeholder="e.g. Q3 Restructuring Plan"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </div>
            <div>
              <Label className="text-sm font-medium mb-2 block">Description (optional)</Label>
              <Input
                placeholder="Brief description of the scenario"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </div>
            <div>
              <Label className="text-sm font-medium mb-2 block">Scenario Type</Label>
              <Select value={scenarioType} onValueChange={(v) => setScenarioType(v as ScenarioType)}>
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="team_merge">Team Merge</SelectItem>
                  <SelectItem value="role_change">Role Change</SelectItem>
                  <SelectItem value="automation_replace">Automation Replace</SelectItem>
                  <SelectItem value="reduction">Reduction</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Button
              className="w-full"
              disabled={!name.trim() || createMutation.isPending}
              onClick={() => createMutation.mutate()}
            >
              {createMutation.isPending && (
                <Loader2 className="w-4 h-4 animate-spin mr-2" />
              )}
              Run Simulation
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Past Simulations */}
      <div className="space-y-3">
        {(simulations ?? []).map((sim, index) => (
          <motion.div
            key={sim.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
          >
            <Card>
              <CardContent className="p-4">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <p className="font-semibold">{sim.name}</p>
                    {sim.description && (
                      <p className="text-sm text-muted-foreground mt-0.5">
                        {sim.description}
                      </p>
                    )}
                  </div>
                  <div className="flex gap-2">
                    <Badge variant="outline">{sim.scenario_type.replace(/_/g, ' ')}</Badge>
                    {sim.is_draft && <Badge variant="secondary">Draft</Badge>}
                  </div>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <div className="p-2 rounded-lg bg-muted/50 text-center">
                    <p className="text-xs text-muted-foreground">Cost Change</p>
                    <p
                      className={`text-sm font-bold ${sim.projected_cost_change > 0 ? 'text-red-500' : 'text-emerald-500'}`}
                    >
                      {sim.projected_cost_change > 0 ? '+' : ''}
                      {sim.projected_cost_change.toFixed(1)}%
                    </p>
                  </div>
                  <div className="p-2 rounded-lg bg-muted/50 text-center">
                    <p className="text-xs text-muted-foreground">Productivity</p>
                    <p
                      className={`text-sm font-bold ${sim.projected_productivity_change >= 0 ? 'text-emerald-500' : 'text-red-500'}`}
                    >
                      {sim.projected_productivity_change > 0 ? '+' : ''}
                      {sim.projected_productivity_change.toFixed(1)}%
                    </p>
                  </div>
                  <div className="p-2 rounded-lg bg-muted/50 text-center">
                    <p className="text-xs text-muted-foreground">Affected</p>
                    <p className="text-sm font-bold">{sim.affected_employees}</p>
                  </div>
                  <div className="p-2 rounded-lg bg-muted/50 text-center">
                    <p className="text-xs text-muted-foreground">Risk Score</p>
                    <p className={`text-sm font-bold ${scoreColor(100 - sim.overall_risk_score)}`}>
                      {sim.overall_risk_score}
                    </p>
                  </div>
                </div>
                {sim.risk_factors.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mt-3">
                    {sim.risk_factors.map((f) => (
                      <Badge key={f} variant="outline" className="text-xs">
                        {f}
                      </Badge>
                    ))}
                  </div>
                )}
                <p className="text-xs text-muted-foreground mt-2">
                  Created {new Date(sim.created_at).toLocaleDateString()}
                </p>
              </CardContent>
            </Card>
          </motion.div>
        ))}
        {(simulations ?? []).length === 0 && (
          <Card>
            <CardContent className="py-12 text-center text-muted-foreground">
              <FlaskConical className="w-10 h-10 mx-auto mb-3 opacity-40" />
              <p>No simulations yet. Create one to forecast workforce changes.</p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}

// ─── Hiring Plan Tab ────────────────────────────────────────────────

function HiringPlanTab() {
  const { data: hiringPlan, isLoading } = useQuery({
    queryKey: queryKeys.workforce.hiringPlan,
    queryFn: () => workforceService.getHiringPlan(),
  });

  if (isLoading) {
    return (
      <Card>
        <CardContent className="py-8">
          <div className="space-y-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-12 w-full rounded-lg" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!hiringPlan) return null;

  return (
    <div className="space-y-4">
      {/* Summary Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-3xl font-bold text-primary">{hiringPlan.total_recommended_hires}</p>
            <p className="text-sm text-muted-foreground">Recommended Hires</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-3xl font-bold">{hiringPlan.estimated_timeline_months}</p>
            <p className="text-sm text-muted-foreground">Months Timeline</p>
          </CardContent>
        </Card>
        <Card className="col-span-2 lg:col-span-1">
          <CardContent className="p-4 text-center">
            <p className="text-3xl font-bold">
              ${(hiringPlan.estimated_cost / 1000).toFixed(0)}k
            </p>
            <p className="text-sm text-muted-foreground">Estimated Cost</p>
          </CardContent>
        </Card>
      </div>

      {/* Hiring Recommendations Table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Hiring Recommendations</CardTitle>
          <CardDescription>
            Skill gaps identified with recommended hiring actions
          </CardDescription>
        </CardHeader>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Skill / Role</TableHead>
              <TableHead>Priority</TableHead>
              <TableHead>Category</TableHead>
              <TableHead>Coverage Gap</TableHead>
              <TableHead>Recommended Hires</TableHead>
              <TableHead>Impact</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {hiringPlan.recommendations.map((rec) => (
              <TableRow key={rec.skill_name}>
                <TableCell className="font-medium">{rec.skill_name}</TableCell>
                <TableCell>
                  <Badge className={urgencyBadgeColor(rec.urgency)}>{rec.urgency}</Badge>
                </TableCell>
                <TableCell className="capitalize">{rec.skill_category}</TableCell>
                <TableCell>
                  <div className="flex items-center gap-2">
                    <Progress
                      value={rec.current_coverage}
                      className="w-16 h-2 [&>div]:bg-blue-500"
                    />
                    <span className="text-sm text-muted-foreground">
                      {rec.current_coverage}% / {rec.required_coverage}%
                    </span>
                  </div>
                </TableCell>
                <TableCell className="font-medium">{rec.recommended_hires}</TableCell>
                <TableCell className="text-sm text-muted-foreground max-w-[200px] truncate">
                  {rec.estimated_impact}
                </TableCell>
              </TableRow>
            ))}
            {hiringPlan.recommendations.length === 0 && (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-12 text-muted-foreground">
                  No hiring recommendations at this time
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </Card>

      {/* Priority Order */}
      {hiringPlan.priority_order.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Priority Order</CardTitle>
            <CardDescription>Recommended hiring sequence</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {hiringPlan.priority_order.map((skill, idx) => (
                <Badge key={skill} variant="outline" className="gap-1.5">
                  <span className="text-xs font-bold text-primary">{idx + 1}</span>
                  {skill}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// ─── Main Page ──────────────────────────────────────────────────────

const tabConfig = [
  { value: 'org-health', label: 'Org Health', icon: Heart },
  { value: 'scores', label: 'Workforce Scores', icon: Users },
  { value: 'managers', label: 'Manager Rankings', icon: Trophy },
  { value: 'attrition', label: 'Attrition Risk', icon: AlertTriangle },
  { value: 'simulations', label: 'Simulations', icon: FlaskConical },
  { value: 'hiring', label: 'Hiring Plan', icon: Briefcase },
];

export default function WorkforcePage() {
  const [activeTab, setActiveTab] = useState('org-health');

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <h1 className="text-2xl lg:text-3xl font-bold">Workforce Intelligence</h1>
            <p className="text-muted-foreground mt-1">
              Monitor organizational health, performance scores, and workforce planning
            </p>
          </div>
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="flex-wrap h-auto gap-1">
            {tabConfig.map((tab) => {
              const Icon = tab.icon;
              return (
                <TabsTrigger key={tab.value} value={tab.value} className="gap-1.5">
                  <Icon className="w-4 h-4" />
                  <span className="hidden sm:inline">{tab.label}</span>
                </TabsTrigger>
              );
            })}
          </TabsList>

          <TabsContent value="org-health" className="mt-6">
            <OrgHealthTab />
          </TabsContent>

          <TabsContent value="scores" className="mt-6">
            <WorkforceScoresTab />
          </TabsContent>

          <TabsContent value="managers" className="mt-6">
            <ManagerRankingsTab />
          </TabsContent>

          <TabsContent value="attrition" className="mt-6">
            <AttritionRiskTab />
          </TabsContent>

          <TabsContent value="simulations" className="mt-6">
            <SimulationsTab />
          </TabsContent>

          <TabsContent value="hiring" className="mt-6">
            <HiringPlanTab />
          </TabsContent>
        </Tabs>
      </div>
    </DashboardLayout>
  );
}

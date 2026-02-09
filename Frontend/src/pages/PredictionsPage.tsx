import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import {
  BrainCircuit,
  TrendingUp,
  TrendingDown,
  Minus,
  Target,
  CheckCircle2,
  AlertTriangle,
  Search,
  Users,
  BarChart3,
  CalendarClock,
  ArrowRight,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import DashboardLayout from '@/components/layout/DashboardLayout';
import { predictionsService } from '@/services/predictions.service';
import { queryKeys } from '@/hooks/useApi';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

// ─── Types aligned with actual API shapes ───────────────────────────

type TaskPredictionData = Awaited<ReturnType<typeof predictionsService.getTaskPrediction>>;

// ─── Urgency helpers ────────────────────────────────────────────────

const urgencyOrder: Record<string, number> = { critical: 0, high: 1, medium: 2, low: 3 };

function urgencyBadgeClass(urgency: string): string {
  switch (urgency) {
    case 'critical':
    case 'high':
      return 'bg-red-500/15 text-red-600 border-red-500/30';
    case 'medium':
      return 'bg-amber-500/15 text-amber-600 border-amber-500/30';
    case 'low':
      return 'bg-emerald-500/15 text-emerald-600 border-emerald-500/30';
    default:
      return '';
  }
}

function TrendIcon({ trend }: { trend: string }) {
  if (trend === 'increasing' || trend === 'up') return <TrendingUp className="w-3 h-3" />;
  if (trend === 'decreasing' || trend === 'down') return <TrendingDown className="w-3 h-3" />;
  return <Minus className="w-3 h-3" />;
}

function trendBadgeClass(trend: string): string {
  if (trend === 'increasing' || trend === 'up') return 'bg-emerald-500/15 text-emerald-600 border-emerald-500/30';
  if (trend === 'decreasing' || trend === 'down') return 'bg-red-500/15 text-red-600 border-red-500/30';
  return 'bg-muted text-muted-foreground';
}

// ─── Component ──────────────────────────────────────────────────────

export default function PredictionsPage() {
  const [taskIdInput, setTaskIdInput] = useState('');
  const [lookupTaskId, setLookupTaskId] = useState<string | null>(null);
  const [accuracyDays] = useState<number>(30);
  const [teamId] = useState<string>('default');

  // ── Queries ──────────────────────────────────────────────────────

  const { data: accuracy, isLoading: accuracyLoading } = useQuery({
    queryKey: queryKeys.predictions.accuracy(accuracyDays),
    queryFn: () => predictionsService.getPredictionAccuracy(accuracyDays),
  });

  const { data: velocity, isLoading: velocityLoading } = useQuery({
    queryKey: queryKeys.predictions.teamVelocity(teamId),
    queryFn: () => predictionsService.getTeamVelocity(teamId),
  });

  const { data: hiring, isLoading: hiringLoading } = useQuery({
    queryKey: queryKeys.predictions.hiring,
    queryFn: () => predictionsService.getHiringPredictions(),
  });

  const {
    data: taskPrediction,
    isLoading: taskPredictionLoading,
    isError: taskPredictionError,
  } = useQuery({
    queryKey: queryKeys.predictions.task(lookupTaskId ?? ''),
    queryFn: () => predictionsService.getTaskPrediction(lookupTaskId!),
    enabled: !!lookupTaskId,
  });

  // ── Derived data ─────────────────────────────────────────────────

  const forecastData = velocity?.snapshots?.map((s) => ({
    week: s.period_start,
    predicted: s.velocity,
    lower_bound: Math.round(s.velocity * 0.8),
    upper_bound: Math.round(s.velocity * 1.2),
  })) ?? [];

  const currentVelocity = velocity?.snapshots?.length
    ? velocity.snapshots[velocity.snapshots.length - 1].velocity
    : 0;
  const predictedVelocity = velocity?.forecasted_velocity ?? 0;
  const velocityTrend = velocity?.trend ?? 'stable';

  const sortedHiring = [...(Array.isArray(hiring) ? hiring : [])].sort(
    (a, b) => (urgencyOrder[a.urgency] ?? 99) - (urgencyOrder[b.urgency] ?? 99),
  );

  // ── Handlers ─────────────────────────────────────────────────────

  function handleTaskLookup(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = taskIdInput.trim();
    if (trimmed) setLookupTaskId(trimmed);
  }

  // ── Render helpers ───────────────────────────────────────────────

  function formatDate(iso?: string) {
    if (!iso) return '--';
    return new Date(iso).toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* ── Header ──────────────────────────────────────────────── */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <div className="flex flex-col gap-1">
            <h1 className="text-2xl lg:text-3xl font-bold flex items-center gap-2">
              <BrainCircuit className="w-7 h-7 text-primary" />
              Predictions & Forecasting
            </h1>
            <p className="text-muted-foreground">
              AI-driven forecasts for task completion, team velocity, and workforce planning
            </p>
          </div>
        </motion.div>

        {/* ── Accuracy Overview ───────────────────────────────────── */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 }}
        >
          <Card>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-lg">Prediction Accuracy</CardTitle>
                  <CardDescription>
                    Model performance over the last {accuracy?.period_days ?? accuracyDays} days
                  </CardDescription>
                </div>
                <Target className="w-5 h-5 text-muted-foreground" />
              </div>
            </CardHeader>
            <CardContent>
              {accuracyLoading ? (
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
                  {Array.from({ length: 4 }).map((_, i) => (
                    <Skeleton key={i} className="h-20 rounded-lg" />
                  ))}
                </div>
              ) : (
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
                  {/* P50 Accuracy */}
                  <div className="text-center">
                    <p className="text-4xl font-bold text-primary">
                      {Math.round(accuracy?.p50_accuracy ?? 0)}%
                    </p>
                    <p className="text-sm text-muted-foreground mt-1">P50 Accuracy</p>
                  </div>

                  {/* P90 Accuracy */}
                  <div className="text-center">
                    <p className="text-4xl font-bold">
                      {Math.round(accuracy?.p90_accuracy ?? 0)}%
                    </p>
                    <p className="text-sm text-muted-foreground mt-1">P90 Accuracy</p>
                  </div>

                  {/* Total Predictions */}
                  <div className="text-center">
                    <p className="text-4xl font-bold">
                      {accuracy?.total_predictions?.toLocaleString() ?? '0'}
                    </p>
                    <p className="text-sm text-muted-foreground mt-1">Total Predictions</p>
                  </div>

                  {/* Mean Absolute Error */}
                  <div className="text-center">
                    <p className="text-4xl font-bold">
                      {accuracy?.mean_absolute_error_days != null
                        ? `${accuracy.mean_absolute_error_days.toFixed(1)}d`
                        : '--'}
                    </p>
                    <p className="text-sm text-muted-foreground mt-1">Mean Abs. Error</p>
                  </div>
                </div>
              )}

              {/* Model version badge */}
              {accuracy?.model_version && (
                <div className="flex items-center gap-2 mt-4 pt-4 border-t">
                  <Badge variant="secondary">Model {accuracy.model_version}</Badge>
                  {accuracy.last_retrained && (
                    <span className="text-xs text-muted-foreground">
                      Last retrained {formatDate(accuracy.last_retrained)}
                    </span>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>

        {/* ── Team Velocity Forecast ─────────────────────────────── */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <Card>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-lg">Team Velocity Forecast</CardTitle>
                  <CardDescription>
                    Predicted velocity with confidence interval
                  </CardDescription>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className={trendBadgeClass(velocityTrend)}>
                    <TrendIcon trend={velocityTrend} />
                    {velocityTrend}
                  </Badge>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {velocityLoading ? (
                <Skeleton className="h-[320px] rounded-lg" />
              ) : (
                <>
                  {/* Velocity comparison */}
                  <div className="grid grid-cols-2 gap-4 mb-6">
                    <div className="rounded-lg border p-4">
                      <p className="text-sm text-muted-foreground">Current Velocity</p>
                      <p className="text-2xl font-bold">{currentVelocity}</p>
                      <p className="text-xs text-muted-foreground">tasks / sprint</p>
                    </div>
                    <div className="rounded-lg border p-4">
                      <p className="text-sm text-muted-foreground">Predicted Velocity</p>
                      <p className="text-2xl font-bold text-primary">{predictedVelocity}</p>
                      <p className="text-xs text-muted-foreground">tasks / sprint (forecast)</p>
                    </div>
                  </div>

                  {/* Area chart */}
                  <div className="h-[300px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={forecastData}>
                        <defs>
                          <linearGradient id="colorConfidence" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.15} />
                            <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0.02} />
                          </linearGradient>
                          <linearGradient id="colorPredicted" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.3} />
                            <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0} />
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                        <XAxis dataKey="week" stroke="hsl(var(--muted-foreground))" fontSize={12} />
                        <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: 'hsl(var(--card))',
                            border: '1px solid hsl(var(--border))',
                            borderRadius: '8px',
                          }}
                        />
                        {/* Confidence interval: upper bound */}
                        <Area
                          type="monotone"
                          dataKey="upper_bound"
                          name="Upper Bound"
                          stroke="none"
                          fillOpacity={1}
                          fill="url(#colorConfidence)"
                          strokeWidth={0}
                        />
                        {/* Confidence interval: lower bound (masks out bottom) */}
                        <Area
                          type="monotone"
                          dataKey="lower_bound"
                          name="Lower Bound"
                          stroke="hsl(var(--primary))"
                          strokeDasharray="4 4"
                          strokeOpacity={0.3}
                          fillOpacity={1}
                          fill="hsl(var(--card))"
                          strokeWidth={1}
                        />
                        {/* Predicted line */}
                        <Area
                          type="monotone"
                          dataKey="predicted"
                          name="Predicted"
                          stroke="hsl(var(--primary))"
                          fillOpacity={1}
                          fill="url(#colorPredicted)"
                          strokeWidth={2}
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        </motion.div>

        {/* ── Hiring Recommendations ─────────────────────────────── */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
        >
          <Card>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-lg">Hiring Recommendations</CardTitle>
                  <CardDescription>
                    AI-identified skill gaps and recommended hires
                  </CardDescription>
                </div>
                <Users className="w-5 h-5 text-muted-foreground" />
              </div>
            </CardHeader>
            <CardContent>
              {hiringLoading ? (
                <div className="space-y-3">
                  {Array.from({ length: 4 }).map((_, i) => (
                    <Skeleton key={i} className="h-12 rounded-lg" />
                  ))}
                </div>
              ) : sortedHiring.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <Users className="w-10 h-10 mx-auto mb-2 opacity-40" />
                  <p>No hiring recommendations at this time.</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Skill / Role</TableHead>
                      <TableHead>Urgency</TableHead>
                      <TableHead>Gap</TableHead>
                      <TableHead>Recommended Hires</TableHead>
                      <TableHead>Coverage</TableHead>
                      <TableHead>Est. Impact</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {sortedHiring.map((rec, index) => {
                      const coveragePct = rec.required_coverage > 0
                        ? Math.round((rec.current_coverage / rec.required_coverage) * 100)
                        : 0;
                      return (
                        <TableRow key={index}>
                          <TableCell className="font-medium">
                            <div>
                              <span>{rec.skill_name}</span>
                              <span className="block text-xs text-muted-foreground">
                                {rec.skill_category}
                              </span>
                            </div>
                          </TableCell>
                          <TableCell>
                            <Badge
                              variant="outline"
                              className={urgencyBadgeClass(rec.urgency)}
                            >
                              {rec.urgency}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <span className="font-mono text-sm">{rec.gap.toFixed(1)}</span>
                          </TableCell>
                          <TableCell>
                            <span className="font-mono text-sm">{rec.recommended_hires}</span>
                          </TableCell>
                          <TableCell>
                            <div className="flex items-center gap-2 min-w-[120px]">
                              <div className="flex-1 h-2 rounded-full bg-muted overflow-hidden">
                                <div
                                  className="h-full rounded-full bg-primary transition-all"
                                  style={{ width: `${Math.min(coveragePct, 100)}%` }}
                                />
                              </div>
                              <span className="text-xs text-muted-foreground w-10 text-right">
                                {coveragePct}%
                              </span>
                            </div>
                          </TableCell>
                          <TableCell>
                            <span className="text-sm">{rec.estimated_impact}</span>
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </motion.div>

        {/* ── Task Prediction Lookup ─────────────────────────────── */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <Card>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-lg">Task Prediction Lookup</CardTitle>
                  <CardDescription>
                    Enter a task ID to view its AI-predicted completion timeline
                  </CardDescription>
                </div>
                <CalendarClock className="w-5 h-5 text-muted-foreground" />
              </div>
            </CardHeader>
            <CardContent>
              {/* Search form */}
              <form onSubmit={handleTaskLookup} className="flex gap-2 mb-6">
                <Input
                  placeholder="Enter task ID (e.g. TASK-1234)"
                  value={taskIdInput}
                  onChange={(e) => setTaskIdInput(e.target.value)}
                  className="max-w-sm"
                />
                <Button type="submit" disabled={!taskIdInput.trim()} className="gap-2">
                  <Search className="w-4 h-4" />
                  Predict
                </Button>
              </form>

              {/* Results */}
              {lookupTaskId && (
                <div>
                  {taskPredictionLoading && (
                    <div className="space-y-4">
                      <Skeleton className="h-6 w-48" />
                      <div className="grid grid-cols-3 gap-4">
                        {Array.from({ length: 3 }).map((_, i) => (
                          <Skeleton key={i} className="h-20 rounded-lg" />
                        ))}
                      </div>
                      <Skeleton className="h-16 rounded-lg" />
                    </div>
                  )}

                  {taskPredictionError && (
                    <div className="flex items-center gap-2 text-destructive py-4">
                      <AlertTriangle className="w-5 h-5" />
                      <span>Failed to load prediction for task "{lookupTaskId}". Please verify the task ID and try again.</span>
                    </div>
                  )}

                  {taskPrediction && !taskPredictionLoading && (
                    <TaskPredictionResult prediction={taskPrediction} formatDate={formatDate} />
                  )}
                </div>
              )}

              {!lookupTaskId && (
                <div className="text-center py-8 text-muted-foreground">
                  <BarChart3 className="w-10 h-10 mx-auto mb-2 opacity-40" />
                  <p>Enter a task ID above to get its AI completion prediction.</p>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </DashboardLayout>
  );
}

// ─── Task Prediction Result Sub-component ─────────────────────────────

function TaskPredictionResult({
  prediction,
  formatDate,
}: {
  prediction: TaskPredictionData;
  formatDate: (iso?: string) => string;
}) {
  const confidencePct = Math.round(prediction.confidence * 100);

  // Build the timeline markers from P25 / P50 / P90
  const timelineMarkers = [
    { label: 'P25 (Optimistic)', date: prediction.predicted_date_p25, position: 15 },
    { label: 'P50 (Most Likely)', date: prediction.predicted_date_p50, position: 50 },
    { label: 'P90 (Conservative)', date: prediction.predicted_date_p90, position: 85 },
  ].filter((m) => m.date);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      {/* Confidence + task info */}
      <div className="flex items-center gap-4 flex-wrap">
        <Badge variant="secondary" className="text-base px-3 py-1">
          Task: {prediction.task_id}
        </Badge>
        <div className="flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-primary" />
          <span className="font-medium">Confidence:</span>
          <span
            className={`text-lg font-bold ${
              confidencePct >= 75
                ? 'text-emerald-600'
                : confidencePct >= 50
                  ? 'text-amber-600'
                  : 'text-red-600'
            }`}
          >
            {confidencePct}%
          </span>
        </div>
        {prediction.risk_score != null && (
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-500" />
            <span className="text-sm text-muted-foreground">
              Risk score: {(prediction.risk_score * 100).toFixed(0)}%
            </span>
          </div>
        )}
      </div>

      {/* Timeline visualization */}
      {timelineMarkers.length > 0 && (
        <div className="rounded-lg border p-4">
          <p className="text-sm font-medium mb-4">Predicted Completion Timeline</p>
          <div className="relative">
            {/* Track */}
            <div className="h-2 rounded-full bg-muted w-full" />
            {/* Gradient fill between first and last marker */}
            <div
              className="absolute top-0 h-2 rounded-full bg-gradient-to-r from-emerald-500 via-amber-400 to-red-400"
              style={{
                left: `${timelineMarkers[0]?.position ?? 0}%`,
                width: `${(timelineMarkers[timelineMarkers.length - 1]?.position ?? 100) - (timelineMarkers[0]?.position ?? 0)}%`,
              }}
            />
            {/* Markers */}
            {timelineMarkers.map((marker, i) => (
              <div
                key={i}
                className="absolute -top-1"
                style={{ left: `${marker.position}%`, transform: 'translateX(-50%)' }}
              >
                <div className="w-4 h-4 rounded-full border-2 border-background bg-primary shadow-sm" />
              </div>
            ))}
          </div>
          {/* Labels below track */}
          <div className="relative mt-4 h-12">
            {timelineMarkers.map((marker, i) => (
              <div
                key={i}
                className="absolute text-center"
                style={{
                  left: `${marker.position}%`,
                  transform: 'translateX(-50%)',
                  width: 'max-content',
                }}
              >
                <p className="text-xs font-medium">{marker.label}</p>
                <p className="text-xs text-muted-foreground">{formatDate(marker.date)}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Date cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="rounded-lg border p-4 text-center">
          <p className="text-xs text-muted-foreground mb-1">P25 (Optimistic)</p>
          <p className="text-lg font-semibold text-emerald-600">
            {formatDate(prediction.predicted_date_p25)}
          </p>
        </div>
        <div className="rounded-lg border p-4 text-center bg-primary/5">
          <p className="text-xs text-muted-foreground mb-1">P50 (Most Likely)</p>
          <p className="text-lg font-semibold text-primary">
            {formatDate(prediction.predicted_date_p50)}
          </p>
        </div>
        <div className="rounded-lg border p-4 text-center">
          <p className="text-xs text-muted-foreground mb-1">P90 (Conservative)</p>
          <p className="text-lg font-semibold text-red-600">
            {formatDate(prediction.predicted_date_p90)}
          </p>
        </div>
      </div>

      {/* Risk factors */}
      {prediction.risk_factors.length > 0 && (
        <div>
          <p className="text-sm font-medium mb-2">Risk Factors</p>
          <div className="flex flex-wrap gap-2">
            {prediction.risk_factors.map((factor, i) => (
              <Badge key={i} variant="outline" className="bg-red-500/10 text-red-600 border-red-500/20">
                <AlertTriangle className="w-3 h-3 mr-1" />
                {factor}
              </Badge>
            ))}
          </div>
        </div>
      )}

      {/* Recommendations */}
      {prediction.recommendations.length > 0 && (
        <div>
          <p className="text-sm font-medium mb-2">Recommendations</p>
          <ul className="space-y-1">
            {prediction.recommendations.map((rec, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-muted-foreground">
                <ArrowRight className="w-4 h-4 mt-0.5 shrink-0 text-primary" />
                {rec}
              </li>
            ))}
          </ul>
        </div>
      )}
    </motion.div>
  );
}

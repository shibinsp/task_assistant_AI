import { useState } from 'react';
import { motion } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import {
  TrendingUp,
  Users,
  CheckCircle2,
  Clock,
  Target,
  Download,
  PieChart,
  Activity,
  ArrowUpRight,
  ArrowDownRight,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import DashboardLayout from '@/components/layout/DashboardLayout';
import { dashboardService } from '@/services/dashboard.service';
import { queryKeys } from '@/hooks/useApi';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart as RePieChart,
  Pie,
  Cell,
  LineChart,
  Line,
} from 'recharts';

export default function AnalyticsPage() {
  const [timeRange, setTimeRange] = useState<'week' | 'month' | 'quarter'>('week');

  const weeksMap = { week: 4, month: 12, quarter: 26 };

  const { data: metrics } = useQuery({
    queryKey: queryKeys.dashboard.metrics(),
    queryFn: () => dashboardService.getMetrics(),
  });

  const { data: velocityRaw } = useQuery({
    queryKey: queryKeys.dashboard.velocity({ weeks: weeksMap[timeRange] }),
    queryFn: () => dashboardService.getVelocity({ weeks: weeksMap[timeRange] }),
  });

  const { data: teamWorkload } = useQuery({
    queryKey: [...queryKeys.dashboard.teamWorkload, timeRange],
    queryFn: () => dashboardService.getTeamWorkload(),
  });

  const { data: teamProductivity } = useQuery({
    queryKey: queryKeys.dashboard.teamProductivity({ period: timeRange } as Record<string, unknown>),
    queryFn: () => dashboardService.getTeamProductivity({ period: timeRange }),
  });

  // Build stats cards from real metrics
  const dynamicStatsCards = [
    {
      title: 'Tasks Completed',
      value: metrics?.completed_tasks?.toLocaleString() ?? '0',
      change: `${Math.round(metrics?.completion_rate ?? 0)}%`,
      trend: 'up' as const,
      icon: CheckCircle2,
      color: 'from-emerald-500 to-teal-500',
    },
    {
      title: 'Avg. Completion Time',
      value: metrics?.avg_completion_hours
        ? `${Math.round(metrics.avg_completion_hours * 10) / 10} hrs`
        : 'N/A',
      change: '',
      trend: 'down' as const,
      icon: Clock,
      color: 'from-blue-500 to-cyan-500',
    },
    {
      title: 'Team Velocity',
      value: velocityRaw?.avg_velocity?.toFixed(1) ?? '0',
      change: velocityRaw?.trend ?? 'stable',
      trend: 'up' as const,
      icon: TrendingUp,
      color: 'from-violet-500 to-purple-500',
    },
    {
      title: 'Sprint Progress',
      value: `${Math.round(metrics?.completion_rate ?? 0)}%`,
      change: 'On track',
      trend: 'up' as const,
      icon: Target,
      color: 'from-amber-500 to-orange-500',
    },
  ];

  // Map velocity data from API
  const velocityData = velocityRaw?.weeks?.map((w) => ({
    week: w.week,
    planned: w.planned,
    completed: w.completed,
  })) ?? [];

  // Derive task distribution from real metrics
  const taskDistribution = metrics ? [
    { name: 'Completed', value: metrics.completed_tasks ?? 0, color: '#10b981' },
    { name: 'In Progress', value: metrics.in_progress_tasks ?? 0, color: '#3b82f6' },
    { name: 'Pending', value: (metrics.total_tasks ?? 0) - (metrics.completed_tasks ?? 0) - (metrics.in_progress_tasks ?? 0), color: '#f59e0b' },
  ].filter(d => d.value > 0) : [];

  // Map team workload to performance format
  const teamWorkloadData = teamWorkload as Record<string, unknown> | undefined;
  const teamPerformance: Array<{ name: string; tasks: number; efficiency: number }> =
    Array.isArray(teamWorkloadData?.members)
      ? (teamWorkloadData.members as Array<{ name?: string; total_tasks?: number; completed_tasks?: number; completion_rate?: number }>).map((m) => ({
          name: m.name ?? 'Unknown',
          tasks: m.total_tasks ?? m.completed_tasks ?? 0,
          efficiency: Math.round(m.completion_rate ?? 0),
        }))
      : [];

  // Map productivity data from API (daily_breakdown)
  const productivityByHour: Array<{ hour: string; productivity: number }> =
    teamProductivity?.daily_breakdown
      ? teamProductivity.daily_breakdown.map((d) => ({
          hour: d.date,
          productivity: d.tasks_completed,
        }))
      : [];

  // Burndown derived from velocity data
  const burndownData = velocityData.length > 0
    ? velocityData.map((w, i) => {
        const total = velocityData[0]?.planned ?? 100;
        const remaining = total > 0 ? Math.round(((total - w.completed) / total) * 100) : 0;
        const idealRemaining = total > 0 ? Math.round(((velocityData.length - 1 - i) / (velocityData.length - 1)) * 100) : 0;
        return { day: w.week, ideal: idealRemaining, actual: Math.max(0, remaining) };
      })
    : [];

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <h1 className="text-2xl lg:text-3xl font-bold">Analytics</h1>
            <p className="text-muted-foreground mt-1">
              Track performance and gain insights into your team's productivity
            </p>
          </div>
          <div className="flex gap-2">
            <Tabs value={timeRange} onValueChange={(v) => setTimeRange(v as typeof timeRange)}>
              <TabsList>
                <TabsTrigger value="week">Week</TabsTrigger>
                <TabsTrigger value="month">Month</TabsTrigger>
                <TabsTrigger value="quarter">Quarter</TabsTrigger>
              </TabsList>
            </Tabs>
            <Button variant="outline" className="gap-2">
              <Download className="w-4 h-4" />
              Export
            </Button>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {dynamicStatsCards.map((card, index) => {
            const Icon = card.icon;
            const isPositive = card.trend === 'up';
            
            return (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                <Card className="hover-lift">
                  <CardContent className="p-4 lg:p-6">
                    <div className="flex items-start justify-between">
                      <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${card.color} flex items-center justify-center`}>
                        <Icon className="w-5 h-5 text-white" />
                      </div>
                      <div className={`flex items-center gap-1 text-xs ${
                        isPositive ? 'text-emerald-500' : 'text-red-500'
                      }`}>
                        {isPositive ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
                        {card.change}
                      </div>
                    </div>
                    <div className="mt-4">
                      <p className="text-2xl lg:text-3xl font-bold">{card.value}</p>
                      <p className="text-sm text-muted-foreground">{card.title}</p>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            );
          })}
        </div>

        {/* Charts Row 1 */}
        <div className="grid lg:grid-cols-2 gap-6">
          {/* Velocity Chart */}
          <Card>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-lg">Sprint Velocity</CardTitle>
                  <CardDescription>Planned vs completed tasks per sprint</CardDescription>
                </div>
                <Badge variant="secondary" className="gap-1">
                  <TrendingUp className="w-3 h-3" />
                  +8.3%
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="h-[280px]">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={velocityData}>
                    <defs>
                      <linearGradient id="colorPlanned" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0}/>
                      </linearGradient>
                      <linearGradient id="colorCompleted" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
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
                    <Area 
                      type="monotone" 
                      dataKey="planned" 
                      name="Planned"
                      stroke="hsl(var(--primary))" 
                      fillOpacity={1} 
                      fill="url(#colorPlanned)" 
                      strokeWidth={2}
                    />
                    <Area 
                      type="monotone" 
                      dataKey="completed" 
                      name="Completed"
                      stroke="#10b981" 
                      fillOpacity={1} 
                      fill="url(#colorCompleted)" 
                      strokeWidth={2}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          {/* Task Distribution */}
          <Card>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-lg">Task Distribution</CardTitle>
                  <CardDescription>Current task status breakdown</CardDescription>
                </div>
                <PieChart className="w-5 h-5 text-muted-foreground" />
              </div>
            </CardHeader>
            <CardContent>
              {taskDistribution.length === 0 ? (
                <div className="h-[280px] flex items-center justify-center text-sm text-muted-foreground">
                  No task data available yet
                </div>
              ) : (
                <div className="h-[280px] flex items-center">
                  <ResponsiveContainer width="100%" height="100%">
                    <RePieChart>
                      <Pie
                        data={taskDistribution}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={100}
                        paddingAngle={5}
                        dataKey="value"
                      >
                        {taskDistribution.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip
                        contentStyle={{
                          backgroundColor: 'hsl(var(--card))',
                          border: '1px solid hsl(var(--border))',
                          borderRadius: '8px',
                        }}
                      />
                    </RePieChart>
                  </ResponsiveContainer>
                  <div className="space-y-2 ml-4">
                    {taskDistribution.map((item, index) => {
                      const total = taskDistribution.reduce((s, d) => s + d.value, 0);
                      const pct = total > 0 ? Math.round((item.value / total) * 100) : 0;
                      return (
                        <div key={index} className="flex items-center gap-2">
                          <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }} />
                          <span className="text-sm">{item.name}</span>
                          <span className="text-sm text-muted-foreground">({pct}%)</span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Charts Row 2 */}
        <div className="grid lg:grid-cols-2 gap-6">
          {/* Burndown Chart */}
          <Card>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-lg">Sprint Burndown</CardTitle>
                  <CardDescription>Remaining work over time</CardDescription>
                </div>
                <Activity className="w-5 h-5 text-muted-foreground" />
              </div>
            </CardHeader>
            <CardContent>
              {burndownData.length === 0 ? (
                <div className="h-[250px] flex items-center justify-center text-sm text-muted-foreground">
                  No burndown data available
                </div>
              ) : (
                <div className="h-[250px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={burndownData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                      <XAxis dataKey="day" stroke="hsl(var(--muted-foreground))" fontSize={12} />
                      <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: 'hsl(var(--card))',
                          border: '1px solid hsl(var(--border))',
                          borderRadius: '8px',
                        }}
                      />
                      <Line
                        type="monotone"
                        dataKey="ideal"
                        name="Ideal"
                        stroke="hsl(var(--muted-foreground))"
                        strokeDasharray="5 5"
                        strokeWidth={2}
                        dot={false}
                      />
                      <Line
                        type="monotone"
                        dataKey="actual"
                        name="Actual"
                        stroke="hsl(var(--primary))"
                        strokeWidth={2}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Productivity by Hour */}
          <Card>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-lg">Productivity by Hour</CardTitle>
                  <CardDescription>When your team is most productive</CardDescription>
                </div>
                <Clock className="w-5 h-5 text-muted-foreground" />
              </div>
            </CardHeader>
            <CardContent>
              {productivityByHour.length === 0 ? (
                <div className="h-[250px] flex items-center justify-center text-sm text-muted-foreground">
                  No productivity data available
                </div>
              ) : (
                <div className="h-[250px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={productivityByHour}>
                      <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                      <XAxis dataKey="hour" stroke="hsl(var(--muted-foreground))" fontSize={12} />
                      <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: 'hsl(var(--card))',
                          border: '1px solid hsl(var(--border))',
                          borderRadius: '8px',
                        }}
                      />
                      <Bar
                        dataKey="productivity"
                        name="Productivity %"
                        fill="hsl(var(--primary))"
                        radius={[4, 4, 0, 0]}
                      />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Team Performance */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-lg">Team Performance</CardTitle>
                <CardDescription>Individual contributor metrics</CardDescription>
              </div>
              <Button variant="outline" size="sm" className="gap-2">
                <Users className="w-4 h-4" />
                View All
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {teamPerformance.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-8">
                No team performance data available yet
              </p>
            ) : (
              <div className="space-y-4">
                {teamPerformance.map((member, index) => (
                  <div key={index} className="flex items-center gap-4">
                    <Avatar className="w-10 h-10">
                      <AvatarFallback className="bg-primary/10 text-primary">
                        {member.name.charAt(0)}
                      </AvatarFallback>
                    </Avatar>
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-medium">{member.name}</span>
                        <span className="text-sm text-muted-foreground">
                          {member.tasks} tasks • {member.efficiency}% efficiency
                        </span>
                      </div>
                      <Progress value={member.efficiency} className="h-2" />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}

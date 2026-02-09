import { useEffect, useState } from 'react';
import { motion, type Variants } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import {
  TrendingUp,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Zap,
  Calendar,
  ArrowRight,
  Plus,
  Sparkles,
  Target,
  Bot,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Skeleton } from '@/components/ui/skeleton';
import DashboardLayout from '@/components/layout/DashboardLayout';
import { useAuthStore } from '@/store/authStore';
import { dashboardService } from '@/services/dashboard.service';
import { tasksService } from '@/services/tasks.service';
import { queryKeys } from '@/hooks/useApi';
import { mapTaskToFrontend } from '@/types/mappers';
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
} from 'recharts';

// Fallback chart data (used when API returns no velocity data)
const fallbackVelocityData = [
  { day: 'Mon', tasks: 0, completed: 0 },
  { day: 'Tue', tasks: 0, completed: 0 },
  { day: 'Wed', tasks: 0, completed: 0 },
  { day: 'Thu', tasks: 0, completed: 0 },
  { day: 'Fri', tasks: 0, completed: 0 },
];

const fallbackProductivityData = [
  { hour: '9AM', focus: 0 },
  { hour: '10AM', focus: 0 },
  { hour: '11AM', focus: 0 },
  { hour: '12PM', focus: 0 },
  { hour: '1PM', focus: 0 },
  { hour: '2PM', focus: 0 },
  { hour: '3PM', focus: 0 },
  { hour: '4PM', focus: 0 },
  { hour: '5PM', focus: 0 },
];

// AI Insights (static for now as there's no specific AI insights endpoint)
const aiInsights = [
  {
    type: 'recommendation',
    message: 'Team velocity is trending up. Consider increasing sprint capacity by 15%.',
    icon: TrendingUp,
    color: 'text-emerald-500',
  },
  {
    type: 'warning',
    message: '3 tasks are at risk of missing their deadline. Review priorities.',
    icon: AlertTriangle,
    color: 'text-amber-500',
  },
  {
    type: 'insight',
    message: 'Peak productivity hours are 10AM-12PM. Schedule focused work then.',
    icon: Target,
    color: 'text-blue-500',
  },
];

// Animation variants
const containerVariants: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1 },
  },
};

const itemVariants: Variants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.5, ease: [0.4, 0, 0.2, 1] },
  },
};

export default function Dashboard() {
  const [greeting, setGreeting] = useState('');
  const { user } = useAuthStore();

  useEffect(() => {
    const hour = new Date().getHours();
    if (hour < 12) setGreeting('Good morning');
    else if (hour < 18) setGreeting('Good afternoon');
    else setGreeting('Good evening');
  }, []);

  // Fetch dashboard metrics
  const { data: metrics, isLoading: metricsLoading, error: metricsError } = useQuery({
    queryKey: queryKeys.dashboard.metrics(),
    queryFn: () => dashboardService.getMetrics(),
  });

  // Fetch recent tasks
  const { data: tasksData, isLoading: tasksLoading } = useQuery({
    queryKey: queryKeys.tasks.list({ limit: 5 }),
    queryFn: () => tasksService.list({ limit: 5 }),
  });

  // Fetch velocity data
  const { data: velocityRaw } = useQuery({
    queryKey: queryKeys.dashboard.velocity({ weeks: 4 }),
    queryFn: () => dashboardService.getVelocity({ weeks: 4 }),
  });

  const recentTasks = (tasksData?.tasks ?? []).map(mapTaskToFrontend);

  // Build stats cards from real metrics
  const statsCards = [
    {
      title: 'Tasks Completed',
      value: metrics?.completed_tasks?.toString() ?? '0',
      change: metrics?.completion_rate ? `${Math.round(metrics.completion_rate)}%` : '0%',
      trend: 'up' as const,
      icon: CheckCircle2,
      color: 'from-emerald-500 to-teal-500',
    },
    {
      title: 'In Progress',
      value: metrics?.in_progress_tasks?.toString() ?? '0',
      change: '',
      trend: 'down' as const,
      icon: Clock,
      color: 'from-blue-500 to-cyan-500',
    },
    {
      title: 'At Risk',
      value: (metrics?.overdue_tasks ?? 0 + (metrics?.blocked_tasks ?? 0)).toString(),
      change: metrics?.overdue_tasks ? `${metrics.overdue_tasks} overdue` : '',
      trend: 'up' as const,
      icon: AlertTriangle,
      color: 'from-amber-500 to-orange-500',
    },
    {
      title: 'Productivity Score',
      value: metrics?.completion_rate ? `${Math.round(metrics.completion_rate)}%` : '0%',
      change: '',
      trend: 'up' as const,
      icon: Zap,
      color: 'from-violet-500 to-purple-500',
    },
  ];

  // Map velocity API data to chart format
  const velocityData = velocityRaw?.weeks?.map((w) => ({
    day: w.week,
    tasks: w.planned,
    completed: w.completed,
  })) ?? fallbackVelocityData;

  const productivityData = fallbackProductivityData;

  if (metricsError) {
    return (
      <DashboardLayout>
        <Card className="p-8">
          <div className="flex flex-col items-center gap-4 text-center">
            <AlertTriangle className="w-12 h-12 text-amber-500" />
            <h2 className="text-lg font-semibold">Failed to load dashboard</h2>
            <p className="text-muted-foreground">{(metricsError as Error).message}</p>
            <Button onClick={() => window.location.reload()}>Retry</Button>
          </div>
        </Card>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="space-y-6"
      >
        {/* Header */}
        <motion.div variants={itemVariants} className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl lg:text-3xl font-bold">
              {greeting}, {user?.name?.split(' ')[0] ?? 'there'}!
            </h1>
            <p className="text-muted-foreground mt-1">
              Here's what's happening with your projects today.
            </p>
          </div>
          <div className="flex gap-3">
            <Button variant="outline" className="gap-2">
              <Calendar className="w-4 h-4" />
              <span className="hidden sm:inline">This Week</span>
            </Button>
            <Button className="gap-2">
              <Plus className="w-4 h-4" />
              New Task
            </Button>
          </div>
        </motion.div>

        {/* AI Insights Banner */}
        <motion.div variants={itemVariants}>
          <Card className="bg-gradient-to-r from-primary/10 via-primary/5 to-transparent border-primary/20">
            <CardContent className="p-4 flex items-center gap-4">
              <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center flex-shrink-0">
                <Sparkles className="w-5 h-5 text-primary" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-medium">AI Insight</p>
                <p className="text-sm text-muted-foreground truncate">
                  {metrics
                    ? `You have ${metrics.total_tasks ?? 0} total tasks, ${metrics.completed_tasks ?? 0} completed. Keep up the great work!`
                    : 'Loading insights...'}
                </p>
              </div>
              <Button variant="ghost" size="sm" className="flex-shrink-0 gap-1">
                View Details
                <ArrowRight className="w-4 h-4" />
              </Button>
            </CardContent>
          </Card>
        </motion.div>

        {/* Stats Grid */}
        <motion.div variants={itemVariants} className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {metricsLoading
            ? Array.from({ length: 4 }).map((_, i) => (
                <Card key={i}>
                  <CardContent className="p-4 lg:p-6">
                    <Skeleton className="h-10 w-10 rounded-xl mb-4" />
                    <Skeleton className="h-8 w-20 mb-2" />
                    <Skeleton className="h-4 w-24" />
                  </CardContent>
                </Card>
              ))
            : statsCards.map((card, index) => {
                const Icon = card.icon;
                const isPositive = card.trend === 'up' && card.title !== 'At Risk';
                return (
                  <Card key={index} className="hover-lift">
                    <CardContent className="p-4 lg:p-6">
                      <div className="flex items-start justify-between">
                        <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${card.color} flex items-center justify-center`}>
                          <Icon className="w-5 h-5 text-white" />
                        </div>
                        {card.change && (
                          <Badge
                            variant="outline"
                            className={`text-xs ${isPositive ? 'text-emerald-500 border-emerald-500/20' : card.title === 'At Risk' ? 'text-red-500 border-red-500/20' : 'text-amber-500 border-amber-500/20'}`}
                          >
                            {card.change}
                          </Badge>
                        )}
                      </div>
                      <div className="mt-4">
                        <p className="text-2xl lg:text-3xl font-bold">{card.value}</p>
                        <p className="text-sm text-muted-foreground">{card.title}</p>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
        </motion.div>

        {/* Charts Row */}
        <motion.div variants={itemVariants} className="grid lg:grid-cols-2 gap-6">
          {/* Task Velocity Chart */}
          <Card>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-lg">Task Velocity</CardTitle>
                  <CardDescription>Tasks created vs completed this week</CardDescription>
                </div>
                <Badge variant="secondary" className="gap-1">
                  <TrendingUp className="w-3 h-3" />
                  {velocityRaw?.trend ?? 'stable'}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="h-[250px]">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={velocityData}>
                    <defs>
                      <linearGradient id="colorTasks" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0}/>
                      </linearGradient>
                      <linearGradient id="colorCompleted" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="hsl(var(--success))" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="hsl(var(--success))" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
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
                    <Area type="monotone" dataKey="tasks" stroke="hsl(var(--primary))" fillOpacity={1} fill="url(#colorTasks)" strokeWidth={2} />
                    <Area type="monotone" dataKey="completed" stroke="hsl(var(--success))" fillOpacity={1} fill="url(#colorCompleted)" strokeWidth={2} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          {/* Productivity Chart */}
          <Card>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-lg">Productivity Heatmap</CardTitle>
                  <CardDescription>Focus levels throughout the day</CardDescription>
                </div>
                <Badge variant="secondary" className="gap-1">
                  <Target className="w-3 h-3" />
                  Peak: 11AM
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="h-[250px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={productivityData}>
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
                    <Bar dataKey="focus" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Bottom Row */}
        <motion.div variants={itemVariants} className="grid lg:grid-cols-3 gap-6">
          {/* Recent Tasks */}
          <Card className="lg:col-span-2">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">Recent Tasks</CardTitle>
                <Button variant="ghost" size="sm" className="gap-1">
                  View All
                  <ArrowRight className="w-4 h-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {tasksLoading ? (
                <div className="space-y-3">
                  {Array.from({ length: 5 }).map((_, i) => (
                    <div key={i} className="flex items-center gap-4 p-3">
                      <Skeleton className="w-2 h-2 rounded-full" />
                      <div className="flex-1">
                        <Skeleton className="h-4 w-3/4 mb-2" />
                        <Skeleton className="h-3 w-1/2" />
                      </div>
                      <Skeleton className="w-8 h-8 rounded-full" />
                    </div>
                  ))}
                </div>
              ) : (
                <div className="space-y-3">
                  {recentTasks.length === 0 ? (
                    <p className="text-sm text-muted-foreground text-center py-8">No tasks yet. Create your first task!</p>
                  ) : (
                    recentTasks.map((task) => (
                      <div
                        key={task.id}
                        className="flex items-center gap-4 p-3 rounded-xl hover:bg-muted/50 transition-colors cursor-pointer group"
                      >
                        <div className={`w-2 h-2 rounded-full flex-shrink-0 ${
                          task.status === 'done' ? 'bg-emerald-500' :
                          task.status === 'in-progress' ? 'bg-blue-500' :
                          task.status === 'review' ? 'bg-amber-500' :
                          'bg-slate-500'
                        }`} />
                        <div className="flex-1 min-w-0">
                          <p className="font-medium truncate group-hover:text-primary transition-colors">
                            {task.title}
                          </p>
                          <div className="flex items-center gap-2 mt-1">
                            <Badge variant="outline" className="text-[10px]">
                              {task.priority}
                            </Badge>
                            <span className="text-xs text-muted-foreground capitalize">
                              {task.status.replace('-', ' ')}
                            </span>
                          </div>
                        </div>
                        <Avatar className="w-8 h-8">
                          <AvatarFallback className="text-xs bg-primary/10 text-primary">
                            {task.assigneeName?.charAt(0) ?? '?'}
                          </AvatarFallback>
                        </Avatar>
                      </div>
                    ))
                  )}
                </div>
              )}
            </CardContent>
          </Card>

          {/* AI Insights */}
          <Card>
            <CardHeader className="pb-2">
              <div className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-primary" />
                <CardTitle className="text-lg">AI Insights</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {aiInsights.map((insight, index) => {
                  const Icon = insight.icon;
                  return (
                    <div key={index} className="flex gap-3">
                      <div className="w-8 h-8 rounded-lg bg-muted flex items-center justify-center flex-shrink-0">
                        <Icon className={`w-4 h-4 ${insight.color}`} />
                      </div>
                      <p className="text-sm text-muted-foreground leading-relaxed">
                        {insight.message}
                      </p>
                    </div>
                  );
                })}
              </div>
              <Button variant="outline" className="w-full mt-6 gap-2">
                <Bot className="w-4 h-4" />
                Ask AI Assistant
              </Button>
            </CardContent>
          </Card>
        </motion.div>
      </motion.div>
    </DashboardLayout>
  );
}

import { useState } from 'react';
import { motion } from 'framer-motion';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Brain,
  Plus,
  Star,
  Target,
  TrendingUp,
  BookOpen,
  Sparkles,
  AlertTriangle,
  CheckCircle2,
  Loader2,
  Lightbulb,
  GraduationCap,
  ShieldCheck,
  BarChart3,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
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
import DashboardLayout from '@/components/layout/DashboardLayout';
import { skillsService } from '@/services/skills.service';
import { queryKeys } from '@/hooks/useApi';
import { useAuthStore } from '@/store/authStore';
import { usePermissions } from '@/hooks/usePermissions';
import { getApiErrorMessage } from '@/lib/api-client';
import { toast } from 'sonner';
import {
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import type { ApiSkillCategory } from '@/types/api';

// ─── Priority helpers ────────────────────────────────────────────────

const priorityConfig: Record<string, { label: string; color: string; bg: string }> = {
  critical: { label: 'Critical', color: 'text-red-500', bg: 'bg-red-500/10' },
  growth: { label: 'Growth', color: 'text-amber-500', bg: 'bg-amber-500/10' },
  stretch: { label: 'Stretch', color: 'text-blue-500', bg: 'bg-blue-500/10' },
};

const categoryColors: Record<string, string> = {
  technical: '#8b5cf6',
  process: '#3b82f6',
  soft: '#10b981',
  domain: '#f59e0b',
  tool: '#ec4899',
  language: '#06b6d4',
};

const trendConfig: Record<string, { icon: typeof TrendingUp; color: string }> = {
  improving: { icon: TrendingUp, color: 'text-emerald-500' },
  stable: { icon: BarChart3, color: 'text-muted-foreground' },
  declining: { icon: TrendingUp, color: 'text-red-500' },
};

// ─── Self-Sufficiency Gauge ──────────────────────────────────────────

function SelfSufficiencyGauge({ score, isLoading }: { score: number; isLoading: boolean }) {
  const radius = 80;
  const circumference = 2 * Math.PI * radius;
  const dashOffset = circumference - (score / 100) * circumference;

  const getScoreColor = (s: number) => {
    if (s >= 80) return '#10b981';
    if (s >= 60) return '#f59e0b';
    return '#ef4444';
  };

  if (isLoading) {
    return (
      <div className="flex flex-col items-center gap-4">
        <Skeleton className="w-48 h-48 rounded-full" />
        <Skeleton className="h-4 w-32" />
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center">
      <div className="relative w-48 h-48">
        <svg className="w-48 h-48 -rotate-90" viewBox="0 0 200 200">
          <circle
            cx="100"
            cy="100"
            r={radius}
            fill="none"
            stroke="hsl(var(--muted))"
            strokeWidth="12"
          />
          <circle
            cx="100"
            cy="100"
            r={radius}
            fill="none"
            stroke={getScoreColor(score)}
            strokeWidth="12"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={dashOffset}
            className="transition-all duration-1000 ease-out"
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-4xl font-bold">{Math.round(score)}</span>
          <span className="text-sm text-muted-foreground">out of 100</span>
        </div>
      </div>
    </div>
  );
}

// ─── Star Level Indicator ────────────────────────────────────────────

function LevelStars({ level, max = 5 }: { level: number; max?: number }) {
  return (
    <div className="flex gap-0.5">
      {Array.from({ length: max }).map((_, i) => (
        <Star
          key={i}
          className={`w-4 h-4 ${
            i < level
              ? 'text-amber-400 fill-amber-400'
              : 'text-muted-foreground/30'
          }`}
        />
      ))}
    </div>
  );
}

// ─── Create Skill Dialog ─────────────────────────────────────────────

function CreateSkillDialog({ children }: { children: React.ReactNode }) {
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [name, setName] = useState('');
  const [category, setCategory] = useState<ApiSkillCategory>('technical');
  const [description, setDescription] = useState('');

  const mutation = useMutation({
    mutationFn: () =>
      skillsService.createSkill({ name, category, description: description || undefined }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.skills.catalog() });
      toast.success('Skill created successfully');
      setOpen(false);
      setName('');
      setCategory('technical');
      setDescription('');
    },
    onError: (err) => toast.error(getApiErrorMessage(err)),
  });

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{children}</DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create New Skill</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 pt-4">
          <div>
            <Label className="text-sm font-medium mb-2 block">Name</Label>
            <Input
              placeholder="e.g., React, Project Management"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>
          <div>
            <Label className="text-sm font-medium mb-2 block">Category</Label>
            <Select value={category} onValueChange={(v) => setCategory(v as ApiSkillCategory)}>
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="technical">Technical</SelectItem>
                <SelectItem value="process">Process</SelectItem>
                <SelectItem value="soft">Soft Skills</SelectItem>
                <SelectItem value="domain">Domain</SelectItem>
                <SelectItem value="tool">Tool</SelectItem>
                <SelectItem value="language">Language</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label className="text-sm font-medium mb-2 block">Description</Label>
            <Textarea
              placeholder="Brief description of the skill..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
            />
          </div>
          <Button
            className="w-full"
            disabled={!name.trim() || mutation.isPending}
            onClick={() => mutation.mutate()}
          >
            {mutation.isPending && <Loader2 className="w-4 h-4 animate-spin mr-2" />}
            Create Skill
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

// ─── Add User Skill Dialog ───────────────────────────────────────────

function AddUserSkillDialog({
  children,
  userId,
}: {
  children: React.ReactNode;
  userId: string;
}) {
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [skillId, setSkillId] = useState('');
  const [level, setLevel] = useState('3');

  const { data: catalogData } = useQuery({
    queryKey: queryKeys.skills.catalog(),
    queryFn: () => skillsService.listSkills({ limit: 200 }),
    enabled: open,
  });

  const mutation = useMutation({
    mutationFn: () =>
      skillsService.addUserSkill(userId, { skill_id: skillId, level: Number(level) }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.skills.userSkills(userId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.skills.graph(userId) });
      toast.success('Skill added successfully');
      setOpen(false);
      setSkillId('');
      setLevel('3');
    },
    onError: (err) => toast.error(getApiErrorMessage(err)),
  });

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{children}</DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add Skill</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 pt-4">
          <div>
            <Label className="text-sm font-medium mb-2 block">Skill</Label>
            <Select value={skillId} onValueChange={setSkillId}>
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Select a skill" />
              </SelectTrigger>
              <SelectContent>
                {catalogData?.skills?.map((s) => (
                  <SelectItem key={s.id} value={s.id}>
                    {s.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label className="text-sm font-medium mb-2 block">Current Level (1-5)</Label>
            <Select value={level} onValueChange={setLevel}>
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="1">1 - Beginner</SelectItem>
                <SelectItem value="2">2 - Basic</SelectItem>
                <SelectItem value="3">3 - Intermediate</SelectItem>
                <SelectItem value="4">4 - Advanced</SelectItem>
                <SelectItem value="5">5 - Expert</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <Button
            className="w-full"
            disabled={!skillId || mutation.isPending}
            onClick={() => mutation.mutate()}
          >
            {mutation.isPending && <Loader2 className="w-4 h-4 animate-spin mr-2" />}
            Add Skill
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

// ─── Main Page ───────────────────────────────────────────────────────

export default function SkillsPage() {
  const user = useAuthStore((s) => s.user);
  const userId = user?.id ?? '';
  const { canCreateSkills } = usePermissions();
  const [activeTab, setActiveTab] = useState('my-skills');
  const [velocityDays] = useState(90);
  const [catalogFilter, setCatalogFilter] = useState<string>('all');

  // ─── Queries ─────────────────────────────────────────────────────

  const { data: selfSufficiency, isLoading: selfSufficiencyLoading } = useQuery({
    queryKey: queryKeys.skills.selfSufficiency(userId),
    queryFn: () => skillsService.getSelfSufficiency(userId),
    enabled: !!userId,
  });

  const { data: userSkills, isLoading: userSkillsLoading } = useQuery({
    queryKey: queryKeys.skills.userSkills(userId),
    queryFn: () => skillsService.getUserSkills(userId),
    enabled: !!userId,
  });

  const { data: skillGraph, isLoading: graphLoading } = useQuery({
    queryKey: queryKeys.skills.graph(userId),
    queryFn: () => skillsService.getSkillGraph(userId),
    enabled: !!userId,
  });

  const { data: skillGaps, isLoading: gapsLoading } = useQuery({
    queryKey: queryKeys.skills.gaps(userId),
    queryFn: () => skillsService.getSkillGaps(userId),
    enabled: !!userId,
  });

  const { data: learningPaths, isLoading: pathsLoading } = useQuery({
    queryKey: queryKeys.skills.learningPaths(userId),
    queryFn: () => skillsService.getLearningPaths(userId),
    enabled: !!userId,
  });

  const { data: velocityData, isLoading: velocityLoading } = useQuery({
    queryKey: queryKeys.skills.velocity(userId, velocityDays),
    queryFn: () => skillsService.getSkillVelocity(userId, velocityDays),
    enabled: !!userId,
  });

  const { data: catalogData, isLoading: catalogLoading } = useQuery({
    queryKey: queryKeys.skills.catalog(
      catalogFilter !== 'all' ? { category: catalogFilter } : undefined
    ),
    queryFn: () =>
      skillsService.listSkills(
        catalogFilter !== 'all' ? { category: catalogFilter, limit: 200 } : { limit: 200 }
      ),
    enabled: canCreateSkills && activeTab === 'catalog',
  });

  // ─── Analyze Gaps Mutation ───────────────────────────────────────

  const [analysisResult, setAnalysisResult] = useState<{
    analysis: string;
    recommendations: string[];
  } | null>(null);

  const analyzeGapsMutation = useMutation({
    mutationFn: () => skillsService.analyzeSkillGaps(userId),
    onSuccess: (data) => {
      // The API returns ApiSkillGapSummary; extract recommended_focus as recommendations
      setAnalysisResult({
        analysis: `Found ${data.total_gaps} skill gaps, including ${data.critical_gaps} critical gaps requiring immediate attention.`,
        recommendations: data.recommended_focus ?? [],
      });
      toast.success('Gap analysis complete');
    },
    onError: (err) => toast.error(getApiErrorMessage(err)),
  });

  // ─── Derived data ───────────────────────────────────────────────

  const radarData =
    skillGraph?.top_skills?.map((s) => ({
      skill: s.name,
      level: s.level,
      fullMark: 5,
    })) ?? [];

  const userSkillsList = Array.isArray(userSkills) ? userSkills : [];

  // Build velocity chart data from history entries
  const velocityChartData =
    velocityData?.history?.map((entry) => ({
      date: new Date(entry.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      skill_name: entry.skill_name,
      level: entry.new_level,
    })) ?? [];

  // Group velocity by date for multi-line display
  const velocityByDate = velocityChartData.reduce<
    Record<string, Record<string, number>>
  >((acc, entry) => {
    if (!acc[entry.date]) acc[entry.date] = {};
    acc[entry.date][entry.skill_name] = entry.level;
    return acc;
  }, {});

  const velocitySkillNames = [
    ...new Set(velocityChartData.map((e) => e.skill_name)),
  ];

  const normalizedVelocityData = Object.entries(velocityByDate).map(([date, skills]) => ({
    date,
    ...skills,
  }));

  const velocityLineColors = ['#8b5cf6', '#3b82f6', '#10b981', '#f59e0b', '#ec4899', '#06b6d4'];

  // Group catalog skills by category
  const catalogSkills = catalogData?.skills ?? [];
  const groupedCatalog = catalogSkills.reduce<Record<string, typeof catalogSkills>>(
    (acc, skill) => {
      const cat = skill.category;
      if (!acc[cat]) acc[cat] = [];
      acc[cat].push(skill);
      return acc;
    },
    {}
  );

  // Self-sufficiency dimensions derived from API response
  const ssiData = selfSufficiency;
  const selfSuffDimensions = ssiData
    ? [
        { name: 'Self-Resolution', score: Math.round((ssiData.blockers_self_resolved / Math.max(ssiData.blockers_encountered, 1)) * 100) },
        { name: 'Collaboration', score: Math.round(ssiData.collaboration_score * 100) },
        { name: 'Help Balance', score: Math.round((ssiData.help_given_count / Math.max(ssiData.help_given_count + ssiData.help_received_count, 1)) * 100) },
        { name: 'Resolution Speed', score: Math.max(0, Math.round(100 - ssiData.avg_blocker_resolution_hours * 2)) },
      ]
    : [];

  // Sort gaps by priority (lower priority number = higher priority)
  const sortedGaps = [...(skillGaps?.gaps ?? [])].sort((a, b) => a.priority - b.priority);

  const learningPathsList = Array.isArray(learningPaths) ? learningPaths : [];

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <h1 className="text-2xl lg:text-3xl font-bold">Skills & Development</h1>
            <p className="text-muted-foreground mt-1">
              Track your skills, identify gaps, and accelerate your professional growth
            </p>
          </div>
          <div className="flex gap-2">
            <AddUserSkillDialog userId={userId}>
              <Button className="gap-2">
                <Plus className="w-4 h-4" />
                Add Skill
              </Button>
            </AddUserSkillDialog>
          </div>
        </div>

        {/* Self-Sufficiency Score */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <Card>
            <CardHeader className="pb-2">
              <div className="flex items-center gap-2">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500 to-purple-500 flex items-center justify-center">
                  <ShieldCheck className="w-5 h-5 text-white" />
                </div>
                <div>
                  <CardTitle className="text-lg">Self-Sufficiency Score</CardTitle>
                  <CardDescription>
                    How independently you resolve challenges and contribute to the team
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="flex flex-col lg:flex-row items-center gap-8">
                <SelfSufficiencyGauge
                  score={ssiData?.self_sufficiency_index ?? 0}
                  isLoading={selfSufficiencyLoading}
                />
                <div className="flex-1 w-full space-y-3">
                  {selfSufficiencyLoading ? (
                    Array.from({ length: 4 }).map((_, i) => (
                      <Skeleton key={i} className="h-10 w-full" />
                    ))
                  ) : (
                    selfSuffDimensions.map((dim) => (
                      <div key={dim.name} className="space-y-1">
                        <div className="flex items-center justify-between text-sm">
                          <span className="font-medium">{dim.name}</span>
                          <span className="text-muted-foreground">{dim.score}%</span>
                        </div>
                        <Progress value={dim.score} className="h-2" />
                      </div>
                    ))
                  )}
                  {ssiData && (
                    <div className="flex gap-4 pt-2 text-xs text-muted-foreground">
                      <span>Trend: <Badge variant="secondary" className="text-xs capitalize">{ssiData.trend}</Badge></span>
                      <span>Blockers resolved: {ssiData.blockers_self_resolved}/{ssiData.blockers_encountered}</span>
                    </div>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList>
            <TabsTrigger value="my-skills" className="gap-1.5">
              <Brain className="w-4 h-4" />
              My Skills
            </TabsTrigger>
            <TabsTrigger value="skill-gaps" className="gap-1.5">
              <Target className="w-4 h-4" />
              Skill Gaps
            </TabsTrigger>
            <TabsTrigger value="learning-paths" className="gap-1.5">
              <BookOpen className="w-4 h-4" />
              Learning Paths
            </TabsTrigger>
            {canCreateSkills && (
              <TabsTrigger value="catalog" className="gap-1.5">
                <GraduationCap className="w-4 h-4" />
                Catalog
              </TabsTrigger>
            )}
          </TabsList>

          {/* ─── My Skills Tab ─────────────────────────────────────── */}
          <TabsContent value="my-skills">
            <div className="grid lg:grid-cols-2 gap-6 mt-4">
              {/* Radar Chart */}
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.1 }}
              >
                <Card className="h-full">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-lg">Skill Radar</CardTitle>
                    <CardDescription>
                      Visual overview of your top skill levels
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {graphLoading ? (
                      <Skeleton className="h-[300px] w-full" />
                    ) : radarData.length === 0 ? (
                      <div className="h-[300px] flex items-center justify-center text-muted-foreground">
                        <div className="text-center">
                          <Brain className="w-12 h-12 mx-auto mb-2 opacity-30" />
                          <p>No skills recorded yet</p>
                          <p className="text-sm">Add skills to see your radar chart</p>
                        </div>
                      </div>
                    ) : (
                      <div className="h-[300px]">
                        <ResponsiveContainer width="100%" height="100%">
                          <RadarChart data={radarData} outerRadius="75%">
                            <PolarGrid stroke="hsl(var(--border))" />
                            <PolarAngleAxis
                              dataKey="skill"
                              tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }}
                            />
                            <PolarRadiusAxis
                              angle={90}
                              domain={[0, 5]}
                              tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 10 }}
                            />
                            <Radar
                              name="Level"
                              dataKey="level"
                              stroke="hsl(var(--primary))"
                              fill="hsl(var(--primary))"
                              fillOpacity={0.2}
                              strokeWidth={2}
                            />
                          </RadarChart>
                        </ResponsiveContainer>
                      </div>
                    )}
                    {skillGraph && (
                      <div className="flex gap-4 mt-2 text-xs text-muted-foreground justify-center">
                        <span>{skillGraph.skill_count} skills</span>
                        <span>Avg level: {skillGraph.avg_level.toFixed(1)}</span>
                        <span>Strongest: <span className="capitalize">{skillGraph.strongest_category}</span></span>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </motion.div>

              {/* Skills List */}
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.2 }}
              >
                <Card className="h-full">
                  <CardHeader className="pb-2">
                    <div className="flex items-center justify-between">
                      <div>
                        <CardTitle className="text-lg">My Skills</CardTitle>
                        <CardDescription>
                          All your assessed skills and proficiency levels
                        </CardDescription>
                      </div>
                      <AddUserSkillDialog userId={userId}>
                        <Button variant="outline" size="sm" className="gap-1.5">
                          <Plus className="w-4 h-4" />
                          Add
                        </Button>
                      </AddUserSkillDialog>
                    </div>
                  </CardHeader>
                  <CardContent>
                    {userSkillsLoading ? (
                      <div className="space-y-3">
                        {Array.from({ length: 5 }).map((_, i) => (
                          <Skeleton key={i} className="h-14 w-full" />
                        ))}
                      </div>
                    ) : userSkillsList.length === 0 ? (
                      <div className="py-8 text-center text-muted-foreground">
                        <Star className="w-12 h-12 mx-auto mb-2 opacity-30" />
                        <p>No skills added yet</p>
                        <p className="text-sm mt-1">Click "Add" to start tracking your skills</p>
                      </div>
                    ) : (
                      <div className="space-y-3 max-h-[340px] overflow-y-auto pr-1">
                        {userSkillsList.map((skill) => {
                          const trendInfo = trendConfig[skill.trend] ?? trendConfig.stable;
                          const TrendIcon = trendInfo.icon;
                          return (
                            <div
                              key={skill.id}
                              className="flex items-center gap-3 p-3 rounded-lg border border-border/50 hover:border-border transition-colors"
                            >
                              <div
                                className="w-2 h-10 rounded-full"
                                style={{
                                  backgroundColor:
                                    categoryColors[skill.skill_category] ?? '#6b7280',
                                }}
                              />
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2">
                                  <span className="font-medium text-sm truncate">
                                    {skill.skill_name}
                                  </span>
                                  {skill.is_certified && (
                                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
                                  )}
                                  <TrendIcon
                                    className={`w-3.5 h-3.5 shrink-0 ${trendInfo.color} ${
                                      skill.trend === 'declining' ? 'rotate-180' : ''
                                    }`}
                                  />
                                </div>
                                <div className="flex items-center gap-2 mt-0.5">
                                  <Badge
                                    variant="secondary"
                                    className="text-[10px] px-1.5 capitalize"
                                  >
                                    {skill.skill_category}
                                  </Badge>
                                  <span className="text-[10px] text-muted-foreground capitalize">
                                    {skill.source.replace('_', ' ')}
                                  </span>
                                </div>
                              </div>
                              <LevelStars level={skill.level} />
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </motion.div>
            </div>
          </TabsContent>

          {/* ─── Skill Gaps Tab ─────────────────────────────────────── */}
          <TabsContent value="skill-gaps">
            <div className="space-y-6 mt-4">
              {/* Analyze button */}
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-semibold">
                    Skill Gaps ({skillGaps?.total_gaps ?? 0})
                  </h2>
                  <p className="text-sm text-muted-foreground">
                    {skillGaps?.critical_gaps ?? 0} critical gaps require attention
                  </p>
                </div>
                <Button
                  variant="outline"
                  className="gap-2"
                  disabled={analyzeGapsMutation.isPending}
                  onClick={() => analyzeGapsMutation.mutate()}
                >
                  {analyzeGapsMutation.isPending ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Sparkles className="w-4 h-4" />
                  )}
                  Analyze Gaps
                </Button>
              </div>

              {/* AI Recommendations */}
              {analysisResult && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                >
                  <Card className="border-primary/20 bg-primary/5">
                    <CardHeader className="pb-2">
                      <div className="flex items-center gap-2">
                        <Lightbulb className="w-5 h-5 text-primary" />
                        <CardTitle className="text-base">AI Analysis</CardTitle>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm text-muted-foreground mb-3">
                        {analysisResult.analysis}
                      </p>
                      {analysisResult.recommendations.length > 0 && (
                        <div className="space-y-2">
                          <p className="text-sm font-medium">Recommendations:</p>
                          <ul className="space-y-1.5">
                            {analysisResult.recommendations.map((rec, i) => (
                              <li key={i} className="flex items-start gap-2 text-sm">
                                <CheckCircle2 className="w-4 h-4 text-primary shrink-0 mt-0.5" />
                                <span>{rec}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </motion.div>
              )}

              {/* Gaps Grid */}
              {gapsLoading ? (
                <div className="grid md:grid-cols-2 gap-4">
                  {Array.from({ length: 4 }).map((_, i) => (
                    <Skeleton key={i} className="h-32" />
                  ))}
                </div>
              ) : sortedGaps.length === 0 ? (
                <Card>
                  <CardContent className="py-12 text-center text-muted-foreground">
                    <Target className="w-12 h-12 mx-auto mb-2 opacity-30" />
                    <p>No skill gaps identified</p>
                    <p className="text-sm mt-1">Great job keeping your skills current!</p>
                  </CardContent>
                </Card>
              ) : (
                <div className="grid md:grid-cols-2 gap-4">
                  {sortedGaps.map((gap, index) => {
                    const pConfig =
                      priorityConfig[gap.gap_type] ?? priorityConfig.stretch;
                    const gapPercent = Math.round(
                      (gap.current_level / Math.max(gap.required_level, 1)) * 100
                    );

                    return (
                      <motion.div
                        key={gap.id}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.05 }}
                      >
                        <Card className="hover-lift">
                          <CardContent className="p-4">
                            <div className="flex items-start justify-between mb-3">
                              <div>
                                <h3 className="font-semibold">{gap.skill_name}</h3>
                                {gap.for_role && (
                                  <p className="text-xs text-muted-foreground">
                                    For: {gap.for_role}
                                  </p>
                                )}
                              </div>
                              <Badge
                                variant="secondary"
                                className={`${pConfig.color} ${pConfig.bg} text-xs`}
                              >
                                {pConfig.label}
                              </Badge>
                            </div>
                            <div className="space-y-2">
                              <div className="flex items-center justify-between text-sm">
                                <span className="text-muted-foreground">
                                  Level {gap.current_level} / {gap.required_level}
                                </span>
                                <span className="font-medium">
                                  Gap: {gap.gap_size}
                                </span>
                              </div>
                              <Progress value={gapPercent} className="h-2" />
                            </div>
                            {gap.learning_resources.length > 0 && (
                              <div className="mt-3 flex flex-wrap gap-1">
                                {gap.learning_resources.slice(0, 3).map((resource, ri) => (
                                  <Badge
                                    key={ri}
                                    variant="outline"
                                    className="text-[10px]"
                                  >
                                    {resource}
                                  </Badge>
                                ))}
                              </div>
                            )}
                          </CardContent>
                        </Card>
                      </motion.div>
                    );
                  })}
                </div>
              )}
            </div>
          </TabsContent>

          {/* ─── Learning Paths Tab ─────────────────────────────────── */}
          <TabsContent value="learning-paths">
            <div className="space-y-6 mt-4">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-semibold">Learning Paths</h2>
                  <p className="text-sm text-muted-foreground">
                    Structured paths to reach your skill goals
                  </p>
                </div>
              </div>

              {pathsLoading ? (
                <div className="grid md:grid-cols-2 gap-4">
                  {Array.from({ length: 3 }).map((_, i) => (
                    <Skeleton key={i} className="h-48" />
                  ))}
                </div>
              ) : learningPathsList.length === 0 ? (
                <Card>
                  <CardContent className="py-12 text-center text-muted-foreground">
                    <BookOpen className="w-12 h-12 mx-auto mb-2 opacity-30" />
                    <p>No learning paths created yet</p>
                    <p className="text-sm mt-1">
                      Learning paths will be generated based on your skill gaps
                    </p>
                  </CardContent>
                </Card>
              ) : (
                <div className="grid md:grid-cols-2 gap-4">
                  {learningPathsList.map((path, index) => (
                    <motion.div
                      key={path.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.05 }}
                    >
                      <Card className="hover-lift h-full">
                        <CardHeader className="pb-2">
                          <div className="flex items-start justify-between">
                            <div>
                              <CardTitle className="text-base">{path.title}</CardTitle>
                              {path.description && (
                                <CardDescription className="mt-1 line-clamp-2">
                                  {path.description}
                                </CardDescription>
                              )}
                            </div>
                            <div className="flex gap-1.5">
                              {path.is_ai_generated && (
                                <Badge variant="secondary" className="text-xs gap-1">
                                  <Sparkles className="w-3 h-3" />
                                  AI
                                </Badge>
                              )}
                              {path.is_active ? (
                                <Badge className="text-xs bg-emerald-500/10 text-emerald-500">
                                  Active
                                </Badge>
                              ) : (
                                <Badge variant="secondary" className="text-xs">
                                  Paused
                                </Badge>
                              )}
                            </div>
                          </div>
                        </CardHeader>
                        <CardContent>
                          {/* Skills targets */}
                          <div className="flex flex-wrap gap-1.5 mb-3">
                            {path.skills.map((s) => (
                              <Badge key={s.skill_id} variant="outline" className="text-[10px]">
                                {s.skill_name}: {s.current_level} → {s.target_level}
                              </Badge>
                            ))}
                          </div>

                          {/* Progress bar */}
                          <div className="space-y-1 mb-3">
                            <div className="flex items-center justify-between text-sm">
                              <span className="text-muted-foreground">Progress</span>
                              <span className="font-medium">
                                {Math.round(path.progress_percentage)}%
                              </span>
                            </div>
                            <Progress value={path.progress_percentage} className="h-2" />
                          </div>

                          {/* Milestones */}
                          {path.milestones.length > 0 && (
                            <div className="space-y-1.5">
                              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                                Milestones
                              </p>
                              {path.milestones.map((milestone, mi) => (
                                <div
                                  key={mi}
                                  className="flex items-center gap-2 text-sm"
                                >
                                  <CheckCircle2
                                    className={`w-4 h-4 shrink-0 ${
                                      milestone.completed
                                        ? 'text-emerald-500'
                                        : 'text-muted-foreground/30'
                                    }`}
                                  />
                                  <span
                                    className={
                                      milestone.completed
                                        ? 'line-through text-muted-foreground'
                                        : ''
                                    }
                                  >
                                    {milestone.title}
                                  </span>
                                </div>
                              ))}
                            </div>
                          )}

                          {path.target_completion && (
                            <p className="text-xs text-muted-foreground mt-2">
                              Target:{' '}
                              {new Date(path.target_completion).toLocaleDateString('en-US', {
                                month: 'short',
                                day: 'numeric',
                                year: 'numeric',
                              })}
                            </p>
                          )}
                        </CardContent>
                      </Card>
                    </motion.div>
                  ))}
                </div>
              )}
            </div>
          </TabsContent>

          {/* ─── Catalog Tab (Admin only) ───────────────────────────── */}
          {canCreateSkills && (
            <TabsContent value="catalog">
              <div className="space-y-6 mt-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-lg font-semibold">Skill Catalog</h2>
                    <p className="text-sm text-muted-foreground">
                      All organization skills grouped by category
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <Select value={catalogFilter} onValueChange={setCatalogFilter}>
                      <SelectTrigger className="w-[160px]">
                        <SelectValue placeholder="Filter category" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All Categories</SelectItem>
                        <SelectItem value="technical">Technical</SelectItem>
                        <SelectItem value="process">Process</SelectItem>
                        <SelectItem value="soft">Soft Skills</SelectItem>
                        <SelectItem value="domain">Domain</SelectItem>
                        <SelectItem value="tool">Tool</SelectItem>
                        <SelectItem value="language">Language</SelectItem>
                      </SelectContent>
                    </Select>
                    <CreateSkillDialog>
                      <Button className="gap-2">
                        <Plus className="w-4 h-4" />
                        Create Skill
                      </Button>
                    </CreateSkillDialog>
                  </div>
                </div>

                {catalogLoading ? (
                  <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {Array.from({ length: 6 }).map((_, i) => (
                      <Skeleton key={i} className="h-24" />
                    ))}
                  </div>
                ) : catalogSkills.length === 0 ? (
                  <Card>
                    <CardContent className="py-12 text-center text-muted-foreground">
                      <GraduationCap className="w-12 h-12 mx-auto mb-2 opacity-30" />
                      <p>No skills in the catalog yet</p>
                      <p className="text-sm mt-1">Create your first skill to get started</p>
                    </CardContent>
                  </Card>
                ) : (
                  Object.entries(groupedCatalog).map(([category, skills]) => (
                    <div key={category}>
                      <div className="flex items-center gap-2 mb-3">
                        <div
                          className="w-3 h-3 rounded-full"
                          style={{
                            backgroundColor: categoryColors[category] ?? '#6b7280',
                          }}
                        />
                        <h3 className="font-semibold capitalize">{category}</h3>
                        <Badge variant="secondary" className="text-xs">
                          {skills.length}
                        </Badge>
                      </div>
                      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-3">
                        {skills.map((skill) => (
                          <Card key={skill.id} className="hover-lift">
                            <CardContent className="p-4">
                              <div className="flex items-start justify-between">
                                <div className="min-w-0">
                                  <h4 className="font-medium text-sm truncate">
                                    {skill.name}
                                  </h4>
                                  {skill.description && (
                                    <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                                      {skill.description}
                                    </p>
                                  )}
                                </div>
                                {!skill.is_active && (
                                  <Badge variant="secondary" className="text-[10px] shrink-0">
                                    Inactive
                                  </Badge>
                                )}
                              </div>
                              <div className="flex items-center gap-3 mt-2 text-xs text-muted-foreground">
                                <span>
                                  Org avg: {skill.org_average_level.toFixed(1)}
                                </span>
                                <span>
                                  Industry: {skill.industry_average_level.toFixed(1)}
                                </span>
                              </div>
                              {skill.aliases.length > 0 && (
                                <div className="flex flex-wrap gap-1 mt-2">
                                  {skill.aliases.slice(0, 3).map((alias, ai) => (
                                    <Badge
                                      key={ai}
                                      variant="outline"
                                      className="text-[10px]"
                                    >
                                      {alias}
                                    </Badge>
                                  ))}
                                </div>
                              )}
                            </CardContent>
                          </Card>
                        ))}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </TabsContent>
          )}
        </Tabs>

        {/* Skill Velocity Chart */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <Card>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-lg">Skill Velocity</CardTitle>
                  <CardDescription>
                    Skill level changes over the past {velocityDays} days
                  </CardDescription>
                </div>
                <div className="flex items-center gap-2">
                  {velocityData && (
                    <div className="flex gap-3 text-xs text-muted-foreground">
                      <span className="flex items-center gap-1">
                        <TrendingUp className="w-3 h-3 text-emerald-500" />
                        {velocityData.skills_improved} improved
                      </span>
                      <span className="flex items-center gap-1">
                        <AlertTriangle className="w-3 h-3 text-amber-500" />
                        {velocityData.skills_declined} declined
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {velocityLoading ? (
                <Skeleton className="h-[280px] w-full" />
              ) : normalizedVelocityData.length === 0 ? (
                <div className="h-[280px] flex items-center justify-center text-muted-foreground">
                  <div className="text-center">
                    <TrendingUp className="w-12 h-12 mx-auto mb-2 opacity-30" />
                    <p>No velocity data yet</p>
                    <p className="text-sm">Skill changes will appear here over time</p>
                  </div>
                </div>
              ) : (
                <div className="h-[280px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={normalizedVelocityData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                      <XAxis
                        dataKey="date"
                        stroke="hsl(var(--muted-foreground))"
                        fontSize={12}
                      />
                      <YAxis
                        stroke="hsl(var(--muted-foreground))"
                        fontSize={12}
                        domain={[0, 5]}
                      />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: 'hsl(var(--card))',
                          border: '1px solid hsl(var(--border))',
                          borderRadius: '8px',
                        }}
                      />
                      {velocitySkillNames.map((skillName, i) => (
                        <Line
                          key={skillName}
                          type="monotone"
                          dataKey={skillName}
                          name={skillName}
                          stroke={velocityLineColors[i % velocityLineColors.length]}
                          strokeWidth={2}
                          dot={{ r: 3 }}
                        />
                      ))}
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              )}
              {velocityData && (
                <div className="flex items-center justify-center gap-4 mt-3">
                  <span className="text-xs text-muted-foreground">
                    Learning velocity: <span className="font-medium text-foreground">{velocityData.learning_velocity.toFixed(2)}</span>
                  </span>
                  <span className="text-xs text-muted-foreground">
                    Avg improvement rate: <span className="font-medium text-foreground">{velocityData.avg_improvement_rate.toFixed(2)}</span>
                  </span>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </DashboardLayout>
  );
}

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Search,
  Filter,
  MoreHorizontal,
  Calendar,
  List,
  LayoutGrid,
  Clock,
  GripVertical,
  ArrowUpDown,
  AlertTriangle,
  Loader2,
  Sparkles,
  Paperclip,
  MessageSquare,
  Bot,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet';
import DashboardLayout from '@/components/layout/DashboardLayout';
import { tasksService } from '@/services/tasks.service';
import { chatService } from '@/services/chat.service';
import { queryKeys } from '@/hooks/useApi';
import { mapTaskToFrontend, mapStatusToApi, type FrontendTask, type FrontendTaskStatus } from '@/types/mappers';
import { getApiErrorMessage } from '@/lib/api-client';
import { toast } from 'sonner';

// Priority config
const priorityConfig: Record<string, { color: string; label: string }> = {
  low: { color: 'bg-slate-500', label: 'Low' },
  medium: { color: 'bg-blue-500', label: 'Medium' },
  high: { color: 'bg-orange-500', label: 'High' },
  urgent: { color: 'bg-red-500', label: 'Urgent' },
};

// Status columns for Kanban
const columns = [
  { id: 'todo' as const, title: 'To Do', color: 'bg-slate-500' },
  { id: 'in-progress' as const, title: 'In Progress', color: 'bg-blue-500' },
  { id: 'review' as const, title: 'Review', color: 'bg-amber-500' },
  { id: 'done' as const, title: 'Done', color: 'bg-emerald-500' },
];

// ─── Describe Task Dialog (AI-driven) ────────────────────────────────
function DescribeTaskDialog({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = useState(false);
  const [description, setDescription] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const navigate = useNavigate();

  const handleSendToAI = () => {
    setOpen(false);
    navigate('/ai', {
      state: {
        pendingTask: {
          description: description.trim() || undefined,
          fileName: file?.name,
        },
        file: file || undefined,
      },
    });
    setDescription('');
    setFile(null);
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{children}</DialogTrigger>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-primary" />
            Describe Your Task
          </DialogTitle>
        </DialogHeader>
        <div className="space-y-4 pt-2">
          <div className="space-y-2">
            <Label>Describe what you need to do</Label>
            <Textarea
              placeholder="e.g., I need to build a REST API for user authentication with JWT tokens, set up database models, write tests..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={5}
            />
          </div>
          <div className="space-y-2">
            <Label>Or upload a task description</Label>
            <div className="border-2 border-dashed rounded-lg p-4 text-center hover:border-primary/50 transition-colors">
              <input
                type="file"
                accept=".pdf,.docx,.txt,.md"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                className="hidden"
                id="task-file-upload"
              />
              <label htmlFor="task-file-upload" className="cursor-pointer">
                {file ? (
                  <div className="flex items-center justify-center gap-2 text-sm text-primary">
                    <Paperclip className="w-4 h-4" />
                    {file.name}
                    <button
                      type="button"
                      className="text-muted-foreground hover:text-foreground text-xs ml-2"
                      onClick={(e) => { e.preventDefault(); setFile(null); }}
                    >
                      Remove
                    </button>
                  </div>
                ) : (
                  <div className="text-muted-foreground text-sm">
                    <Paperclip className="w-5 h-5 mx-auto mb-1 opacity-50" />
                    Click to upload PDF, DOCX, or TXT
                  </div>
                )}
              </label>
            </div>
          </div>
          <Button
            className="w-full gap-2"
            disabled={!description.trim() && !file}
            onClick={handleSendToAI}
          >
            <Bot className="w-4 h-4" />
            Send to AI Agent
          </Button>
          <p className="text-xs text-muted-foreground text-center">
            The AI agent will ask you about deadlines, priorities, and create the task with subtasks.
          </p>
        </div>
      </DialogContent>
    </Dialog>
  );
}

// ─── Task Detail Panel (Sheet) ───────────────────────────────────────
function TaskDetailPanel({
  task,
  onClose,
}: {
  task: FrontendTask;
  onClose: () => void;
}) {
  const queryClient = useQueryClient();
  const [blockerDesc, setBlockerDesc] = useState('');
  const [showBlockerForm, setShowBlockerForm] = useState(false);

  const { data: subtasks, isLoading: subtasksLoading } = useQuery({
    queryKey: queryKeys.tasks.subtasks(task.id),
    queryFn: () => tasksService.getSubtasks(task.id),
  });

  const { data: commentsData } = useQuery({
    queryKey: queryKeys.tasks.comments(task.id),
    queryFn: () => tasksService.getComments(task.id),
  });
  const comments = Array.isArray(commentsData) ? commentsData : (commentsData as any)?.comments ?? [];

  const blockerMutation = useMutation({
    mutationFn: () =>
      tasksService.updateStatus(task.id, {
        status: 'BLOCKED',
        blocker_type: 'BUG',
        blocker_description: blockerDesc,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.tasks.all });
      toast.success('Blocker reported — AI agent is analyzing...');
      setBlockerDesc('');
      setShowBlockerForm(false);
      chatService.sendMessage({
        message: `I'm blocked on task "${task.title}": ${blockerDesc}`,
      });
    },
    onError: (err) => toast.error(getApiErrorMessage(err)),
  });

  const statusLabels: Record<string, string> = {
    'todo': 'To Do', 'in-progress': 'In Progress', 'review': 'Review', 'done': 'Done',
  };

  return (
    <Sheet open onOpenChange={() => onClose()}>
      <SheetContent side="right" className="sm:max-w-lg overflow-y-auto">
        <SheetHeader>
          <SheetTitle>{task.title}</SheetTitle>
        </SheetHeader>
        <div className="space-y-6 px-4 pb-6">
          {task.description && (
            <p className="text-sm text-muted-foreground">{task.description}</p>
          )}
          <div className="flex gap-2">
            <Badge variant="outline">{statusLabels[task.status] ?? task.status}</Badge>
            <Badge variant="secondary">{priorityConfig[task.priority]?.label ?? task.priority}</Badge>
            {task.dueDate && (
              <Badge variant="outline" className="text-xs">
                <Calendar className="w-3 h-3 mr-1" />
                {new Date(task.dueDate).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
              </Badge>
            )}
          </div>

          {/* Subtasks */}
          <div>
            <h3 className="font-medium mb-2 text-sm">Subtasks</h3>
            {subtasksLoading ? (
              <div className="space-y-2">
                <Skeleton className="h-12 w-full" />
                <Skeleton className="h-12 w-full" />
              </div>
            ) : subtasks && subtasks.length > 0 ? (
              <div className="space-y-2">
                {subtasks.map((sub: any) => (
                  <div
                    key={sub.id}
                    className="flex items-center justify-between p-3 rounded-lg border"
                  >
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{sub.title}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <Badge variant="outline" className="text-[10px]">
                          {sub.status?.replace('_', ' ')}
                        </Badge>
                        {sub.estimated_hours && (
                          <span className="text-[10px] text-muted-foreground flex items-center gap-0.5">
                            <Clock className="w-2.5 h-2.5" />{sub.estimated_hours}h
                          </span>
                        )}
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-xs text-amber-600 shrink-0"
                      onClick={() => setShowBlockerForm(true)}
                    >
                      Report Issue
                    </Button>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No subtasks yet.</p>
            )}
          </div>

          {/* Blocker Report Form */}
          {showBlockerForm && (
            <div className="space-y-3 border rounded-lg p-4 bg-amber-50 dark:bg-amber-500/5">
              <h3 className="font-medium text-sm text-amber-800 dark:text-amber-300 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4" />
                Report a Blocker
              </h3>
              <Textarea
                placeholder="Describe what's blocking you... Include error messages if any."
                value={blockerDesc}
                onChange={(e) => setBlockerDesc(e.target.value)}
                rows={3}
              />
              <div className="flex gap-2">
                <Button
                  size="sm"
                  className="gap-1"
                  disabled={!blockerDesc.trim() || blockerMutation.isPending}
                  onClick={() => blockerMutation.mutate()}
                >
                  {blockerMutation.isPending && <Loader2 className="w-3 h-3 animate-spin" />}
                  Report & Get AI Help
                </Button>
                <Button variant="ghost" size="sm" onClick={() => setShowBlockerForm(false)}>
                  Cancel
                </Button>
              </div>
            </div>
          )}

          {!showBlockerForm && (
            <Button
              variant="outline"
              className="w-full gap-2 text-amber-600 border-amber-300 hover:bg-amber-50 dark:hover:bg-amber-500/5"
              onClick={() => setShowBlockerForm(true)}
            >
              <AlertTriangle className="w-4 h-4" />
              Report Blocker / Issue
            </Button>
          )}

          {/* Comments */}
          {comments.length > 0 && (
            <div>
              <h3 className="font-medium mb-2 text-sm flex items-center gap-2">
                <MessageSquare className="w-4 h-4" />
                Comments
              </h3>
              <div className="space-y-2">
                {comments.map((comment: any) => (
                  <div key={comment.id} className="p-3 rounded-lg bg-muted text-sm">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium text-xs">
                        {comment.is_ai_generated ? (
                          <span className="flex items-center gap-1 text-primary">
                            <Bot className="w-3 h-3" /> AI Agent
                          </span>
                        ) : (
                          comment.user_name ?? 'User'
                        )}
                      </span>
                      <span className="text-[10px] text-muted-foreground">
                        {new Date(comment.created_at).toLocaleString()}
                      </span>
                    </div>
                    <p className="whitespace-pre-wrap text-xs">{comment.content}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}

// ─── Kanban View ─────────────────────────────────────────────────────
function KanbanView({
  tasks, onStatusChange, onDelete, onSelect,
}: {
  tasks: FrontendTask[];
  onStatusChange: (id: string, status: FrontendTaskStatus) => void;
  onDelete: (id: string) => void;
  onSelect: (task: FrontendTask) => void;
}) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {columns.map((column) => {
        const columnTasks = tasks.filter((task) => task.status === column.id);
        return (
          <div key={column.id} className="flex flex-col">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <div className={`w-3 h-3 rounded-full ${column.color}`} />
                <span className="font-medium">{column.title}</span>
                <Badge variant="secondary" className="text-xs">{columnTasks.length}</Badge>
              </div>
            </div>
            <div className="space-y-3">
              <AnimatePresence>
                {columnTasks.map((task) => (
                  <motion.div
                    key={task.id}
                    layout
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.95 }}
                    transition={{ duration: 0.2 }}
                  >
                    <TaskCard task={task} onStatusChange={onStatusChange} onDelete={onDelete} onSelect={onSelect} />
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ─── Task Card ───────────────────────────────────────────────────────
function TaskCard({
  task, onStatusChange, onDelete, onSelect,
}: {
  task: FrontendTask;
  onStatusChange: (id: string, status: FrontendTaskStatus) => void;
  onDelete: (id: string) => void;
  onSelect: (task: FrontendTask) => void;
}) {
  const priority = priorityConfig[task.priority] ?? priorityConfig.medium;
  return (
    <Card
      className="cursor-pointer hover:shadow-md transition-shadow group"
      onClick={() => onSelect(task)}
    >
      <CardContent className="p-4">
        <div className="flex items-start justify-between mb-2">
          <div className={`w-2 h-2 rounded-full ${priority.color} mt-1.5`} />
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity"
                onClick={(e) => e.stopPropagation()}
              >
                <MoreHorizontal className="w-4 h-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              {columns.filter((c) => c.id !== task.status).map((col) => (
                <DropdownMenuItem key={col.id} onClick={(e) => { e.stopPropagation(); onStatusChange(task.id, col.id); }}>
                  Move to {col.title}
                </DropdownMenuItem>
              ))}
              <DropdownMenuItem className="text-destructive" onClick={(e) => { e.stopPropagation(); onDelete(task.id); }}>Delete</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
        <h4 className="font-medium mb-2 line-clamp-2">{task.title}</h4>
        <div className="flex flex-wrap gap-1 mb-3">
          {task.tags.map((tag) => (
            <Badge key={tag} variant="secondary" className="text-[10px]">{tag}</Badge>
          ))}
        </div>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Avatar className="w-6 h-6">
              <AvatarFallback className="text-[10px] bg-primary/10 text-primary">
                {task.assigneeName?.charAt(0) ?? '?'}
              </AvatarFallback>
            </Avatar>
            <span className="text-xs text-muted-foreground flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {task.estimatedHours}h
            </span>
          </div>
          {task.dueDate && (
            <span className={`text-xs ${new Date(task.dueDate) < new Date() ? 'text-red-500' : 'text-muted-foreground'}`}>
              {new Date(task.dueDate).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
            </span>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

// ─── List View ───────────────────────────────────────────────────────
function ListView({
  tasks, onStatusChange: _onStatusChange, onDelete: _onDelete, onSelect,
}: {
  tasks: FrontendTask[];
  onStatusChange: (id: string, status: FrontendTaskStatus) => void;
  onDelete: (id: string) => void;
  onSelect: (task: FrontendTask) => void;
}) {
  return (
    <Card>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-border/50">
              <th className="text-left p-4 font-medium text-sm text-muted-foreground">
                <div className="flex items-center gap-2">
                  <GripVertical className="w-4 h-4 opacity-0" />
                  Task
                </div>
              </th>
              <th className="text-left p-4 font-medium text-sm text-muted-foreground">Status</th>
              <th className="text-left p-4 font-medium text-sm text-muted-foreground">Priority</th>
              <th className="text-left p-4 font-medium text-sm text-muted-foreground">Assignee</th>
              <th className="text-left p-4 font-medium text-sm text-muted-foreground">Due Date</th>
              <th className="text-left p-4 font-medium text-sm text-muted-foreground">Est.</th>
            </tr>
          </thead>
          <tbody>
            {tasks.map((task) => {
              const priority = priorityConfig[task.priority] ?? priorityConfig.medium;
              const statusLabels: Record<string, string> = {
                'todo': 'To Do', 'in-progress': 'In Progress', 'review': 'Review', 'done': 'Done',
              };
              return (
                <tr
                  key={task.id}
                  className="border-b border-border/50 hover:bg-muted/50 transition-colors cursor-pointer"
                  onClick={() => onSelect(task)}
                >
                  <td className="p-4">
                    <div className="flex items-center gap-2">
                      <GripVertical className="w-4 h-4 text-muted-foreground cursor-grab" />
                      <div>
                        <p className="font-medium">{task.title}</p>
                        <div className="flex gap-1 mt-1">
                          {task.tags.map((tag) => (
                            <Badge key={tag} variant="secondary" className="text-[10px]">{tag}</Badge>
                          ))}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="p-4"><Badge variant="outline" className="text-xs">{statusLabels[task.status]}</Badge></td>
                  <td className="p-4">
                    <div className="flex items-center gap-2">
                      <div className={`w-2 h-2 rounded-full ${priority.color}`} />
                      <span className="text-sm">{priority.label}</span>
                    </div>
                  </td>
                  <td className="p-4">
                    <Avatar className="w-8 h-8">
                      <AvatarFallback className="text-xs bg-primary/10 text-primary">
                        {task.assigneeName?.charAt(0) ?? '?'}
                      </AvatarFallback>
                    </Avatar>
                  </td>
                  <td className="p-4">
                    {task.dueDate ? (
                      <span className={`text-sm ${new Date(task.dueDate) < new Date() ? 'text-red-500' : ''}`}>
                        {new Date(task.dueDate).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                      </span>
                    ) : (
                      <span className="text-sm text-muted-foreground">-</span>
                    )}
                  </td>
                  <td className="p-4"><span className="text-sm text-muted-foreground">{task.estimatedHours}h</span></td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </Card>
  );
}

// ─── Timeline View ───────────────────────────────────────────────────
function TimelineView({ tasks }: { tasks: FrontendTask[] }) {
  const sortedTasks = [...tasks].filter((t) => t.dueDate).sort((a, b) =>
    new Date(a.dueDate).getTime() - new Date(b.dueDate).getTime()
  );
  const groupedByDate = sortedTasks.reduce((acc, task) => {
    const date = task.dueDate.split('T')[0];
    if (!acc[date]) acc[date] = [];
    acc[date].push(task);
    return acc;
  }, {} as Record<string, FrontendTask[]>);

  if (Object.keys(groupedByDate).length === 0) {
    return <p className="text-center text-muted-foreground py-12">No tasks with due dates to display in timeline view.</p>;
  }

  return (
    <div className="space-y-6">
      {Object.entries(groupedByDate).map(([date, dateTasks]) => (
        <div key={date} className="relative">
          <div className="flex items-center gap-4 mb-4">
            <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
              <Calendar className="w-5 h-5 text-primary" />
            </div>
            <div>
              <p className="font-medium">
                {new Date(date).toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })}
              </p>
              <p className="text-sm text-muted-foreground">{dateTasks.length} tasks</p>
            </div>
          </div>
          <div className="absolute left-5 top-14 bottom-0 w-px bg-border" />
          <div className="space-y-3 ml-12">
            {dateTasks.map((task) => (
              <Card key={task.id} className="p-4">
                <h4 className="font-medium">{task.title}</h4>
                <div className="flex items-center gap-2 mt-1">
                  <Badge variant="outline" className="text-[10px]">{task.priority}</Badge>
                  <span className="text-xs text-muted-foreground capitalize">{task.status.replace('-', ' ')}</span>
                </div>
              </Card>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

// ─── Main Tasks Page ─────────────────────────────────────────────────
export default function TasksPage() {
  const [view, setView] = useState<'kanban' | 'list' | 'timeline'>('kanban');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTask, setSelectedTask] = useState<FrontendTask | null>(null);
  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery({
    queryKey: queryKeys.tasks.list({ search: searchQuery || undefined, root_only: true, limit: 100 }),
    queryFn: () => tasksService.list({ search: searchQuery || undefined, root_only: true, limit: 100 }),
  });

  const tasks = (data?.tasks ?? []).map(mapTaskToFrontend);

  const statusMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: FrontendTaskStatus }) =>
      tasksService.updateStatus(id, { status: mapStatusToApi(status) }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.tasks.all }),
    onError: (err) => toast.error(getApiErrorMessage(err)),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => tasksService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.tasks.all });
      toast.success('Task deleted');
    },
    onError: (err) => toast.error(getApiErrorMessage(err)),
  });

  const handleStatusChange = (id: string, status: FrontendTaskStatus) => statusMutation.mutate({ id, status });
  const handleDelete = (id: string) => deleteMutation.mutate(id);

  if (error) {
    return (
      <DashboardLayout>
        <Card className="p-8">
          <div className="flex flex-col items-center gap-4 text-center">
            <AlertTriangle className="w-12 h-12 text-amber-500" />
            <h2 className="text-lg font-semibold">Failed to load tasks</h2>
            <p className="text-muted-foreground">{(error as Error).message}</p>
            <Button onClick={() => queryClient.invalidateQueries({ queryKey: queryKeys.tasks.all })}>Retry</Button>
          </div>
        </Card>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <h1 className="text-2xl lg:text-3xl font-bold">Tasks</h1>
            <p className="text-muted-foreground mt-1">Manage and track your tasks</p>
          </div>
          <DescribeTaskDialog>
            <Button className="gap-2">
              <Sparkles className="w-4 h-4" />
              Describe Your Task
            </Button>
          </DescribeTaskDialog>
        </div>

        {/* Controls */}
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="Search tasks..."
              className="pl-10"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
          <div className="flex gap-2">
            <Button variant="outline" className="gap-2">
              <Filter className="w-4 h-4" />
              Filter
            </Button>
            <Button variant="outline" className="gap-2">
              <ArrowUpDown className="w-4 h-4" />
              Sort
            </Button>
            <Tabs value={view} onValueChange={(v) => setView(v as typeof view)}>
              <TabsList>
                <TabsTrigger value="kanban" className="gap-2">
                  <LayoutGrid className="w-4 h-4" />
                  <span className="hidden sm:inline">Board</span>
                </TabsTrigger>
                <TabsTrigger value="list" className="gap-2">
                  <List className="w-4 h-4" />
                  <span className="hidden sm:inline">List</span>
                </TabsTrigger>
                <TabsTrigger value="timeline" className="gap-2">
                  <Calendar className="w-4 h-4" />
                  <span className="hidden sm:inline">Timeline</span>
                </TabsTrigger>
              </TabsList>
            </Tabs>
          </div>
        </div>

        {/* Content */}
        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="space-y-3">
                <Skeleton className="h-6 w-24" />
                <Skeleton className="h-32 w-full rounded-xl" />
                <Skeleton className="h-32 w-full rounded-xl" />
              </div>
            ))}
          </div>
        ) : (
          <AnimatePresence mode="wait">
            <motion.div
              key={view}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
            >
              {view === 'kanban' && <KanbanView tasks={tasks} onStatusChange={handleStatusChange} onDelete={handleDelete} onSelect={setSelectedTask} />}
              {view === 'list' && <ListView tasks={tasks} onStatusChange={handleStatusChange} onDelete={handleDelete} onSelect={setSelectedTask} />}
              {view === 'timeline' && <TimelineView tasks={tasks} />}
            </motion.div>
          </AnimatePresence>
        )}
      </div>

      {/* Task Detail Panel */}
      {selectedTask && (
        <TaskDetailPanel
          task={selectedTask}
          onClose={() => setSelectedTask(null)}
        />
      )}
    </DashboardLayout>
  );
}

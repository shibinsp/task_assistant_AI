import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Plus,
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
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
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
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import DashboardLayout from '@/components/layout/DashboardLayout';
import { tasksService } from '@/services/tasks.service';
import { queryKeys } from '@/hooks/useApi';
import { mapTaskToFrontend, mapStatusToApi, mapPriorityToApi, type FrontendTask, type FrontendTaskStatus, type FrontendTaskPriority } from '@/types/mappers';
import type { ApiTaskCreate, ApiTaskPriority } from '@/types/api';
import { getApiErrorMessage } from '@/lib/api-client';
import { toast } from 'sonner';

// Priority config
const priorityConfig = {
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

// Create Task Dialog
function CreateTaskDialog({ children }: { children: React.ReactNode }) {
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ title: '', description: '', priority: 'MEDIUM' as ApiTaskPriority });

  const createMutation = useMutation({
    mutationFn: (payload: ApiTaskCreate) => tasksService.create(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.tasks.all });
      toast.success('Task created');
      setOpen(false);
      setForm({ title: '', description: '', priority: 'MEDIUM' });
    },
    onError: (err) => toast.error(getApiErrorMessage(err)),
  });

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{children}</DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create Task</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 pt-2">
          <div className="space-y-2">
            <Label>Title</Label>
            <Input
              placeholder="Task title"
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
            />
          </div>
          <div className="space-y-2">
            <Label>Description</Label>
            <Input
              placeholder="Optional description"
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
            />
          </div>
          <div className="space-y-2">
            <Label>Priority</Label>
            <Select value={form.priority} onValueChange={(v) => setForm({ ...form, priority: v as ApiTaskPriority })}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="LOW">Low</SelectItem>
                <SelectItem value="MEDIUM">Medium</SelectItem>
                <SelectItem value="HIGH">High</SelectItem>
                <SelectItem value="CRITICAL">Urgent</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <Button
            className="w-full"
            disabled={!form.title.trim() || createMutation.isPending}
            onClick={() => createMutation.mutate({
              title: form.title,
              description: form.description || undefined,
              priority: form.priority,
            })}
          >
            {createMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
            Create Task
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

// Kanban View
function KanbanView({ tasks, onStatusChange, onDelete }: { tasks: FrontendTask[]; onStatusChange: (id: string, status: FrontendTaskStatus) => void; onDelete: (id: string) => void }) {
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
                    <TaskCard task={task} onStatusChange={onStatusChange} onDelete={onDelete} />
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

// Task Card Component
function TaskCard({ task, onStatusChange, onDelete }: { task: FrontendTask; onStatusChange: (id: string, status: FrontendTaskStatus) => void; onDelete: (id: string) => void }) {
  const priority = priorityConfig[task.priority];
  return (
    <Card className="cursor-pointer hover:shadow-md transition-shadow group">
      <CardContent className="p-4">
        <div className="flex items-start justify-between mb-2">
          <div className={`w-2 h-2 rounded-full ${priority.color} mt-1.5`} />
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity">
                <MoreHorizontal className="w-4 h-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              {columns.filter((c) => c.id !== task.status).map((col) => (
                <DropdownMenuItem key={col.id} onClick={() => onStatusChange(task.id, col.id)}>
                  Move to {col.title}
                </DropdownMenuItem>
              ))}
              <DropdownMenuItem className="text-destructive" onClick={() => onDelete(task.id)}>Delete</DropdownMenuItem>
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

// List View
function ListView({ tasks, onStatusChange, onDelete }: { tasks: FrontendTask[]; onStatusChange: (id: string, status: FrontendTaskStatus) => void; onDelete: (id: string) => void }) {
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
              const priority = priorityConfig[task.priority];
              const statusLabels: Record<string, string> = {
                'todo': 'To Do', 'in-progress': 'In Progress', 'review': 'Review', 'done': 'Done',
              };
              return (
                <tr key={task.id} className="border-b border-border/50 hover:bg-muted/50 transition-colors">
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

// Timeline View
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

export default function TasksPage() {
  const [view, setView] = useState<'kanban' | 'list' | 'timeline'>('kanban');
  const [searchQuery, setSearchQuery] = useState('');
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
            <p className="text-muted-foreground mt-1">Manage and track your team's tasks</p>
          </div>
          <CreateTaskDialog>
            <Button className="gap-2">
              <Plus className="w-4 h-4" />
              New Task
            </Button>
          </CreateTaskDialog>
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
              {view === 'kanban' && <KanbanView tasks={tasks} onStatusChange={handleStatusChange} onDelete={handleDelete} />}
              {view === 'list' && <ListView tasks={tasks} onStatusChange={handleStatusChange} onDelete={handleDelete} />}
              {view === 'timeline' && <TimelineView tasks={tasks} />}
            </motion.div>
          </AnimatePresence>
        )}
      </div>
    </DashboardLayout>
  );
}

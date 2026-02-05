import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
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
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import DashboardLayout from '@/components/layout/DashboardLayout';

// Task types
interface Task {
  id: string;
  title: string;
  description: string;
  status: 'todo' | 'in-progress' | 'review' | 'done';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  assignee: string;
  dueDate: string;
  tags: string[];
  estimatedHours: number;
}

// Mock tasks data
const mockTasks: Task[] = [
  {
    id: '1',
    title: 'Design new landing page',
    description: 'Create mockups for the new marketing landing page',
    status: 'todo',
    priority: 'high',
    assignee: 'AW',
    dueDate: '2025-02-10',
    tags: ['design', 'marketing'],
    estimatedHours: 8,
  },
  {
    id: '2',
    title: 'Fix authentication bug',
    description: 'Users reporting login issues on mobile devices',
    status: 'in-progress',
    priority: 'urgent',
    assignee: 'JD',
    dueDate: '2025-02-05',
    tags: ['bug', 'auth'],
    estimatedHours: 4,
  },
  {
    id: '3',
    title: 'Update API documentation',
    description: 'Add new endpoints to the developer docs',
    status: 'review',
    priority: 'medium',
    assignee: 'SM',
    dueDate: '2025-02-08',
    tags: ['docs', 'api'],
    estimatedHours: 3,
  },
  {
    id: '4',
    title: 'Optimize database queries',
    description: 'Improve performance of slow queries',
    status: 'done',
    priority: 'high',
    assignee: 'RK',
    dueDate: '2025-02-03',
    tags: ['performance', 'database'],
    estimatedHours: 6,
  },
  {
    id: '5',
    title: 'Write unit tests',
    description: 'Increase test coverage for auth module',
    status: 'todo',
    priority: 'medium',
    assignee: 'ML',
    dueDate: '2025-02-12',
    tags: ['testing'],
    estimatedHours: 5,
  },
  {
    id: '6',
    title: 'Implement dark mode',
    description: 'Add dark theme support to the dashboard',
    status: 'in-progress',
    priority: 'low',
    assignee: 'TC',
    dueDate: '2025-02-15',
    tags: ['ui', 'feature'],
    estimatedHours: 10,
  },
];

// Priority config
const priorityConfig = {
  low: { color: 'bg-slate-500', label: 'Low' },
  medium: { color: 'bg-blue-500', label: 'Medium' },
  high: { color: 'bg-orange-500', label: 'High' },
  urgent: { color: 'bg-red-500', label: 'Urgent' },
};

// Status columns for Kanban
const columns = [
  { id: 'todo', title: 'To Do', color: 'bg-slate-500' },
  { id: 'in-progress', title: 'In Progress', color: 'bg-blue-500' },
  { id: 'review', title: 'Review', color: 'bg-amber-500' },
  { id: 'done', title: 'Done', color: 'bg-emerald-500' },
];

// Kanban View
function KanbanView({ tasks }: { tasks: Task[] }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {columns.map((column) => {
        const columnTasks = tasks.filter((task) => task.status === column.id);
        
        return (
          <div key={column.id} className="flex flex-col">
            {/* Column Header */}
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <div className={`w-3 h-3 rounded-full ${column.color}`} />
                <span className="font-medium">{column.title}</span>
                <Badge variant="secondary" className="text-xs">
                  {columnTasks.length}
                </Badge>
              </div>
              <Button variant="ghost" size="icon" className="h-8 w-8">
                <Plus className="w-4 h-4" />
              </Button>
            </div>
            
            {/* Tasks */}
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
                    <TaskCard task={task} />
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
function TaskCard({ task }: { task: Task }) {
  const priority = priorityConfig[task.priority];
  
  return (
    <Card className="cursor-pointer hover:shadow-md transition-shadow group">
      <CardContent className="p-4">
        {/* Header */}
        <div className="flex items-start justify-between mb-2">
          <div className={`w-2 h-2 rounded-full ${priority.color} mt-1.5`} />
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity">
                <MoreHorizontal className="w-4 h-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem>Edit</DropdownMenuItem>
              <DropdownMenuItem>Duplicate</DropdownMenuItem>
              <DropdownMenuItem className="text-destructive">Delete</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
        
        {/* Title */}
        <h4 className="font-medium mb-2 line-clamp-2">{task.title}</h4>
        
        {/* Tags */}
        <div className="flex flex-wrap gap-1 mb-3">
          {task.tags.map((tag) => (
            <Badge key={tag} variant="secondary" className="text-[10px]">
              {tag}
            </Badge>
          ))}
        </div>
        
        {/* Footer */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Avatar className="w-6 h-6">
              <AvatarFallback className="text-[10px] bg-primary/10 text-primary">
                {task.assignee}
              </AvatarFallback>
            </Avatar>
            <span className="text-xs text-muted-foreground flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {task.estimatedHours}h
            </span>
          </div>
          <span className={`text-xs ${
            new Date(task.dueDate) < new Date() ? 'text-red-500' : 'text-muted-foreground'
          }`}>
            {new Date(task.dueDate).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
          </span>
        </div>
      </CardContent>
    </Card>
  );
}

// List View
function ListView({ tasks }: { tasks: Task[] }) {
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
                'todo': 'To Do',
                'in-progress': 'In Progress',
                'review': 'Review',
                'done': 'Done',
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
                            <Badge key={tag} variant="secondary" className="text-[10px]">
                              {tag}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="p-4">
                    <Badge variant="outline" className="text-xs">
                      {statusLabels[task.status]}
                    </Badge>
                  </td>
                  <td className="p-4">
                    <div className="flex items-center gap-2">
                      <div className={`w-2 h-2 rounded-full ${priority.color}`} />
                      <span className="text-sm">{priority.label}</span>
                    </div>
                  </td>
                  <td className="p-4">
                    <Avatar className="w-8 h-8">
                      <AvatarFallback className="text-xs bg-primary/10 text-primary">
                        {task.assignee}
                      </AvatarFallback>
                    </Avatar>
                  </td>
                  <td className="p-4">
                    <span className={`text-sm ${
                      new Date(task.dueDate) < new Date() ? 'text-red-500' : ''
                    }`}>
                      {new Date(task.dueDate).toLocaleDateString('en-US', { 
                        month: 'short', 
                        day: 'numeric',
                        year: 'numeric'
                      })}
                    </span>
                  </td>
                  <td className="p-4">
                    <span className="text-sm text-muted-foreground">{task.estimatedHours}h</span>
                  </td>
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
function TimelineView({ tasks }: { tasks: Task[] }) {
  const sortedTasks = [...tasks].sort((a, b) => 
    new Date(a.dueDate).getTime() - new Date(b.dueDate).getTime()
  );
  
  const groupedByDate = sortedTasks.reduce((acc, task) => {
    const date = task.dueDate;
    if (!acc[date]) acc[date] = [];
    acc[date].push(task);
    return acc;
  }, {} as Record<string, Task[]>);

  return (
    <div className="space-y-6">
      {Object.entries(groupedByDate).map(([date, dateTasks]) => (
        <div key={date} className="relative">
          {/* Date Header */}
          <div className="flex items-center gap-4 mb-4">
            <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
              <Calendar className="w-5 h-5 text-primary" />
            </div>
            <div>
              <p className="font-medium">
                {new Date(date).toLocaleDateString('en-US', { 
                  weekday: 'long',
                  month: 'long', 
                  day: 'numeric',
                })}
              </p>
              <p className="text-sm text-muted-foreground">
                {dateTasks.length} tasks
              </p>
            </div>
          </div>
          
          {/* Timeline Line */}
          <div className="absolute left-5 top-14 bottom-0 w-px bg-border" />
          
          {/* Tasks */}
          <div className="space-y-3 ml-12">
            {dateTasks.map((task) => (
              <TaskCard key={task.id} task={task} />
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
  
  const filteredTasks = mockTasks.filter((task) =>
    task.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    task.tags.some((tag) => tag.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <h1 className="text-2xl lg:text-3xl font-bold">Tasks</h1>
            <p className="text-muted-foreground mt-1">
              Manage and track your team's tasks
            </p>
          </div>
          <Button className="gap-2">
            <Plus className="w-4 h-4" />
            New Task
          </Button>
        </div>

        {/* Controls */}
        <div className="flex flex-col sm:flex-row gap-4">
          {/* Search */}
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="Search tasks..."
              className="pl-10"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
          
          {/* Filters & View Toggle */}
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
        <AnimatePresence mode="wait">
          <motion.div
            key={view}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
          >
            {view === 'kanban' && <KanbanView tasks={filteredTasks} />}
            {view === 'list' && <ListView tasks={filteredTasks} />}
            {view === 'timeline' && <TimelineView tasks={filteredTasks} />}
          </motion.div>
        </AnimatePresence>
      </div>
    </DashboardLayout>
  );
}

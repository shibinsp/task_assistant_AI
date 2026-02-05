import { useState } from 'react';
import { motion } from 'framer-motion';
import {
  Plus,
  Play,
  Zap,
  Clock,
  Mail,
  MessageSquare,
  CheckSquare,
  Bell,
  GitBranch,
  Trash2,
  Copy,
  Edit3,
  Power,
  CheckCircle2,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
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
import DashboardLayout from '@/components/layout/DashboardLayout';

// Workflow types
interface Workflow {
  id: string;
  name: string;
  description: string;
  status: 'active' | 'paused' | 'draft';
  trigger: string;
  actions: number;
  lastRun: string;
  runsCount: number;
  successRate: number;
}

// Mock workflows
const mockWorkflows: Workflow[] = [
  {
    id: '1',
    name: 'New Task Notification',
    description: 'Send Slack notification when a new task is created',
    status: 'active',
    trigger: 'Task Created',
    actions: 2,
    lastRun: '2 min ago',
    runsCount: 1247,
    successRate: 99.8,
  },
  {
    id: '2',
    name: 'Daily Standup Reminder',
    description: 'Remind team members to update their tasks',
    status: 'active',
    trigger: 'Schedule (Daily 9AM)',
    actions: 3,
    lastRun: '5 hours ago',
    runsCount: 89,
    successRate: 100,
  },
  {
    id: '3',
    name: 'Overdue Task Escalation',
    description: 'Escalate overdue tasks to managers',
    status: 'paused',
    trigger: 'Task Overdue',
    actions: 4,
    lastRun: '2 days ago',
    runsCount: 56,
    successRate: 94.6,
  },
  {
    id: '4',
    name: 'Sprint Completion Report',
    description: 'Generate and email sprint report',
    status: 'active',
    trigger: 'Sprint End',
    actions: 5,
    lastRun: '1 week ago',
    runsCount: 12,
    successRate: 100,
  },
];

// Trigger types
const triggerTypes = [
  { icon: CheckSquare, label: 'Task Event', description: 'When a task is created, updated, or completed' },
  { icon: Clock, label: 'Schedule', description: 'Run on a recurring schedule' },
  { icon: Mail, label: 'Email', description: 'When an email is received' },
  { icon: MessageSquare, label: 'Slack', description: 'When a Slack message is sent' },
];

// Action types
const actionTypes = [
  { icon: Mail, label: 'Send Email', color: 'bg-blue-500' },
  { icon: MessageSquare, label: 'Send Slack Message', color: 'bg-purple-500' },
  { icon: CheckSquare, label: 'Create Task', color: 'bg-emerald-500' },
  { icon: Bell, label: 'Send Notification', color: 'bg-amber-500' },
  { icon: GitBranch, label: 'Conditional Logic', color: 'bg-pink-500' },
];

// Workflow Card Component
function WorkflowCard({ workflow }: { workflow: Workflow }) {
  const [isEnabled, setIsEnabled] = useState(workflow.status === 'active');

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardContent className="p-5">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-4">
            {/* Status Icon */}
            <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
              workflow.status === 'active' ? 'bg-emerald-500/10' :
              workflow.status === 'paused' ? 'bg-amber-500/10' :
              'bg-slate-500/10'
            }`}>
              <Power className={`w-5 h-5 ${
                workflow.status === 'active' ? 'text-emerald-500' :
                workflow.status === 'paused' ? 'text-amber-500' :
                'text-slate-500'
              }`} />
            </div>

            {/* Info */}
            <div>
              <h3 className="font-semibold">{workflow.name}</h3>
              <p className="text-sm text-muted-foreground mt-1">{workflow.description}</p>
              
              <div className="flex items-center gap-4 mt-3">
                <Badge variant="outline" className="text-xs">
                  <Zap className="w-3 h-3 mr-1" />
                  {workflow.trigger}
                </Badge>
                <span className="text-xs text-muted-foreground">
                  {workflow.actions} actions
                </span>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2">
            <Switch
              checked={isEnabled}
              onCheckedChange={setIsEnabled}
            />
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" className="h-8 w-8">
                  <span className="sr-only">Open menu</span>
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
                  </svg>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem>
                  <Edit3 className="w-4 h-4 mr-2" />
                  Edit
                </DropdownMenuItem>
                <DropdownMenuItem>
                  <Copy className="w-4 h-4 mr-2" />
                  Duplicate
                </DropdownMenuItem>
                <DropdownMenuItem className="text-destructive">
                  <Trash2 className="w-4 h-4 mr-2" />
                  Delete
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>

        {/* Stats */}
        <div className="flex items-center gap-6 mt-4 pt-4 border-t border-border/50">
          <div>
            <p className="text-xs text-muted-foreground">Last Run</p>
            <p className="text-sm font-medium">{workflow.lastRun}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Total Runs</p>
            <p className="text-sm font-medium">{workflow.runsCount.toLocaleString()}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Success Rate</p>
            <p className={`text-sm font-medium ${
              workflow.successRate >= 95 ? 'text-emerald-500' : 'text-amber-500'
            }`}>
              {workflow.successRate}%
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// Visual Workflow Builder Dialog
function WorkflowBuilderDialog({ children }: { children: React.ReactNode }) {
  const nodes = [
    { id: '1', type: 'trigger', label: 'Task Created', x: 100, y: 100 },
    { id: '2', type: 'action', label: 'Send Email', x: 100, y: 250 },
    { id: '3', type: 'action', label: 'Create Task', x: 100, y: 400 },
  ];

  return (
    <Dialog>
      <DialogTrigger asChild>{children}</DialogTrigger>
      <DialogContent className="max-w-5xl h-[80vh]">
        <DialogHeader>
          <DialogTitle>Create Workflow</DialogTitle>
        </DialogHeader>
        
        <div className="flex h-full gap-4">
          {/* Sidebar - Triggers & Actions */}
          <div className="w-64 border-r border-border/50 pr-4 space-y-6 overflow-auto">
            {/* Triggers */}
            <div>
              <h4 className="text-sm font-medium mb-3">Triggers</h4>
              <div className="space-y-2">
                {triggerTypes.map((trigger, index) => {
                  const Icon = trigger.icon;
                  return (
                    <div
                      key={index}
                      className="p-3 rounded-lg border border-border/50 hover:border-primary/50 hover:bg-primary/5 cursor-pointer transition-colors"
                    >
                      <div className="flex items-center gap-2">
                        <Icon className="w-4 h-4 text-primary" />
                        <span className="text-sm font-medium">{trigger.label}</span>
                      </div>
                      <p className="text-xs text-muted-foreground mt-1">{trigger.description}</p>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Actions */}
            <div>
              <h4 className="text-sm font-medium mb-3">Actions</h4>
              <div className="space-y-2">
                {actionTypes.map((action, index) => {
                  const Icon = action.icon;
                  return (
                    <div
                      key={index}
                      className="p-3 rounded-lg border border-border/50 hover:border-primary/50 hover:bg-primary/5 cursor-pointer transition-colors"
                    >
                      <div className="flex items-center gap-2">
                        <div className={`w-6 h-6 rounded ${action.color} flex items-center justify-center`}>
                          <Icon className="w-3 h-3 text-white" />
                        </div>
                        <span className="text-sm font-medium">{action.label}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Canvas */}
          <div className="flex-1 bg-muted/30 rounded-xl relative overflow-hidden">
            {/* Grid Background */}
            <div 
              className="absolute inset-0 opacity-30"
              style={{
                backgroundImage: `
                  linear-gradient(to right, hsl(var(--border)) 1px, transparent 1px),
                  linear-gradient(to bottom, hsl(var(--border)) 1px, transparent 1px)
                `,
                backgroundSize: '20px 20px',
              }}
            />

            {/* Nodes */}
            {nodes.map((node, index) => (
              <motion.div
                key={node.id}
                initial={{ scale: 0, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ delay: index * 0.1 }}
                className="absolute"
                style={{ left: node.x, top: node.y }}
              >
                <div className="relative">
                  {/* Connection Line */}
                  {index < nodes.length - 1 && (
                    <div className="absolute left-1/2 top-full w-px h-[100px] bg-primary/30 -translate-x-1/2">
                      <div className="absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-1/2">
                        <div className="w-2 h-2 bg-primary rounded-full" />
                      </div>
                    </div>
                  )}
                  
                  {/* Node */}
                  <div className={`w-48 p-4 rounded-xl border-2 ${
                    node.type === 'trigger' 
                      ? 'bg-primary/10 border-primary' 
                      : 'bg-card border-border hover:border-primary/50'
                  } transition-colors cursor-pointer shadow-lg`}>
                    <div className="flex items-center gap-2">
                      {node.type === 'trigger' ? (
                        <Zap className="w-4 h-4 text-primary" />
                      ) : (
                        <Play className="w-4 h-4 text-muted-foreground" />
                      )}
                      <span className="font-medium text-sm">{node.label}</span>
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}

            {/* Add Node Button */}
            <Button
              variant="outline"
              size="sm"
              className="absolute bottom-4 right-4 gap-2"
            >
              <Plus className="w-4 h-4" />
              Add Node
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

export default function AutomationPage() {
  const [filter, setFilter] = useState<'all' | 'active' | 'paused'>('all');

  const filteredWorkflows = mockWorkflows.filter((w) =>
    filter === 'all' ? true : w.status === filter
  );

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <h1 className="text-2xl lg:text-3xl font-bold">Automation</h1>
            <p className="text-muted-foreground mt-1">
              Build powerful workflows to automate your tasks
            </p>
          </div>
          <WorkflowBuilderDialog>
            <Button className="gap-2">
              <Plus className="w-4 h-4" />
              Create Workflow
            </Button>
          </WorkflowBuilderDialog>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { label: 'Active Workflows', value: '12', icon: Play, color: 'text-emerald-500' },
            { label: 'Total Runs', value: '1,404', icon: Zap, color: 'text-primary' },
            { label: 'Success Rate', value: '98.2%', icon: CheckCircle2, color: 'text-blue-500' },
            { label: 'Time Saved', value: '48h', icon: Clock, color: 'text-amber-500' },
          ].map((stat, index) => {
            const Icon = stat.icon;
            return (
              <Card key={index}>
                <CardContent className="p-4">
                  <div className="flex items-center gap-3">
                    <Icon className={`w-5 h-5 ${stat.color}`} />
                    <div>
                      <p className="text-2xl font-bold">{stat.value}</p>
                      <p className="text-xs text-muted-foreground">{stat.label}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* Filter Tabs */}
        <div className="flex items-center gap-2">
          {(['all', 'active', 'paused'] as const).map((f) => (
            <Button
              key={f}
              variant={filter === f ? 'default' : 'outline'}
              size="sm"
              onClick={() => setFilter(f)}
              className="capitalize"
            >
              {f}
            </Button>
          ))}
        </div>

        {/* Workflows Grid */}
        <div className="grid gap-4">
          {filteredWorkflows.map((workflow) => (
            <WorkflowCard key={workflow.id} workflow={workflow} />
          ))}
        </div>

        {/* Empty State */}
        {filteredWorkflows.length === 0 && (
          <Card className="py-16">
            <CardContent className="text-center">
              <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mx-auto mb-4">
                <Zap className="w-8 h-8 text-muted-foreground" />
              </div>
              <h3 className="text-lg font-medium mb-2">No workflows found</h3>
              <p className="text-muted-foreground mb-4">
                Create your first automation to get started
              </p>
              <WorkflowBuilderDialog>
                <Button>Create Workflow</Button>
              </WorkflowBuilderDialog>
            </CardContent>
          </Card>
        )}
      </div>
    </DashboardLayout>
  );
}

import { useState } from 'react';
import {
  Plus,
  Search,
  MoreHorizontal,
  Mail,
  Shield,
  User,
  Crown,
  Eye,
  CheckCircle2,
  Filter,
  Download,
  Trash2,
  Edit3,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
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
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import DashboardLayout from '@/components/layout/DashboardLayout';

// Team member types
interface TeamMember {
  id: string;
  name: string;
  email: string;
  role: 'admin' | 'manager' | 'member' | 'viewer';
  status: 'active' | 'invited' | 'inactive';
  avatar?: string;
  tasksCompleted: number;
  tasksInProgress: number;
  efficiency: number;
  lastActive: string;
}

// Mock team data
const mockTeam: TeamMember[] = [
  {
    id: '1',
    name: 'Alex Johnson',
    email: 'alex@company.com',
    role: 'admin',
    status: 'active',
    tasksCompleted: 127,
    tasksInProgress: 5,
    efficiency: 94,
    lastActive: '2 min ago',
  },
  {
    id: '2',
    name: 'Sarah Chen',
    email: 'sarah@company.com',
    role: 'manager',
    status: 'active',
    tasksCompleted: 89,
    tasksInProgress: 8,
    efficiency: 96,
    lastActive: '15 min ago',
  },
  {
    id: '3',
    name: 'Mike Rodriguez',
    email: 'mike@company.com',
    role: 'member',
    status: 'active',
    tasksCompleted: 64,
    tasksInProgress: 4,
    efficiency: 88,
    lastActive: '1 hour ago',
  },
  {
    id: '4',
    name: 'Emma Watson',
    email: 'emma@company.com',
    role: 'member',
    status: 'active',
    tasksCompleted: 72,
    tasksInProgress: 6,
    efficiency: 92,
    lastActive: '30 min ago',
  },
  {
    id: '5',
    name: 'John Smith',
    email: 'john@company.com',
    role: 'viewer',
    status: 'invited',
    tasksCompleted: 0,
    tasksInProgress: 0,
    efficiency: 0,
    lastActive: 'Never',
  },
];

// Role configuration
const roleConfig = {
  admin: { icon: Crown, color: 'text-amber-500', bg: 'bg-amber-500/10', label: 'Admin' },
  manager: { icon: Shield, color: 'text-blue-500', bg: 'bg-blue-500/10', label: 'Manager' },
  member: { icon: User, color: 'text-emerald-500', bg: 'bg-emerald-500/10', label: 'Member' },
  viewer: { icon: Eye, color: 'text-slate-500', bg: 'bg-slate-500/10', label: 'Viewer' },
};

// Status configuration
const statusConfig = {
  active: { color: 'text-emerald-500', bg: 'bg-emerald-500/10', label: 'Active' },
  invited: { color: 'text-amber-500', bg: 'bg-amber-500/10', label: 'Invited' },
  inactive: { color: 'text-slate-500', bg: 'bg-slate-500/10', label: 'Inactive' },
};

// Permission matrix
const permissions = [
  { name: 'Create Tasks', admin: true, manager: true, member: true, viewer: false },
  { name: 'Edit All Tasks', admin: true, manager: true, member: false, viewer: false },
  { name: 'Delete Tasks', admin: true, manager: false, member: false, viewer: false },
  { name: 'Manage Team', admin: true, manager: true, member: false, viewer: false },
  { name: 'View Analytics', admin: true, manager: true, member: true, viewer: true },
  { name: 'Create Automations', admin: true, manager: true, member: false, viewer: false },
  { name: 'Access AI Features', admin: true, manager: true, member: true, viewer: false },
  { name: 'Manage Settings', admin: true, manager: false, member: false, viewer: false },
];

export default function TeamPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState('members');

  const filteredTeam = mockTeam.filter((member) =>
    member.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    member.email.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const activeMembers = mockTeam.filter((m) => m.status === 'active').length;
  const totalTasks = mockTeam.reduce((acc, m) => acc + m.tasksCompleted, 0);
  const avgEfficiency = Math.round(
    mockTeam.filter((m) => m.status === 'active').reduce((acc, m) => acc + m.efficiency, 0) /
      activeMembers
  );

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <h1 className="text-2xl lg:text-3xl font-bold">Team</h1>
            <p className="text-muted-foreground mt-1">
              Manage team members and their permissions
            </p>
          </div>
          <Dialog>
            <DialogTrigger asChild>
              <Button className="gap-2">
                <Plus className="w-4 h-4" />
                Invite Member
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Invite Team Member</DialogTitle>
              </DialogHeader>
              <div className="space-y-4 pt-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">Email Address</label>
                  <Input placeholder="colleague@company.com" />
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">Role</label>
                  <div className="grid grid-cols-2 gap-2">
                    {Object.entries(roleConfig).map(([key, config]) => {
                      const Icon = config.icon;
                      return (
                        <button
                          key={key}
                          className="flex items-center gap-2 p-3 rounded-lg border border-border/50 hover:border-primary/50 hover:bg-primary/5 transition-colors text-left"
                        >
                          <div className={`w-8 h-8 rounded-lg ${config.bg} flex items-center justify-center`}>
                            <Icon className={`w-4 h-4 ${config.color}`} />
                          </div>
                          <div>
                            <p className="font-medium text-sm">{config.label}</p>
                          </div>
                        </button>
                      );
                    })}
                  </div>
                </div>
                <Button className="w-full">Send Invitation</Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { label: 'Total Members', value: mockTeam.length, icon: User },
            { label: 'Active Now', value: activeMembers, icon: CheckCircle2 },
            { label: 'Tasks Completed', value: totalTasks.toLocaleString(), icon: CheckCircle2 },
            { label: 'Avg Efficiency', value: `${avgEfficiency}%`, icon: Shield },
          ].map((stat, index) => {
            const Icon = stat.icon;
            return (
              <Card key={index}>
                <CardContent className="p-4">
                  <div className="flex items-center gap-3">
                    <Icon className="w-5 h-5 text-primary" />
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

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList>
            <TabsTrigger value="members">Members</TabsTrigger>
            <TabsTrigger value="permissions">Permissions</TabsTrigger>
            <TabsTrigger value="activity">Activity</TabsTrigger>
          </TabsList>

          {/* Members Tab */}
          {activeTab === 'members' && (
            <div className="mt-6 space-y-4">
              {/* Search & Filter */}
              <div className="flex gap-2">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <Input
                    placeholder="Search members..."
                    className="pl-10"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                  />
                </div>
                <Button variant="outline" className="gap-2">
                  <Filter className="w-4 h-4" />
                  Filter
                </Button>
                <Button variant="outline" className="gap-2">
                  <Download className="w-4 h-4" />
                  Export
                </Button>
              </div>

              {/* Members Table */}
              <Card>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Member</TableHead>
                      <TableHead>Role</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Tasks</TableHead>
                      <TableHead>Efficiency</TableHead>
                      <TableHead>Last Active</TableHead>
                      <TableHead className="w-10"></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredTeam.map((member) => {
                      const role = roleConfig[member.role];
                      const status = statusConfig[member.status];
                      const RoleIcon = role.icon;

                      return (
                        <TableRow key={member.id}>
                          <TableCell>
                            <div className="flex items-center gap-3">
                              <Avatar className="w-10 h-10">
                                <AvatarFallback className="bg-primary/10 text-primary">
                                  {member.name.charAt(0)}
                                </AvatarFallback>
                              </Avatar>
                              <div>
                                <p className="font-medium">{member.name}</p>
                                <p className="text-sm text-muted-foreground">{member.email}</p>
                              </div>
                            </div>
                          </TableCell>
                          <TableCell>
                            <Badge variant="outline" className={`gap-1 ${role.color}`}>
                              <RoleIcon className="w-3 h-3" />
                              {role.label}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <Badge variant="secondary" className={`${status.color} ${status.bg}`}>
                              {status.label}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <div className="text-sm">
                              <span className="font-medium">{member.tasksCompleted}</span>
                              <span className="text-muted-foreground"> / {member.tasksInProgress} in progress</span>
                            </div>
                          </TableCell>
                          <TableCell>
                            <div className="flex items-center gap-2">
                              <Progress value={member.efficiency} className="w-16 h-2" />
                              <span className="text-sm">{member.efficiency}%</span>
                            </div>
                          </TableCell>
                          <TableCell>
                            <span className="text-sm text-muted-foreground">{member.lastActive}</span>
                          </TableCell>
                          <TableCell>
                            <DropdownMenu>
                              <DropdownMenuTrigger asChild>
                                <Button variant="ghost" size="icon" className="h-8 w-8">
                                  <MoreHorizontal className="w-4 h-4" />
                                </Button>
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end">
                                <DropdownMenuItem>
                                  <Edit3 className="w-4 h-4 mr-2" />
                                  Edit Role
                                </DropdownMenuItem>
                                <DropdownMenuItem>
                                  <Mail className="w-4 h-4 mr-2" />
                                  Send Message
                                </DropdownMenuItem>
                                <DropdownMenuItem className="text-destructive">
                                  <Trash2 className="w-4 h-4 mr-2" />
                                  Remove
                                </DropdownMenuItem>
                              </DropdownMenuContent>
                            </DropdownMenu>
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </Card>
            </div>
          )}

          {/* Permissions Tab */}
          {activeTab === 'permissions' && (
            <div className="mt-6">
              <Card>
                <CardHeader>
                  <CardTitle>Role Permissions</CardTitle>
                </CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Permission</TableHead>
                        <TableHead className="text-center">Admin</TableHead>
                        <TableHead className="text-center">Manager</TableHead>
                        <TableHead className="text-center">Member</TableHead>
                        <TableHead className="text-center">Viewer</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {permissions.map((perm, index) => (
                        <TableRow key={index}>
                          <TableCell className="font-medium">{perm.name}</TableCell>
                          <TableCell className="text-center">
                            {perm.admin ? (
                              <CheckCircle2 className="w-5 h-5 text-emerald-500 mx-auto" />
                            ) : (
                              <span className="text-muted-foreground">—</span>
                            )}
                          </TableCell>
                          <TableCell className="text-center">
                            {perm.manager ? (
                              <CheckCircle2 className="w-5 h-5 text-emerald-500 mx-auto" />
                            ) : (
                              <span className="text-muted-foreground">—</span>
                            )}
                          </TableCell>
                          <TableCell className="text-center">
                            {perm.member ? (
                              <CheckCircle2 className="w-5 h-5 text-emerald-500 mx-auto" />
                            ) : (
                              <span className="text-muted-foreground">—</span>
                            )}
                          </TableCell>
                          <TableCell className="text-center">
                            {perm.viewer ? (
                              <CheckCircle2 className="w-5 h-5 text-emerald-500 mx-auto" />
                            ) : (
                              <span className="text-muted-foreground">—</span>
                            )}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Activity Tab */}
          {activeTab === 'activity' && (
            <div className="mt-6">
              <Card>
                <CardHeader>
                  <CardTitle>Recent Activity</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {[
                      { user: 'Alex Johnson', action: 'completed task', target: 'Update API docs', time: '2 min ago' },
                      { user: 'Sarah Chen', action: 'created task', target: 'Design review', time: '15 min ago' },
                      { user: 'Mike Rodriguez', action: 'commented on', target: 'Bug fix #234', time: '1 hour ago' },
                      { user: 'Emma Watson', action: 'assigned task to', target: 'John Smith', time: '2 hours ago' },
                      { user: 'John Smith', action: 'joined the team', target: '', time: '1 day ago' },
                    ].map((activity, index) => (
                      <div key={index} className="flex items-center gap-4">
                        <Avatar className="w-8 h-8">
                          <AvatarFallback className="text-xs bg-primary/10 text-primary">
                            {activity.user.charAt(0)}
                          </AvatarFallback>
                        </Avatar>
                        <div className="flex-1">
                          <p className="text-sm">
                            <span className="font-medium">{activity.user}</span>
                            {' '}{activity.action}{' '}
                            {activity.target && <span className="font-medium">{activity.target}</span>}
                          </p>
                          <p className="text-xs text-muted-foreground">{activity.time}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </Tabs>
      </div>
    </DashboardLayout>
  );
}

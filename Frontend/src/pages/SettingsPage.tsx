import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  User,
  Palette,
  Bell,
  Shield,
  Key,
  Eye,
  EyeOff,
  Check,
  Upload,
  Trash2,
  Save,
  Sun,
  Moon,
  Monitor,
  Loader2,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { toast } from 'sonner';
import DashboardLayout from '@/components/layout/DashboardLayout';
import { useThemeStore, type ThemeMode, type AccentColor } from '@/store/themeStore';
import { useAuthStore } from '@/store/authStore';
import { settingsService } from '@/services/settings.service';
import { notificationsService } from '@/services/notifications.service';
import { queryKeys } from '@/hooks/useApi';
import { splitFullName } from '@/types/mappers';
import { getApiErrorMessage } from '@/lib/api-client';

// Accent color options
const accentColors: { value: AccentColor; label: string; gradient: string }[] = [
  { value: 'purple', label: 'Purple', gradient: 'from-violet-500 to-purple-500' },
  { value: 'blue', label: 'Blue', gradient: 'from-blue-500 to-cyan-500' },
  { value: 'cyan', label: 'Cyan', gradient: 'from-cyan-500 to-teal-500' },
  { value: 'green', label: 'Green', gradient: 'from-emerald-500 to-green-500' },
  { value: 'orange', label: 'Orange', gradient: 'from-orange-500 to-amber-500' },
  { value: 'pink', label: 'Pink', gradient: 'from-pink-500 to-rose-500' },
];

// Profile Section
function ProfileSection() {
  const { user, updateUser } = useAuthStore();
  const [formData, setFormData] = useState({
    name: user?.name || '',
    email: user?.email || '',
    bio: '',
    company: '',
    role: '',
  });

  const saveMutation = useMutation({
    mutationFn: async () => {
      if (!user?.id) throw new Error('Not logged in');
      const { firstName, lastName } = splitFullName(formData.name);
      await settingsService.updateProfile(user.id, {
        first_name: firstName,
        last_name: lastName,
      });
    },
    onSuccess: () => {
      updateUser({ name: formData.name });
      toast.success('Profile updated successfully');
    },
    onError: (err) => toast.error(getApiErrorMessage(err)),
  });

  const handleSave = () => saveMutation.mutate();

  return (
    <div className="space-y-6">
      {/* Avatar */}
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center gap-6">
            <div className="relative">
              <Avatar className="w-24 h-24">
                <AvatarImage src="" />
                <AvatarFallback className="text-3xl bg-primary/10 text-primary">
                  {user?.name?.charAt(0).toUpperCase() || 'U'}
                </AvatarFallback>
              </Avatar>
              <Button size="icon" className="absolute -bottom-2 -right-2 w-8 h-8 rounded-full">
                <Upload className="w-4 h-4" />
              </Button>
            </div>
            <div>
              <h3 className="font-semibold">Profile Picture</h3>
              <p className="text-sm text-muted-foreground mb-3">
                Recommended: 400x400px PNG or JPG
              </p>
              <div className="flex gap-2">
                <Button variant="outline" size="sm">Upload New</Button>
                <Button variant="outline" size="sm" className="text-destructive">
                  <Trash2 className="w-4 h-4 mr-2" />
                  Remove
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Personal Info */}
      <Card>
        <CardHeader>
          <CardTitle>Personal Information</CardTitle>
          <CardDescription>Update your personal details</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="name">Full Name</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">Email Address</Label>
              <Input
                id="email"
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              />
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="bio">Bio</Label>
            <Input
              id="bio"
              placeholder="Tell us about yourself..."
              value={formData.bio}
              onChange={(e) => setFormData({ ...formData, bio: e.target.value })}
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="company">Company</Label>
              <Input
                id="company"
                placeholder="Your company"
                value={formData.company}
                onChange={(e) => setFormData({ ...formData, company: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="role">Job Title</Label>
              <Input
                id="role"
                placeholder="Your role"
                value={formData.role}
                onChange={(e) => setFormData({ ...formData, role: e.target.value })}
              />
            </div>
          </div>
          <Button onClick={handleSave} className="gap-2" disabled={saveMutation.isPending}>
            {saveMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
            Save Changes
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}

// Appearance Section
function AppearanceSection() {
  const { mode, accent, setMode, setAccent } = useThemeStore();

  return (
    <div className="space-y-6">
      {/* Theme Mode */}
      <Card>
        <CardHeader>
          <CardTitle>Theme</CardTitle>
          <CardDescription>Choose your preferred color scheme</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4">
            {[
              { value: 'light', label: 'Light', icon: Sun },
              { value: 'dark', label: 'Dark', icon: Moon },
              { value: 'system', label: 'System', icon: Monitor },
            ].map((theme) => {
              const Icon = theme.icon;
              const isActive = mode === theme.value;
              
              return (
                <button
                  key={theme.value}
                  onClick={() => setMode(theme.value as ThemeMode)}
                  className={`flex flex-col items-center gap-3 p-4 rounded-xl border-2 transition-all ${
                    isActive
                      ? 'border-primary bg-primary/5'
                      : 'border-border hover:border-primary/50'
                  }`}
                >
                  <Icon className={`w-6 h-6 ${isActive ? 'text-primary' : 'text-muted-foreground'}`} />
                  <span className={`font-medium ${isActive ? 'text-primary' : ''}`}>{theme.label}</span>
                  {isActive && <Check className="w-4 h-4 text-primary absolute top-2 right-2" />}
                </button>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Accent Color */}
      <Card>
        <CardHeader>
          <CardTitle>Accent Color</CardTitle>
          <CardDescription>Choose your preferred accent color</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 sm:grid-cols-6 gap-4">
            {accentColors.map((color) => {
              const isActive = accent === color.value;
              
              return (
                <button
                  key={color.value}
                  onClick={() => setAccent(color.value)}
                  className={`flex flex-col items-center gap-2 p-3 rounded-xl border-2 transition-all relative ${
                    isActive
                      ? 'border-primary'
                      : 'border-border hover:border-primary/50'
                  }`}
                >
                  <div className={`w-10 h-10 rounded-full bg-gradient-to-br ${color.gradient}`} />
                  <span className="text-xs font-medium">{color.label}</span>
                  {isActive && (
                    <div className="absolute top-1 right-1 w-5 h-5 rounded-full bg-primary flex items-center justify-center">
                      <Check className="w-3 h-3 text-white" />
                    </div>
                  )}
                </button>
              );
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// Notifications Section
function NotificationsSection() {
  const [settings, setSettings] = useState({
    emailNotifications: true,
    pushNotifications: true,
    taskAssignments: true,
    taskDueDates: true,
    mentions: true,
    teamUpdates: false,
    weeklyDigest: true,
    marketingEmails: false,
  });

  // Load notification preferences from API
  const { data: prefs } = useQuery({
    queryKey: queryKeys.notifications.preferences,
    queryFn: () => notificationsService.getPreferences(),
  });

  // Sync API prefs into local state when loaded
  useState(() => {
    if (prefs) {
      setSettings((prev) => ({
        ...prev,
        emailNotifications: prefs.email_enabled ?? prev.emailNotifications,
        pushNotifications: prefs.push_enabled ?? prev.pushNotifications,
      }));
    }
  });

  const prefsMutation = useMutation({
    mutationFn: (update: { email_enabled?: boolean; push_enabled?: boolean }) =>
      notificationsService.updatePreferences(update),
    onSuccess: () => toast.success('Preferences saved'),
    onError: (err) => toast.error(getApiErrorMessage(err)),
  });

  const toggleSetting = (key: keyof typeof settings) => {
    const newValue = !settings[key];
    setSettings((prev) => ({ ...prev, [key]: newValue }));

    // Sync email/push toggles to API
    if (key === 'emailNotifications') {
      prefsMutation.mutate({ email_enabled: newValue });
    } else if (key === 'pushNotifications') {
      prefsMutation.mutate({ push_enabled: newValue });
    }
  };

  return (
    <div className="space-y-6">
      {/* Email Notifications */}
      <Card>
        <CardHeader>
          <CardTitle>Email Notifications</CardTitle>
          <CardDescription>Configure which emails you receive</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {[
            { key: 'taskAssignments', label: 'Task Assignments', description: 'When someone assigns you a task' },
            { key: 'taskDueDates', label: 'Due Date Reminders', description: 'Reminders before task deadlines' },
            { key: 'mentions', label: 'Mentions', description: 'When someone mentions you in a comment' },
            { key: 'teamUpdates', label: 'Team Updates', description: 'Updates about your team activity' },
            { key: 'weeklyDigest', label: 'Weekly Digest', description: 'Summary of your week every Monday' },
            { key: 'marketingEmails', label: 'Marketing Emails', description: 'Product updates and promotions' },
          ].map((item) => (
            <div key={item.key} className="flex items-center justify-between">
              <div>
                <p className="font-medium">{item.label}</p>
                <p className="text-sm text-muted-foreground">{item.description}</p>
              </div>
              <Switch
                checked={settings[item.key as keyof typeof settings]}
                onCheckedChange={() => toggleSetting(item.key as keyof typeof settings)}
              />
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Push Notifications */}
      <Card>
        <CardHeader>
          <CardTitle>Push Notifications</CardTitle>
          <CardDescription>Configure browser and mobile notifications</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">Enable Push Notifications</p>
              <p className="text-sm text-muted-foreground">Receive notifications in your browser</p>
            </div>
            <Switch
              checked={settings.pushNotifications}
              onCheckedChange={() => toggleSetting('pushNotifications')}
            />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// Security Section
function SecuritySection() {
  const [showPassword, setShowPassword] = useState(false);
  const [pwForm, setPwForm] = useState({ current: '', newPw: '', confirm: '' });

  const pwMutation = useMutation({
    mutationFn: () => settingsService.changePassword({
      current_password: pwForm.current,
      new_password: pwForm.newPw,
    }),
    onSuccess: () => {
      toast.success('Password updated');
      setPwForm({ current: '', newPw: '', confirm: '' });
    },
    onError: (err) => toast.error(getApiErrorMessage(err)),
  });

  const handlePasswordUpdate = () => {
    if (pwForm.newPw !== pwForm.confirm) {
      toast.error('Passwords do not match');
      return;
    }
    if (pwForm.newPw.length < 8) {
      toast.error('Password must be at least 8 characters');
      return;
    }
    pwMutation.mutate();
  };

  return (
    <div className="space-y-6">
      {/* Password */}
      <Card>
        <CardHeader>
          <CardTitle>Password</CardTitle>
          <CardDescription>Update your password</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="current">Current Password</Label>
            <div className="relative">
              <Input
                id="current"
                type={showPassword ? 'text' : 'password'}
                placeholder="Enter current password"
                value={pwForm.current}
                onChange={(e) => setPwForm({ ...pwForm, current: e.target.value })}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground"
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="new">New Password</Label>
            <Input
              id="new"
              type="password"
              placeholder="Enter new password"
              value={pwForm.newPw}
              onChange={(e) => setPwForm({ ...pwForm, newPw: e.target.value })}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="confirm">Confirm New Password</Label>
            <Input
              id="confirm"
              type="password"
              placeholder="Confirm new password"
              value={pwForm.confirm}
              onChange={(e) => setPwForm({ ...pwForm, confirm: e.target.value })}
            />
          </div>
          <Button
            onClick={handlePasswordUpdate}
            disabled={!pwForm.current || !pwForm.newPw || !pwForm.confirm || pwMutation.isPending}
          >
            {pwMutation.isPending && <Loader2 className="w-4 h-4 animate-spin mr-2" />}
            Update Password
          </Button>
        </CardContent>
      </Card>

      {/* Two-Factor Authentication */}
      <Card>
        <CardHeader>
          <CardTitle>Two-Factor Authentication</CardTitle>
          <CardDescription>Add an extra layer of security</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                <Shield className="w-5 h-5 text-primary" />
              </div>
              <div>
                <p className="font-medium">Authenticator App</p>
                <p className="text-sm text-muted-foreground">Use an authenticator app to generate codes</p>
              </div>
            </div>
            <Button variant="outline">Enable</Button>
          </div>
        </CardContent>
      </Card>

      {/* API Keys */}
      <Card>
        <CardHeader>
          <CardTitle>API Keys</CardTitle>
          <CardDescription>Manage your API access</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between p-4 border border-border/50 rounded-lg">
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                <Key className="w-5 h-5 text-primary" />
              </div>
              <div>
                <p className="font-medium">Production API Key</p>
                <p className="text-sm text-muted-foreground font-mono">••••••••••••••••</p>
              </div>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" size="sm">Reveal</Button>
              <Button variant="outline" size="sm">Regenerate</Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default function SettingsPage() {
  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Settings</h1>
          <p className="text-muted-foreground mt-1">
            Manage your account settings and preferences
          </p>
        </div>

        {/* Settings Tabs */}
        <Tabs defaultValue="profile" className="space-y-6">
          <TabsList className="grid grid-cols-2 lg:grid-cols-4 w-full lg:w-auto">
            <TabsTrigger value="profile" className="gap-2">
              <User className="w-4 h-4" />
              <span className="hidden sm:inline">Profile</span>
            </TabsTrigger>
            <TabsTrigger value="appearance" className="gap-2">
              <Palette className="w-4 h-4" />
              <span className="hidden sm:inline">Appearance</span>
            </TabsTrigger>
            <TabsTrigger value="notifications" className="gap-2">
              <Bell className="w-4 h-4" />
              <span className="hidden sm:inline">Notifications</span>
            </TabsTrigger>
            <TabsTrigger value="security" className="gap-2">
              <Shield className="w-4 h-4" />
              <span className="hidden sm:inline">Security</span>
            </TabsTrigger>
          </TabsList>

          <TabsContent value="profile">
            <ProfileSection />
          </TabsContent>

          <TabsContent value="appearance">
            <AppearanceSection />
          </TabsContent>

          <TabsContent value="notifications">
            <NotificationsSection />
          </TabsContent>

          <TabsContent value="security">
            <SecuritySection />
          </TabsContent>
        </Tabs>
      </div>
    </DashboardLayout>
  );
}

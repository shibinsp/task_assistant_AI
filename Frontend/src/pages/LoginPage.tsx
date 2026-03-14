import { useState } from 'react';
import { motion } from 'framer-motion';
import { Link, useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import {
  Mail,
  Lock,
  Eye,
  EyeOff,
  ArrowRight,
  Github,
  Loader2
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { Separator } from '@/components/ui/separator';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogTrigger,
} from '@/components/ui/dialog';
import { useAuthStore } from '@/store/authStore';
import { authService } from '@/services/auth.service';
import { getApiErrorMessage } from '@/lib/api-client';
import { toast } from 'sonner';

function ForgotPasswordDialog() {
  const [email, setEmail] = useState('');
  const [open, setOpen] = useState(false);

  const forgotMutation = useMutation({
    mutationFn: (emailAddr: string) => authService.forgotPassword(emailAddr),
    onSuccess: () => {
      toast.success('Password reset email sent. Check your inbox.');
      setOpen(false);
      setEmail('');
    },
    onError: (err) => toast.error(getApiErrorMessage(err)),
  });

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <button type="button" className="text-sm text-primary hover:underline">
          Forgot password?
        </button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Reset Password</DialogTitle>
          <DialogDescription>
            Enter your email address and we'll send you a link to reset your password.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4 pt-2">
          <div className="space-y-2">
            <Label htmlFor="reset-email">Email</Label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                id="reset-email"
                type="email"
                placeholder="you@example.com"
                className="pl-10"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
          </div>
          <Button
            onClick={() => forgotMutation.mutate(email)}
            disabled={!email || forgotMutation.isPending}
            className="w-full gap-2"
          >
            {forgotMutation.isPending ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Mail className="w-4 h-4" />
            )}
            Send Reset Link
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

export default function LoginPage() {
  const navigate = useNavigate();
  const { login, oauthLogin, isLoading } = useAuthStore();
  const [showPassword, setShowPassword] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    rememberMe: false,
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.email || !formData.password) {
      toast.error('Please fill in all fields');
      return;
    }

    try {
      await login(formData.email, formData.password);
      toast.success('Welcome back!');
      navigate('/dashboard');
    } catch (error) {
      toast.error(getApiErrorMessage(error));
    }
  };

  return (
    <div className="min-h-screen flex">
      {/* Left Side - Form */}
      <motion.div
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.5 }}
        className="flex-1 flex items-center justify-center px-4 sm:px-6 lg:px-8 xl:px-12 py-12"
      >
        <div className="w-full max-w-md">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 mb-8">
            <img src="/beeax-logo.jpeg" alt="TaskPulse" className="w-10 h-10 rounded-xl object-cover" />
            <span className="text-xl font-bold">TaskPulse</span>
          </Link>

          {/* Heading */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold mb-2">Welcome back</h1>
            <p className="text-muted-foreground">
              Sign in to your account to continue
            </p>
          </div>

          {/* Social Login */}
          <div className="mb-6 space-y-3">
            <Button
              variant="outline"
              className="gap-2 w-full"
              onClick={async () => {
                try {
                  await oauthLogin();
                } catch (error) {
                  toast.error(getApiErrorMessage(error));
                }
              }}
            >
              <svg className="w-4 h-4" viewBox="0 0 24 24">
                <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"/>
                <path fill="currentColor" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                <path fill="currentColor" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                <path fill="currentColor" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
              </svg>
              Google
            </Button>
            <Button variant="outline" className="gap-2 w-full">
              <Github className="w-4 h-4" />
              GitHub
            </Button>
          </div>

          <div className="relative mb-6">
            <Separator />
            <span className="absolute left-1/2 -translate-x-1/2 -translate-y-1/2 bg-background px-2 text-xs text-muted-foreground">
              Or continue with email
            </span>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                  id="email"
                  type="email"
                  placeholder="you@example.com"
                  className="pl-10"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Enter your password"
                  className="pl-10 pr-10"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Checkbox
                  id="remember"
                  checked={formData.rememberMe}
                  onCheckedChange={(checked) => 
                    setFormData({ ...formData, rememberMe: checked as boolean })
                  }
                />
                <Label htmlFor="remember" className="text-sm font-normal cursor-pointer">
                  Remember me
                </Label>
              </div>
              <ForgotPasswordDialog />
            </div>

            <Button type="submit" className="w-full gap-2" disabled={isLoading}>
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Signing in...
                </>
              ) : (
                <>
                  Sign In
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </Button>
          </form>

          {/* Sign Up Link */}
          <p className="mt-6 text-center text-sm text-muted-foreground">
            Don't have an account?{' '}
            <Link to="/signup" className="text-primary hover:underline font-medium">
              Sign up
            </Link>
          </p>
        </div>
      </motion.div>

      {/* Right Side - Image */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5, delay: 0.2 }}
        className="hidden lg:flex flex-1 relative overflow-hidden"
      >
        <div 
          className="absolute inset-0 bg-cover bg-center"
          style={{ backgroundImage: 'url(/hero-dashboard.jpg)' }}
        />
        <div className="absolute inset-0 bg-gradient-to-br from-primary/90 via-primary/80 to-accent-secondary/90" />
        
        {/* Content */}
        <div className="relative z-10 flex flex-col justify-center px-12 text-white">
          <blockquote className="text-2xl font-medium leading-relaxed mb-6">
            "TaskPulse has completely transformed how our team manages projects. 
            The AI insights are game-changing."
          </blockquote>
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-full bg-white/20 flex items-center justify-center text-lg font-medium">
              SC
            </div>
            <div>
              <div className="font-medium">Sarah Chen</div>
              <div className="text-white/70 text-sm">VP of Engineering, TechCorp</div>
            </div>
          </div>
        </div>

        {/* Decorative Elements */}
        <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-background/20 to-transparent" />
      </motion.div>
    </div>
  );
}

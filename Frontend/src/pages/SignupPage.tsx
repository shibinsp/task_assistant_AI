import { useState } from 'react';
import { motion } from 'framer-motion';
import { Link, useNavigate } from 'react-router-dom';
import {
  Mail,
  Lock,
  Eye,
  EyeOff,
  ArrowRight,
  Github,
  Loader2,
  User,
  Building2,
  Shield
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { Separator } from '@/components/ui/separator';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useAuthStore } from '@/store/authStore';
import { getApiErrorMessage } from '@/lib/api-client';
import { toast } from 'sonner';

const SIGNUP_ROLES = [
  { value: 'manager', label: 'Manager', description: 'Manage teams and assign tasks' },
  { value: 'team_lead', label: 'Team Lead', description: 'Lead a team and track progress' },
  { value: 'employee', label: 'Employee', description: 'Work on tasks and report progress' },
  { value: 'viewer', label: 'Viewer', description: 'View tasks and reports (read-only)' },
];

export default function SignupPage() {
  const navigate = useNavigate();
  const { signup, oauthLogin, isLoading } = useAuthStore();
  const [showPassword, setShowPassword] = useState(false);
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    company: '',
    role: 'employee',
    agreeToTerms: false,
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (step === 1) {
      if (!formData.name || !formData.email) {
        toast.error('Please fill in all required fields');
        return;
      }
      if (!formData.company) {
        toast.error('Please enter your company name');
        return;
      }
      setStep(2);
      return;
    }

    if (!formData.password || !formData.agreeToTerms) {
      toast.error('Please fill in all fields and agree to terms');
      return;
    }

    try {
      await signup(formData.email, formData.password, formData.name, formData.company, formData.role);
      toast.success('Account created successfully!');
      navigate('/dashboard');
    } catch (error) {
      toast.error(getApiErrorMessage(error));
    }
  };

  const selectedRole = SIGNUP_ROLES.find(r => r.value === formData.role);

  return (
    <div className="min-h-screen flex">
      {/* Left Side - Form */}
      <motion.div
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.5 }}
        className="flex-1 flex flex-col justify-center px-4 sm:px-6 lg:px-8 xl:px-12 py-12"
      >
        <div className="w-full max-w-md mx-auto">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 mb-8">
            <img src="/beeax-logo.jpeg" alt="TaskPulse" className="w-10 h-10 rounded-xl object-cover" />
            <span className="text-xl font-bold">TaskPulse</span>
          </Link>

          {/* Heading */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold mb-2">
              {step === 1 ? 'Create your account' : 'Set up your password'}
            </h1>
            <p className="text-muted-foreground">
              {step === 1
                ? 'Start your 14-day free trial today'
                : 'Almost there! Create a secure password'}
            </p>
          </div>

          {/* Progress */}
          <div className="flex gap-2 mb-6">
            {[1, 2].map((s) => (
              <div
                key={s}
                className={`h-1 flex-1 rounded-full transition-colors ${
                  s <= step ? 'bg-primary' : 'bg-muted'
                }`}
              />
            ))}
          </div>

          {/* Social Login */}
          {step === 1 && (
            <>
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
            </>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {step === 1 ? (
              <>
                <div className="space-y-2">
                  <Label htmlFor="name">Full Name</Label>
                  <div className="relative">
                    <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                    <Input
                      id="name"
                      type="text"
                      placeholder="John Doe"
                      className="pl-10"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="email">Work Email</Label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                    <Input
                      id="email"
                      type="email"
                      placeholder="you@company.com"
                      className="pl-10"
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="company">Company</Label>
                  <div className="relative">
                    <Building2 className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                    <Input
                      id="company"
                      type="text"
                      placeholder="Your company name"
                      className="pl-10"
                      value={formData.company}
                      onChange={(e) => setFormData({ ...formData, company: e.target.value })}
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="role">Role</Label>
                  <div className="relative">
                    <Shield className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground z-10 pointer-events-none" />
                    <Select
                      value={formData.role}
                      onValueChange={(value) => setFormData({ ...formData, role: value })}
                    >
                      <SelectTrigger className="pl-10">
                        <SelectValue placeholder="Select your role" />
                      </SelectTrigger>
                      <SelectContent>
                        {SIGNUP_ROLES.map((role) => (
                          <SelectItem key={role.value} value={role.value}>
                            <div className="flex flex-col">
                              <span>{role.label}</span>
                            </div>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  {selectedRole && (
                    <p className="text-xs text-muted-foreground">{selectedRole.description}</p>
                  )}
                </div>
              </>
            ) : (
              <>
                <div className="rounded-lg border bg-muted/50 p-3 mb-2">
                  <div className="text-sm text-muted-foreground">Signing up as</div>
                  <div className="font-medium">{formData.name} &middot; {selectedRole?.label}</div>
                  <div className="text-sm text-muted-foreground">{formData.email} &middot; {formData.company}</div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="password">Password</Label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                    <Input
                      id="password"
                      type={showPassword ? 'text' : 'password'}
                      placeholder="Create a strong password"
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
                  <p className="text-xs text-muted-foreground">
                    Must be at least 8 characters with uppercase, lowercase, and number
                  </p>
                </div>

                <div className="flex items-start gap-2">
                  <Checkbox
                    id="terms"
                    checked={formData.agreeToTerms}
                    onCheckedChange={(checked) =>
                      setFormData({ ...formData, agreeToTerms: checked as boolean })
                    }
                  />
                  <Label htmlFor="terms" className="text-sm font-normal cursor-pointer leading-relaxed">
                    I agree to the{' '}
                    <Link to="/terms" className="text-primary hover:underline">Terms of Service</Link>
                    {' '}and{' '}
                    <Link to="/privacy" className="text-primary hover:underline">Privacy Policy</Link>
                  </Label>
                </div>
              </>
            )}

            <div className="flex gap-3">
              {step === 2 && (
                <Button
                  type="button"
                  variant="outline"
                  className="flex-1"
                  onClick={() => setStep(1)}
                >
                  Back
                </Button>
              )}
              <Button type="submit" className="flex-1 gap-2" disabled={isLoading}>
                {isLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Creating account...
                  </>
                ) : (
                  <>
                    {step === 1 ? 'Continue' : 'Create Account'}
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </Button>
            </div>
          </form>

          {/* Sign In Link */}
          <p className="mt-6 text-center text-sm text-muted-foreground">
            Already have an account?{' '}
            <Link to="/login" className="text-primary hover:underline font-medium">
              Sign in
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
          style={{ backgroundImage: 'url(/feature-analytics.jpg)' }}
        />
        <div className="absolute inset-0 bg-gradient-to-br from-primary/90 via-primary/80 to-accent-secondary/90" />

        {/* Content */}
        <div className="relative z-10 flex flex-col justify-center px-12 text-white">
          <div className="mb-8">
            <div className="text-5xl font-bold mb-2">10K+</div>
            <div className="text-white/70">Teams already using TaskPulse</div>
          </div>
          <div className="space-y-4">
            {[
              'Unlimited tasks & projects',
              'AI-powered insights',
              'Advanced automation',
              'Priority support',
            ].map((feature, index) => (
              <div key={index} className="flex items-center gap-3">
                <div className="w-5 h-5 rounded-full bg-white/20 flex items-center justify-center">
                  <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <span>{feature}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Decorative Elements */}
        <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-background/20 to-transparent" />
      </motion.div>
    </div>
  );
}

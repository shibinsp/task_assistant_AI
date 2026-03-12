import { useEffect, useRef, useState } from 'react';
import { motion, useScroll, useTransform, useSpring, useMotionValue, useMotionTemplate } from 'framer-motion';
import {
  Sparkles,
  Zap,
  Shield,
  BarChart3,
  Users,
  Workflow,
  ArrowRight,
  Check,
  Star,
  Play,
  Menu,
  X,
  Moon,
  Sun
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Link } from 'react-router-dom';
import { useThemeStore, applyTheme } from '@/store/themeStore';

// ─── Floating Glassmorphic Shape ────────────────────────────────────────
function FloatingShape({
  className = '',
  delay = 0,
  duration = 6,
  size = 120,
  gradient = 'from-amber-500/20 to-orange-500/10',
  blur = 'blur-2xl',
}: {
  className?: string;
  delay?: number;
  duration?: number;
  size?: number;
  gradient?: string;
  blur?: string;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 1.2, delay }}
      className={`absolute pointer-events-none ${className}`}
    >
      <motion.div
        animate={{
          y: [-20, 20, -20],
          x: [-10, 10, -10],
          rotate: [0, 5, -5, 0],
        }}
        transition={{
          duration,
          repeat: Infinity,
          ease: 'easeInOut',
          delay,
        }}
        style={{ width: size, height: size }}
        className={`rounded-3xl bg-gradient-to-br ${gradient} backdrop-blur-sm border border-border/20 ${blur}`}
      />
    </motion.div>
  );
}

// ─── Theme Toggle Button ────────────────────────────────────────────────
function ThemeToggle() {
  const { mode, toggleMode } = useThemeStore();
  const isDark = mode === 'dark' || (mode === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);

  return (
    <motion.button
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      onClick={toggleMode}
      className="relative w-9 h-9 rounded-xl glass-card border border-border/50 flex items-center justify-center text-muted-foreground hover:text-foreground transition-colors duration-300"
      aria-label="Toggle theme"
    >
      <motion.div
        initial={false}
        animate={{ rotate: isDark ? 180 : 0, scale: isDark ? 0 : 1 }}
        transition={{ duration: 0.3, ease: 'easeInOut' }}
        className="absolute"
      >
        <Sun className="w-4 h-4" />
      </motion.div>
      <motion.div
        initial={false}
        animate={{ rotate: isDark ? 0 : -180, scale: isDark ? 1 : 0 }}
        transition={{ duration: 0.3, ease: 'easeInOut' }}
        className="absolute"
      >
        <Moon className="w-4 h-4" />
      </motion.div>
    </motion.button>
  );
}

// ─── Navigation ─────────────────────────────────────────────────────────
function Navigation() {
  const [isScrolled, setIsScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 50);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const navLinks = [
    { label: 'Features', href: '#features' },
    { label: 'How it Works', href: '#how-it-works' },
    { label: 'Pricing', href: '#pricing' },
    { label: 'Testimonials', href: '#testimonials' },
  ];

  return (
    <motion.nav
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ duration: 0.5, ease: 'easeOut' }}
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ${
        isScrolled
          ? 'glass-card border-b border-border/50'
          : 'bg-transparent'
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 lg:h-20">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2.5 group">
            <img src="/beeax-logo.jpeg" alt="TaskPulse" className="w-9 h-9 lg:w-10 lg:h-10 rounded-xl object-cover shadow-lg shadow-amber-600/25 group-hover:shadow-amber-600/40 transition-shadow duration-300" />
            <span className="text-lg lg:text-xl font-bold tracking-tight">TaskPulse</span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-8">
            {navLinks.map((link) => (
              <a
                key={link.label}
                href={link.href}
                className="text-sm text-muted-foreground hover:text-foreground transition-colors duration-200 relative after:absolute after:bottom-0 after:left-0 after:w-0 after:h-px after:bg-gradient-to-r after:from-amber-600 after:to-orange-500 hover:after:w-full after:transition-all after:duration-300"
              >
                {link.label}
              </a>
            ))}
          </div>

          {/* CTA Buttons + Theme Toggle */}
          <div className="hidden md:flex items-center gap-3">
            <ThemeToggle />
            <Link to="/login">
              <Button variant="ghost" size="sm" className="text-muted-foreground hover:text-foreground">Sign In</Button>
            </Link>
            <Link to="/signup">
              <Button size="sm" className="gap-2 bg-gradient-to-r from-amber-700 to-orange-600 hover:from-amber-600 hover:to-orange-500 border-0 text-white shadow-lg shadow-amber-600/25 hover:shadow-amber-600/40 transition-all duration-300">
                Get Started
                <ArrowRight className="w-4 h-4" />
              </Button>
            </Link>
          </div>

          {/* Mobile: Theme Toggle + Menu Button */}
          <div className="md:hidden flex items-center gap-2">
            <ThemeToggle />
            <button
              className="p-2 text-muted-foreground hover:text-foreground transition-colors"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="md:hidden border-t border-border/50 py-4"
          >
            <div className="flex flex-col gap-4">
              {navLinks.map((link) => (
                <a
                  key={link.label}
                  href={link.href}
                  className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  {link.label}
                </a>
              ))}
              <div className="flex flex-col gap-2 pt-4 border-t border-border/50">
                <Link to="/login">
                  <Button variant="ghost" className="w-full">Sign In</Button>
                </Link>
                <Link to="/signup">
                  <Button className="w-full gap-2 bg-gradient-to-r from-amber-700 to-orange-600 hover:from-amber-600 hover:to-orange-500 border-0 text-white">
                    Get Started
                    <ArrowRight className="w-4 h-4" />
                  </Button>
                </Link>
              </div>
            </div>
          </motion.div>
        )}
      </div>
    </motion.nav>
  );
}

// ─── Hero Section ───────────────────────────────────────────────────────
function HeroSection() {
  const containerRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ['start start', 'end start'],
  });

  const y = useTransform(scrollYProgress, [0, 1], ['0%', '30%']);
  const opacity = useTransform(scrollYProgress, [0, 0.5], [1, 0]);
  const scale = useTransform(scrollYProgress, [0, 0.5], [1, 0.95]);

  const springY = useSpring(y, { stiffness: 100, damping: 30 });
  const springOpacity = useSpring(opacity, { stiffness: 100, damping: 30 });
  const springScale = useSpring(scale, { stiffness: 100, damping: 30 });

  // Mouse-tracking glow
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);

  const handleMouseMove = (e: React.MouseEvent) => {
    const rect = e.currentTarget.getBoundingClientRect();
    mouseX.set(e.clientX - rect.left);
    mouseY.set(e.clientY - rect.top);
  };

  const glowBackground = useMotionTemplate`radial-gradient(600px circle at ${mouseX}px ${mouseY}px, hsl(var(--primary) / 0.06), transparent 80%)`;

  return (
    <section
      ref={containerRef}
      onMouseMove={handleMouseMove}
      className="relative min-h-screen flex items-center justify-center overflow-hidden"
    >
      {/* Animated Mesh Gradient Background */}
      <motion.div
        style={{ y: springY, scale: springScale }}
        className="absolute inset-0 z-0"
      >
        <div className="absolute inset-0 mesh-gradient" />
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-background/30 to-background" />
      </motion.div>

      {/* Mouse-tracking glow */}
      <motion.div
        style={{ background: glowBackground }}
        className="absolute inset-0 z-[1] pointer-events-none"
      />

      {/* Floating Glassmorphic Shapes */}
      <div className="absolute inset-0 z-[2] overflow-hidden pointer-events-none">
        <FloatingShape
          className="top-[15%] left-[8%]"
          size={180}
          gradient="from-amber-500/15 to-yellow-500/10"
          delay={0}
          duration={7}
          blur="blur-xl"
        />
        <FloatingShape
          className="top-[10%] right-[12%]"
          size={140}
          gradient="from-orange-500/12 to-amber-500/8"
          delay={1}
          duration={8}
          blur="blur-2xl"
        />
        <FloatingShape
          className="bottom-[20%] left-[15%]"
          size={100}
          gradient="from-teal-500/10 to-cyan-500/8"
          delay={2}
          duration={6}
          blur="blur-xl"
        />
        <FloatingShape
          className="bottom-[15%] right-[8%]"
          size={160}
          gradient="from-yellow-500/12 to-amber-500/8"
          delay={0.5}
          duration={9}
          blur="blur-2xl"
        />
        <FloatingShape
          className="top-[50%] left-[50%] -translate-x-1/2 -translate-y-1/2"
          size={220}
          gradient="from-amber-600/8 to-yellow-500/5"
          delay={1.5}
          duration={10}
          blur="blur-3xl"
        />
      </div>

      {/* Animated Particles */}
      <div className="absolute inset-0 z-[3] overflow-hidden pointer-events-none">
        {[...Array(30)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute w-[2px] h-[2px] rounded-full bg-amber-500/30 dark:bg-amber-400/40"
            initial={{
              x: `${Math.random() * 100}%`,
              y: `${Math.random() * 100}%`,
              scale: Math.random() * 0.5 + 0.5,
            }}
            animate={{
              y: [null, '-15%'],
              opacity: [0, 0.8, 0],
            }}
            transition={{
              duration: Math.random() * 6 + 4,
              repeat: Infinity,
              delay: Math.random() * 5,
              ease: 'linear',
            }}
          />
        ))}
      </div>

      {/* Content */}
      <motion.div
        style={{ opacity: springOpacity }}
        className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-24 pb-12"
      >
        <div className="text-center">
          {/* Badge */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
          >
            <Badge
              variant="secondary"
              className="mb-8 px-5 py-2.5 text-sm bg-amber-500/10 text-amber-700 dark:text-amber-300 border border-amber-500/20 backdrop-blur-sm"
            >
              <Sparkles className="w-4 h-4 mr-2" />
              AI-Powered Task Management
            </Badge>
          </motion.div>

          {/* Heading */}
          <motion.h1
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-5xl sm:text-6xl md:text-7xl lg:text-8xl font-bold tracking-tight mb-8"
          >
            <span className="block text-foreground">Work Smarter with</span>
            <span className="block gradient-text mt-2 pb-2">Intelligent Automation</span>
          </motion.h1>

          {/* Subheading */}
          <motion.p
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="text-lg sm:text-xl text-muted-foreground max-w-2xl mx-auto mb-12 leading-relaxed"
          >
            TaskPulse AI transforms how teams work. Automate workflows, predict bottlenecks,
            and achieve more with AI-powered task management that learns and adapts.
          </motion.p>

          {/* CTA Buttons */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="flex flex-col sm:flex-row items-center justify-center gap-4"
          >
            <Link to="/signup">
              <Button size="lg" className="gap-2 text-base px-8 bg-gradient-to-r from-amber-700 to-orange-600 hover:from-amber-600 hover:to-orange-500 border-0 text-white shadow-xl shadow-amber-600/25 hover:shadow-amber-600/40 transition-all duration-300 hover:scale-105">
                Start Free Trial
                <ArrowRight className="w-5 h-5" />
              </Button>
            </Link>
            <Button size="lg" variant="outline" className="gap-2 text-base px-8 glass-card border-border/50 hover:border-primary/30 transition-all duration-300">
              <Play className="w-5 h-5" />
              Watch Demo
            </Button>
          </motion.div>

          {/* Stats */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.6 }}
            className="mt-20 grid grid-cols-2 md:grid-cols-4 gap-8"
          >
            {[
              { value: '10K+', label: 'Active Teams' },
              { value: '1M+', label: 'Tasks Completed' },
              { value: '99.9%', label: 'Uptime' },
              { value: '4.9/5', label: 'User Rating' },
            ].map((stat, index) => (
              <motion.div
                key={index}
                whileHover={{ scale: 1.05 }}
                className="text-center p-4 rounded-2xl glass-card border border-border/30"
              >
                <div className="text-2xl sm:text-3xl font-bold gradient-text">{stat.value}</div>
                <div className="text-sm text-muted-foreground mt-1">{stat.label}</div>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </motion.div>

      {/* Scroll Indicator */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1.2 }}
        className="absolute bottom-8 left-1/2 -translate-x-1/2 z-10"
      >
        <motion.div
          animate={{ y: [0, 8, 0] }}
          transition={{ duration: 1.5, repeat: Infinity }}
          className="w-6 h-10 rounded-full border-2 border-muted-foreground/30 flex items-start justify-center p-2"
        >
          <motion.div className="w-1.5 h-1.5 rounded-full bg-amber-500/60" />
        </motion.div>
      </motion.div>
    </section>
  );
}

// ─── Features Section ───────────────────────────────────────────────────
function FeaturesSection() {
  const features = [
    {
      icon: <Sparkles className="w-6 h-6" />,
      title: 'AI-Powered Insights',
      description: 'Get intelligent recommendations and predictions to optimize your workflow and prevent bottlenecks before they happen.',
      color: 'from-amber-600 to-yellow-600',
    },
    {
      icon: <Workflow className="w-6 h-6" />,
      title: 'Smart Automation',
      description: 'Build powerful workflows with our visual builder. Automate repetitive tasks and focus on what matters most.',
      color: 'from-blue-500 to-cyan-500',
    },
    {
      icon: <BarChart3 className="w-6 h-6" />,
      title: 'Real-time Analytics',
      description: 'Track progress with beautiful dashboards. Understand team velocity, identify trends, and make data-driven decisions.',
      color: 'from-emerald-500 to-teal-500',
    },
    {
      icon: <Users className="w-6 h-6" />,
      title: 'Team Collaboration',
      description: 'Work together seamlessly with real-time updates, comments, and intelligent task assignment based on workload.',
      color: 'from-orange-500 to-amber-500',
    },
    {
      icon: <Shield className="w-6 h-6" />,
      title: 'Enterprise Security',
      description: 'Bank-grade encryption, SSO, and granular permissions. Your data is protected with industry-leading security.',
      color: 'from-red-500 to-rose-500',
    },
    {
      icon: <Zap className="w-6 h-6" />,
      title: 'Lightning Fast',
      description: 'Built for speed. Experience instant updates, smooth animations, and a responsive interface that never slows you down.',
      color: 'from-yellow-500 to-orange-500',
    },
  ];

  return (
    <section id="features" className="py-24 lg:py-32 relative">
      {/* Background Glowing Orbs */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-amber-500/[0.04] rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-orange-500/[0.04] rounded-full blur-3xl" />
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative">
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center mb-20"
        >
          <Badge variant="outline" className="mb-4 border-amber-500/30 text-amber-700 dark:text-amber-300">Features</Badge>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-6">
            Everything you need to{' '}
            <span className="gradient-text">ship faster</span>
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Powerful features designed for modern teams. From AI automation to real-time collaboration,
            TaskPulse has everything you need.
          </p>
        </motion.div>

        {/* Features Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 lg:gap-8">
          {features.map((feature, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              whileHover={{ y: -8, transition: { duration: 0.2 } }}
              className="group relative"
            >
              <div className="relative p-6 lg:p-8 rounded-2xl glass-card border border-border/30 hover:border-primary/30 transition-all duration-500 hover:shadow-2xl hover:shadow-amber-500/[0.08] overflow-hidden">
                {/* Gradient border on hover */}
                <div className="absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 bg-gradient-to-br from-amber-500/10 via-transparent to-orange-500/10 pointer-events-none" />

                {/* Icon */}
                <div className={`relative w-12 h-12 rounded-xl bg-gradient-to-br ${feature.color} flex items-center justify-center text-white mb-5 group-hover:scale-110 group-hover:shadow-lg transition-all duration-300`}>
                  {feature.icon}
                </div>

                {/* Content */}
                <h3 className="text-xl font-semibold mb-3 relative">{feature.title}</h3>
                <p className="text-muted-foreground leading-relaxed relative">
                  {feature.description}
                </p>

                {/* Hover Glow */}
                <div className={`absolute -bottom-8 -right-8 w-40 h-40 bg-gradient-to-br ${feature.color} opacity-0 group-hover:opacity-[0.07] transition-opacity duration-500 blur-3xl rounded-full`} />
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ─── How It Works ───────────────────────────────────────────────────────
function HowItWorksSection() {
  const steps = [
    {
      number: '01',
      title: 'Connect Your Tools',
      description: 'Integrate with your existing stack in minutes. We support 100+ integrations including Slack, GitHub, Jira, and more.',
      image: '/feature-automation.jpg',
    },
    {
      number: '02',
      title: 'Let AI Do the Heavy Lifting',
      description: 'Our AI analyzes your workflow, suggests optimizations, and automates repetitive tasks so you can focus on high-impact work.',
      image: '/hero-dashboard.jpg',
    },
    {
      number: '03',
      title: 'Track & Optimize',
      description: 'Get real-time insights into team performance, identify bottlenecks, and continuously improve your processes.',
      image: '/feature-analytics.jpg',
    },
  ];

  return (
    <section id="how-it-works" className="py-24 lg:py-32 relative overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-amber-500/[0.03] to-transparent" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative">
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center mb-20"
        >
          <Badge variant="outline" className="mb-4 border-amber-500/30 text-amber-700 dark:text-amber-300">How It Works</Badge>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-4">
            Get started in{' '}
            <span className="gradient-text">three simple steps</span>
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            From setup to optimization, TaskPulse makes it easy to transform your workflow.
          </p>
        </motion.div>

        {/* Steps */}
        <div className="space-y-24 lg:space-y-32">
          {steps.map((step, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 50 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className={`grid lg:grid-cols-2 gap-12 lg:gap-20 items-center`}
            >
              {/* Content */}
              <div className={index % 2 === 1 ? 'lg:order-2' : ''}>
                <div className="text-6xl lg:text-8xl font-bold gradient-text opacity-30 mb-4">
                  {step.number}
                </div>
                <h3 className="text-2xl lg:text-3xl font-bold mb-4">{step.title}</h3>
                <p className="text-lg text-muted-foreground leading-relaxed">
                  {step.description}
                </p>
              </div>

              {/* Image */}
              <div className={index % 2 === 1 ? 'lg:order-1' : ''}>
                <motion.div
                  whileHover={{ scale: 1.02 }}
                  transition={{ duration: 0.3 }}
                  className="relative rounded-2xl overflow-hidden shadow-2xl shadow-amber-600/10 border border-border/30"
                >
                  <img
                    src={step.image}
                    alt={step.title}
                    className="w-full aspect-video object-cover"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-background/60 to-transparent" />
                </motion.div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ─── Pricing Section ────────────────────────────────────────────────────
function PricingSection() {
  const plans = [
    {
      name: 'Starter',
      description: 'Perfect for individuals and small teams',
      price: { monthly: 0, annually: 0 },
      features: [
        'Up to 5 team members',
        '100 tasks per month',
        'Basic AI insights',
        '3 workflow automations',
        'Email support',
      ],
      cta: 'Get Started Free',
      popular: false,
    },
    {
      name: 'Pro',
      description: 'For growing teams that need more power',
      price: { monthly: 29, annually: 24 },
      features: [
        'Up to 25 team members',
        'Unlimited tasks',
        'Advanced AI insights',
        'Unlimited automations',
        'Priority support',
        'Custom integrations',
        'Analytics dashboard',
      ],
      cta: 'Start Free Trial',
      popular: true,
    },
    {
      name: 'Enterprise',
      description: 'For large organizations with custom needs',
      price: { monthly: null, annually: null },
      features: [
        'Unlimited team members',
        'Unlimited everything',
        'Custom AI models',
        'Dedicated success manager',
        'SLA guarantee',
        'On-premise deployment',
        'Advanced security',
      ],
      cta: 'Contact Sales',
      popular: false,
    },
  ];

  const [billingCycle, setBillingCycle] = useState<'monthly' | 'annually'>('monthly');

  return (
    <section id="pricing" className="py-24 lg:py-32 relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center mb-12"
        >
          <Badge variant="outline" className="mb-4 border-amber-500/30 text-amber-700 dark:text-amber-300">Pricing</Badge>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-4">
            Simple, transparent{' '}
            <span className="gradient-text">pricing</span>
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Choose the plan that fits your team. All plans include a 14-day free trial.
          </p>
        </motion.div>

        {/* Billing Toggle */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="flex items-center justify-center gap-4 mb-16"
        >
          <span className={`text-sm transition-colors ${billingCycle === 'monthly' ? 'text-foreground' : 'text-muted-foreground'}`}>
            Monthly
          </span>
          <button
            onClick={() => setBillingCycle(billingCycle === 'monthly' ? 'annually' : 'monthly')}
            className="relative w-14 h-7 rounded-full bg-amber-500/20 border border-amber-500/30 transition-colors"
          >
            <motion.div
              animate={{ x: billingCycle === 'annually' ? 28 : 2 }}
              transition={{ type: 'spring', stiffness: 500, damping: 30 }}
              className="absolute top-1 w-5 h-5 rounded-full bg-gradient-to-r from-amber-600 to-orange-500"
            />
          </button>
          <span className={`text-sm transition-colors ${billingCycle === 'annually' ? 'text-foreground' : 'text-muted-foreground'}`}>
            Annually
          </span>
          {billingCycle === 'annually' && (
            <Badge variant="secondary" className="text-xs bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20">Save 20%</Badge>
          )}
        </motion.div>

        {/* Pricing Cards */}
        <div className="grid md:grid-cols-3 gap-6 lg:gap-8 items-start">
          {plans.map((plan, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              className={`relative ${plan.popular ? 'md:-mt-4 md:mb-4' : ''}`}
            >
              {/* Rotating Border for Pro Card */}
              <div className={`relative rounded-2xl p-6 lg:p-8 ${
                plan.popular
                  ? 'rotating-border z-10'
                  : 'glass-card border border-border/30'
              }`}>
                {plan.popular && (
                  <div className="absolute -top-4 left-1/2 -translate-x-1/2 z-20">
                    <Badge className="bg-gradient-to-r from-amber-700 to-orange-600 text-white border-0 shadow-lg shadow-amber-600/25">
                      Most Popular
                    </Badge>
                  </div>
                )}

                <div className="mb-6">
                  <h3 className="text-xl font-semibold mb-2">{plan.name}</h3>
                  <p className="text-sm text-muted-foreground">{plan.description}</p>
                </div>

                <div className="mb-6">
                  {plan.price.monthly !== null ? (
                    <div className="flex items-baseline gap-1">
                      <span className="text-4xl font-bold">
                        ${billingCycle === 'monthly' ? plan.price.monthly : plan.price.annually}
                      </span>
                      <span className="text-muted-foreground">/month</span>
                    </div>
                  ) : (
                    <div className="text-4xl font-bold gradient-text">Custom</div>
                  )}
                </div>

                <ul className="space-y-3 mb-8">
                  {plan.features.map((feature, featureIndex) => (
                    <li key={featureIndex} className="flex items-start gap-3">
                      <Check className={`w-5 h-5 flex-shrink-0 mt-0.5 ${plan.popular ? 'text-amber-700 dark:text-amber-400' : 'text-muted-foreground'}`} />
                      <span className="text-sm text-muted-foreground">{feature}</span>
                    </li>
                  ))}
                </ul>

                <Button
                  className={`w-full ${
                    plan.popular
                      ? 'bg-gradient-to-r from-amber-700 to-orange-600 hover:from-amber-600 hover:to-orange-500 border-0 text-white shadow-lg shadow-amber-600/25 hover:shadow-amber-600/40 transition-all duration-300'
                      : 'glass-card border border-border/50 hover:border-primary/30'
                  }`}
                  variant={plan.popular ? 'default' : 'outline'}
                >
                  {plan.cta}
                </Button>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ─── Testimonials Section ───────────────────────────────────────────────
function TestimonialsSection() {
  const testimonials = [
    {
      quote: "TaskPulse transformed how our team works. The AI insights alone have saved us countless hours every week.",
      author: "Sarah Chen",
      role: "VP of Engineering",
      company: "TechCorp",
      avatar: "SC",
      color: 'from-amber-600 to-yellow-600',
    },
    {
      quote: "The automation features are incredible. We've reduced manual task management by 80% since switching to TaskPulse.",
      author: "Michael Rodriguez",
      role: "Product Manager",
      company: "StartupXYZ",
      avatar: "MR",
      color: 'from-blue-500 to-cyan-500',
    },
    {
      quote: "Best task management tool we've ever used. The AI predictions help us stay ahead of deadlines.",
      author: "Emily Watson",
      role: "Team Lead",
      company: "DesignStudio",
      avatar: "EW",
      color: 'from-orange-500 to-red-500',
    },
  ];

  return (
    <section id="testimonials" className="py-24 lg:py-32 relative overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 bg-gradient-to-b from-amber-500/[0.02] via-transparent to-amber-500/[0.02]" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative">
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <Badge variant="outline" className="mb-4 border-amber-500/30 text-amber-700 dark:text-amber-300">Testimonials</Badge>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-4">
            Loved by teams{' '}
            <span className="gradient-text">worldwide</span>
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            See what our customers have to say about their experience with TaskPulse.
          </p>
        </motion.div>

        {/* Testimonials Grid */}
        <div className="grid md:grid-cols-3 gap-6 lg:gap-8">
          {testimonials.map((testimonial, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.15 }}
              whileHover={{ y: -6, transition: { duration: 0.2 } }}
              className="group relative"
            >
              <div className="relative p-6 lg:p-8 rounded-2xl glass-card border border-border/30 hover:border-primary/20 transition-all duration-500 overflow-hidden">
                {/* Ambient glow */}
                <div className={`absolute -top-12 -right-12 w-32 h-32 bg-gradient-to-br ${testimonial.color} opacity-0 group-hover:opacity-[0.08] transition-opacity duration-500 blur-3xl rounded-full`} />

                {/* Stars */}
                <div className="flex gap-1 mb-5">
                  {[...Array(5)].map((_, i) => (
                    <Star key={i} className="w-4 h-4 fill-amber-500 text-amber-600 dark:fill-amber-400 dark:text-amber-400" />
                  ))}
                </div>

                {/* Quote */}
                <p className="text-base lg:text-lg mb-8 leading-relaxed text-foreground/90">
                  &ldquo;{testimonial.quote}&rdquo;
                </p>

                {/* Author */}
                <div className="flex items-center gap-4">
                  <div className={`w-11 h-11 rounded-full bg-gradient-to-br ${testimonial.color} flex items-center justify-center text-sm font-semibold text-white shadow-lg`}>
                    {testimonial.avatar}
                  </div>
                  <div>
                    <div className="font-medium text-foreground">{testimonial.author}</div>
                    <div className="text-sm text-muted-foreground">
                      {testimonial.role} at {testimonial.company}
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ─── CTA Section ────────────────────────────────────────────────────────
function CTASection() {
  return (
    <section className="py-24 lg:py-32 relative overflow-hidden">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="relative rounded-3xl overflow-hidden"
        >
          {/* Background */}
          <div className="absolute inset-0 bg-gradient-to-br from-amber-700 via-orange-600 to-yellow-600" />
          <div className="absolute inset-0 mesh-gradient opacity-30" />

          {/* Pattern */}
          <div className="absolute inset-0 opacity-[0.07]">
            <div className="absolute inset-0" style={{
              backgroundImage: `radial-gradient(circle at 2px 2px, white 1px, transparent 0)`,
              backgroundSize: '32px 32px',
            }} />
          </div>

          {/* Floating shapes */}
          <div className="absolute inset-0 overflow-hidden pointer-events-none">
            <FloatingShape className="top-[10%] left-[5%]" size={100} gradient="from-white/10 to-white/5" delay={0} duration={6} blur="blur-xl" />
            <FloatingShape className="bottom-[10%] right-[5%]" size={80} gradient="from-white/10 to-white/5" delay={1} duration={7} blur="blur-xl" />
          </div>

          {/* Content */}
          <div className="relative py-16 lg:py-24 px-8 lg:px-16 text-center">
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-white mb-6">
              Ready to transform your workflow?
            </h2>
            <p className="text-lg lg:text-xl text-white/80 max-w-2xl mx-auto mb-10">
              Join thousands of teams already using TaskPulse to work smarter, not harder.
              Start your free trial today.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link to="/signup">
                <Button size="lg" variant="secondary" className="gap-2 text-base px-8 bg-white text-amber-800 hover:bg-white/90 shadow-xl shadow-black/20">
                  Get Started Free
                  <ArrowRight className="w-5 h-5" />
                </Button>
              </Link>
              <Button size="lg" variant="outline" className="gap-2 text-base px-8 border-white/30 text-white hover:bg-white/10 backdrop-blur-sm">
                <Play className="w-5 h-5" />
                Watch Demo
              </Button>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}

// ─── Footer ─────────────────────────────────────────────────────────────
function Footer() {
  const footerLinks = {
    Product: ['Features', 'Integrations', 'Pricing', 'Changelog', 'Roadmap'],
    Company: ['About', 'Blog', 'Careers', 'Press', 'Partners'],
    Resources: ['Documentation', 'Help Center', 'Community', 'Templates', 'Webinars'],
    Legal: ['Privacy', 'Terms', 'Security', 'Cookies', 'Compliance'],
  };

  return (
    <footer className="py-16 border-t border-border/50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-8 lg:gap-12 mb-12">
          {/* Brand */}
          <div className="col-span-2">
            <Link to="/" className="flex items-center gap-2.5 mb-4">
              <img src="/beeax-logo.jpeg" alt="TaskPulse" className="w-9 h-9 rounded-xl object-cover shadow-lg shadow-amber-600/25" />
              <span className="text-lg font-bold">TaskPulse</span>
            </Link>
            <p className="text-sm text-muted-foreground mb-4 max-w-xs">
              AI-powered task management that helps teams work smarter and ship faster.
            </p>
            <div className="flex gap-3">
              {['Twitter', 'LinkedIn', 'GitHub', 'Discord'].map((social) => (
                <a
                  key={social}
                  href="#"
                  className="w-9 h-9 rounded-lg glass-card border border-border/50 flex items-center justify-center text-muted-foreground hover:text-foreground hover:border-primary/30 transition-all duration-300"
                >
                  <span className="text-xs font-medium">{social[0]}</span>
                </a>
              ))}
            </div>
          </div>

          {/* Links */}
          {Object.entries(footerLinks).map(([category, links]) => (
            <div key={category}>
              <h4 className="font-medium mb-4 text-foreground/90">{category}</h4>
              <ul className="space-y-2.5">
                {links.map((link) => (
                  <li key={link}>
                    <a
                      href="#"
                      className="text-sm text-muted-foreground hover:text-foreground transition-colors duration-200"
                    >
                      {link}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Bottom */}
        <div className="pt-8 border-t border-border/50 flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="text-sm text-muted-foreground">
            &copy; 2025 TaskPulse. All rights reserved.
          </p>
          <div className="flex items-center gap-6">
            <a href="#" className="text-sm text-muted-foreground hover:text-foreground transition-colors duration-200">
              Privacy Policy
            </a>
            <a href="#" className="text-sm text-muted-foreground hover:text-foreground transition-colors duration-200">
              Terms of Service
            </a>
            <a href="#" className="text-sm text-muted-foreground hover:text-foreground transition-colors duration-200">
              Cookie Settings
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}

// ─── Main Landing Page ──────────────────────────────────────────────────
export default function LandingPage() {
  const { mode, accent } = useThemeStore();

  // Apply theme on mount and when it changes
  useEffect(() => {
    applyTheme(mode, accent);
  }, [mode, accent]);

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Navigation />
      <main>
        <HeroSection />
        <FeaturesSection />
        <HowItWorksSection />
        <PricingSection />
        <TestimonialsSection />
        <CTASection />
      </main>
      <Footer />
    </div>
  );
}

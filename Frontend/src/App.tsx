import { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AnimatePresence } from 'framer-motion';
import { initTheme } from './store/themeStore';
import { useAuthStore } from './store/authStore';

// Pages
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import SignupPage from './pages/SignupPage';
import Dashboard from './pages/Dashboard';
import TasksPage from './pages/TasksPage';
import AICommandCenter from './pages/AICommandCenter';
import AutomationPage from './pages/AutomationPage';
import AnalyticsPage from './pages/AnalyticsPage';
import TeamPage from './pages/TeamPage';
import SettingsPage from './pages/SettingsPage';
import CheckInsPage from './pages/CheckInsPage';
import OrganizationSettingsPage from './pages/OrganizationSettingsPage';
import AdminPage from './pages/AdminPage';
import KnowledgeBasePage from './pages/KnowledgeBasePage';
import SkillsPage from './pages/SkillsPage';
import PredictionsPage from './pages/PredictionsPage';
import WorkforcePage from './pages/WorkforcePage';
import IntegrationsPage from './pages/IntegrationsPage';

// Components
import { Toaster } from '@/components/ui/sonner';
import { TooltipProvider } from '@/components/ui/tooltip';

// Protected Route Component
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore();
  return isAuthenticated ? children : <Navigate to="/login" replace />;
}

function App() {
  useEffect(() => {
    initTheme();
  }, []);

  return (
    <TooltipProvider delayDuration={100}>
      <BrowserRouter>
        <AnimatePresence mode="wait">
          <Routes>
            {/* Public Routes */}
            <Route path="/" element={<LandingPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/signup" element={<SignupPage />} />

            {/* Protected Routes */}
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/tasks"
              element={
                <ProtectedRoute>
                  <TasksPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/ai"
              element={
                <ProtectedRoute>
                  <AICommandCenter />
                </ProtectedRoute>
              }
            />
            <Route
              path="/automation"
              element={
                <ProtectedRoute>
                  <AutomationPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/analytics"
              element={
                <ProtectedRoute>
                  <AnalyticsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/team"
              element={
                <ProtectedRoute>
                  <TeamPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/settings"
              element={
                <ProtectedRoute>
                  <SettingsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/checkins"
              element={
                <ProtectedRoute>
                  <CheckInsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/organization"
              element={
                <ProtectedRoute>
                  <OrganizationSettingsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin"
              element={
                <ProtectedRoute>
                  <AdminPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/knowledge-base"
              element={
                <ProtectedRoute>
                  <KnowledgeBasePage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/skills"
              element={
                <ProtectedRoute>
                  <SkillsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/predictions"
              element={
                <ProtectedRoute>
                  <PredictionsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/workforce"
              element={
                <ProtectedRoute>
                  <WorkforcePage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/integrations"
              element={
                <ProtectedRoute>
                  <IntegrationsPage />
                </ProtectedRoute>
              }
            />

            {/* Fallback */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </AnimatePresence>
      </BrowserRouter>
      <Toaster position="bottom-right" richColors />
    </TooltipProvider>
  );
}

export default App;

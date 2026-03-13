import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader2 } from 'lucide-react';

/**
 * OAuth callback page.
 *
 * After Supabase redirects back from Google OAuth, the Supabase client
 * automatically exchanges the code/hash for a session. The
 * onAuthStateChange listener in authStore handles the rest (setting
 * user + tokens in Zustand). We just wait briefly and redirect.
 */
export default function AuthCallback() {
  const navigate = useNavigate();

  useEffect(() => {
    // Give onAuthStateChange a moment to fire, then redirect
    const timer = setTimeout(() => {
      navigate('/dashboard', { replace: true });
    }, 1500);
    return () => clearTimeout(timer);
  }, [navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center space-y-4">
        <Loader2 className="w-8 h-8 animate-spin mx-auto text-primary" />
        <p className="text-muted-foreground">Completing sign in...</p>
      </div>
    </div>
  );
}

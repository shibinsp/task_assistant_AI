import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type ThemeMode = 'light' | 'dark' | 'system';
export type AccentColor = 'purple' | 'blue' | 'cyan' | 'green' | 'orange' | 'pink';

interface ThemeState {
  mode: ThemeMode;
  accent: AccentColor;
  reduceMotion: boolean;
  setMode: (mode: ThemeMode) => void;
  setAccent: (accent: AccentColor) => void;
  setReduceMotion: (reduce: boolean) => void;
  toggleMode: () => void;
}

const accentColors: Record<AccentColor, { primary: string; secondary: string }> = {
  purple: { primary: '262.1 83.3% 57.8%', secondary: '263.4 70% 50.4%' },
  blue: { primary: '217.2 91.2% 59.8%', secondary: '221.2 83.2% 53.3%' },
  cyan: { primary: '189.4 94.5% 43.1%', secondary: '192.9 82.3% 31%' },
  green: { primary: '142.1 76.2% 36.3%', secondary: '142.4 71.8% 29.2%' },
  orange: { primary: '24.6 95% 53.1%', secondary: '20.5 90.2% 48.2%' },
  pink: { primary: '330.4 81.2% 60.4%', secondary: '329.4 86.2% 70.4%' },
};

export const useThemeStore = create<ThemeState>()(
  persist(
    (set, get) => ({
      mode: 'system',
      accent: 'purple',
      reduceMotion: false,
      setMode: (mode) => {
        set({ mode });
        applyTheme(mode, get().accent);
      },
      setAccent: (accent) => {
        set({ accent });
        applyTheme(get().mode, accent);
      },
      setReduceMotion: (reduceMotion) => set({ reduceMotion }),
      toggleMode: () => {
        const newMode = get().mode === 'light' ? 'dark' : 'light';
        set({ mode: newMode });
        applyTheme(newMode, get().accent);
      },
    }),
    {
      name: 'taskpulse-theme',
    }
  )
);

export function applyTheme(mode: ThemeMode, accent: AccentColor) {
  const root = document.documentElement;
  const colors = accentColors[accent];
  
  // Apply accent colors
  root.style.setProperty('--accent-primary', colors.primary);
  root.style.setProperty('--accent-secondary', colors.secondary);
  
  // Handle system preference
  let effectiveMode = mode;
  if (mode === 'system') {
    effectiveMode = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }
  
  // Apply mode
  if (effectiveMode === 'dark') {
    root.classList.add('dark');
  } else {
    root.classList.remove('dark');
  }
}

// Initialize theme on load
export function initTheme() {
  const stored = localStorage.getItem('taskpulse-theme');
  if (stored) {
    const { state } = JSON.parse(stored);
    applyTheme(state.mode, state.accent);
  }
}

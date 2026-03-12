import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type ThemeMode = 'light' | 'dark' | 'system';
export type AccentColor = 'gold' | 'amber' | 'blue' | 'teal' | 'green' | 'orange' | 'olive';

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
  gold: { primary: '44 80% 46%', secondary: '28 80% 52%' },
  amber: { primary: '44 90% 61%', secondary: '43 89% 38%' },
  blue: { primary: '217.2 91.2% 59.8%', secondary: '221.2 83.2% 53.3%' },
  teal: { primary: '180 64% 46%', secondary: '180 64% 36%' },
  green: { primary: '145 63% 42%', secondary: '145 63% 32%' },
  orange: { primary: '28 80% 52%', secondary: '20 90% 48%' },
  olive: { primary: '60 100% 27%', secondary: '60 80% 22%' },
};

export const useThemeStore = create<ThemeState>()(
  persist(
    (set, get) => ({
      mode: 'system',
      accent: 'gold',
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
  const colors = accentColors[accent] ?? accentColors.gold;

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
    const accent = accentColors[state.accent as AccentColor] ? state.accent : 'gold';
    applyTheme(state.mode ?? 'system', accent);
  }
}

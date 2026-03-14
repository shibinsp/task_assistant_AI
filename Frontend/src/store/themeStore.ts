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

const accentColors: Record<AccentColor, { primary: string; primaryDark: string; secondary: string }> = {
  gold:   { primary: '43 82% 46%',  primaryDark: '43 90% 55%',  secondary: '28 80% 52%' },
  amber:  { primary: '38 92% 50%',  primaryDark: '38 92% 60%',  secondary: '43 89% 38%' },
  blue:   { primary: '217 91% 60%', primaryDark: '217 91% 65%', secondary: '221 83% 53%' },
  teal:   { primary: '180 64% 46%', primaryDark: '180 64% 56%', secondary: '180 64% 36%' },
  green:  { primary: '145 63% 42%', primaryDark: '145 63% 52%', secondary: '145 63% 32%' },
  orange: { primary: '28 80% 52%',  primaryDark: '28 80% 62%',  secondary: '20 90% 48%' },
  olive:  { primary: '60 100% 27%', primaryDark: '60 100% 37%', secondary: '60 80% 22%' },
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

  // Apply accent colors — update primary, ring, and sidebar to match
  const isDark = effectiveMode === 'dark';
  const primaryValue = isDark ? colors.primaryDark : colors.primary;
  root.style.setProperty('--primary', primaryValue);
  root.style.setProperty('--ring', primaryValue);
  root.style.setProperty('--sidebar-primary', primaryValue);
  root.style.setProperty('--sidebar-ring', primaryValue);
  root.style.setProperty('--accent-primary', colors.primary);
  root.style.setProperty('--accent-secondary', colors.secondary);
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

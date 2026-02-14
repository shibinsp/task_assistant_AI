import { create } from 'zustand';

interface UIState {
  sidebarOpen: boolean;
  commandPaletteOpen: boolean;
  notificationsOpen: boolean;
  taskCreationSidebarOpen: boolean;
  currentView: 'dashboard' | 'tasks' | 'ai' | 'automation' | 'analytics' | 'team' | 'settings';
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  toggleCommandPalette: () => void;
  setCommandPaletteOpen: (open: boolean) => void;
  toggleNotifications: () => void;
  toggleTaskCreationSidebar: () => void;
  setTaskCreationSidebarOpen: (open: boolean) => void;
  setCurrentView: (view: UIState['currentView']) => void;
}

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: true,
  commandPaletteOpen: false,
  notificationsOpen: false,
  taskCreationSidebarOpen: false,
  currentView: 'dashboard',
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  toggleCommandPalette: () => set((state) => ({ commandPaletteOpen: !state.commandPaletteOpen })),
  setCommandPaletteOpen: (open) => set({ commandPaletteOpen: open }),
  toggleNotifications: () => set((state) => ({ notificationsOpen: !state.notificationsOpen })),
  toggleTaskCreationSidebar: () => set((state) => ({ taskCreationSidebarOpen: !state.taskCreationSidebarOpen })),
  setTaskCreationSidebarOpen: (open) => set({ taskCreationSidebarOpen: open }),
  setCurrentView: (view) => set({ currentView: view }),
}));

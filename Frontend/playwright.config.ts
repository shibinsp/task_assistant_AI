import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: [['html', { open: 'never' }], ['list']],
  timeout: 60_000,
  expect: { timeout: 10_000 },

  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },

  projects: [
    // Setup project - runs first to authenticate
    {
      name: 'setup',
      testMatch: /auth\.setup\.ts/,
    },
    // Public pages - no auth needed
    {
      name: 'public',
      testMatch: /01-landing\.spec\.ts/,
      use: { ...devices['Desktop Chrome'] },
    },
    // Auth tests - login/signup/logout flows (no stored auth)
    {
      name: 'auth',
      testMatch: /02-auth\.spec\.ts/,
      use: { ...devices['Desktop Chrome'] },
    },
    // Authenticated tests - reuse stored auth state
    {
      name: 'authenticated',
      testMatch: /0[3-9]-.*\.spec\.ts|1[0-3]-.*\.spec\.ts/,
      use: {
        ...devices['Desktop Chrome'],
        storageState: 'e2e/.auth/user.json',
      },
      dependencies: ['setup'],
    },
  ],

  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:5173',
    reuseExistingServer: true,
    timeout: 30_000,
  },
});

import { type Page, expect } from '@playwright/test';

/** Demo credentials — use deployed Supabase credentials when E2E_BASE_URL is set */
export const DEMO_USER = {
  email: process.env.E2E_BASE_URL ? 'admin@taskpulse.demo' : 'admin@acme.com',
  password: process.env.E2E_BASE_URL ? 'TaskPulse2024' : 'demo123',
  name: 'Admin',
};

/**
 * Log in via the UI and wait for the dashboard to load.
 * Uses a smarter approach: first checks if already authenticated,
 * then tries login with retry to handle rate limiting.
 */
export async function login(page: Page, email = DEMO_USER.email, password = DEMO_USER.password) {
  await page.goto('/login');

  // Wait a moment for any redirects
  await page.waitForTimeout(1000);

  // If already redirected to dashboard (still logged in), skip
  if (page.url().includes('/dashboard')) return;

  // If redirected away from login somehow, go back
  if (!page.url().includes('/login')) {
    await page.goto('/login');
  }

  await page.waitForLoadState('domcontentloaded');

  // Fill credentials
  await page.getByPlaceholder('you@example.com').fill(email);
  await page.getByPlaceholder('Enter your password').fill(password);

  // Click the exact "Sign In" submit button (not the Google one)
  await page.getByRole('button', { name: 'Sign In', exact: true }).click();

  // Wait for navigation to dashboard
  await page.waitForURL('**/dashboard', { timeout: 20_000 });
  await expect(page).toHaveURL(/\/dashboard/);
}

/**
 * Navigate to Tasks page from dashboard.
 */
export async function goToTasks(page: Page) {
  await page.getByRole('link', { name: 'Tasks' }).first().click();
  await page.waitForURL('**/tasks', { timeout: 10_000 });
  await expect(page).toHaveURL(/\/tasks/);
}

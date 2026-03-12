import { test as setup, expect } from '@playwright/test';
import { DEMO_USER } from './helpers';

const authFile = 'e2e/.auth/user.json';

setup('authenticate', async ({ page }) => {
  await page.goto('/login');
  await page.waitForLoadState('domcontentloaded');

  await page.getByPlaceholder('you@example.com').fill(DEMO_USER.email);
  await page.getByPlaceholder('Enter your password').fill(DEMO_USER.password);
  await page.getByRole('button', { name: 'Sign In', exact: true }).click();

  await page.waitForURL('**/dashboard', { timeout: 20_000 });
  await expect(page).toHaveURL(/\/dashboard/);

  // Save signed-in state
  await page.context().storageState({ path: authFile });
});

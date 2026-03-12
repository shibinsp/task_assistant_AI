import { test, expect } from '@playwright/test';

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('domcontentloaded');
  });

  test('displays greeting with user name', async ({ page }) => {
    await expect(page.getByText(/good (morning|afternoon|evening)/i)).toBeVisible();
  });

  test('shows stats cards', async ({ page }) => {
    await expect(page.getByText('Tasks Completed')).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText('In Progress').first()).toBeVisible();
  });

  test('shows AI Insights banner', async ({ page }) => {
    await expect(page.getByText('AI Insight', { exact: true })).toBeVisible();
  });

  test('shows Task Velocity chart section', async ({ page }) => {
    await expect(page.getByText('Task Velocity')).toBeVisible();
  });

  test('shows Productivity Heatmap chart section', async ({ page }) => {
    await expect(page.getByText('Productivity Heatmap')).toBeVisible();
  });

  test('shows Recent Tasks section', async ({ page }) => {
    await expect(page.getByText('Recent Tasks')).toBeVisible();
  });

  test('shows AI Insights panel', async ({ page }) => {
    await expect(page.getByText('AI Insights')).toBeVisible();
    await expect(page.getByRole('button', { name: /ask ai assistant/i })).toBeVisible();
  });

  test('has action buttons in header area', async ({ page }) => {
    await expect(page.getByText(/this week/i).first()).toBeVisible();
    await expect(page.getByText(/new task/i).first()).toBeVisible();
  });

  test('sidebar navigation to tasks works', async ({ page }) => {
    const tasksLink = page.locator('aside').getByText('Tasks').first();
    await tasksLink.click();
    await page.waitForURL('**/tasks', { timeout: 10_000 });
    await expect(page).toHaveURL(/\/tasks/);
  });

  test('sidebar collapse toggle works', async ({ page }) => {
    const collapseBtn = page.getByText('Collapse').first();
    if (await collapseBtn.isVisible()) {
      await collapseBtn.click();
      await page.waitForTimeout(500);
    }
  });
});

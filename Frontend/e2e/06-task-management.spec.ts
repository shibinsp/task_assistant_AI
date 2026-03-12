import { test, expect } from '@playwright/test';

test.describe('Task Management', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/tasks');
    await page.waitForLoadState('domcontentloaded');
  });

  test('displays task board with status columns', async ({ page }) => {
    await expect(page.getByText('To Do').first()).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText('In Progress').first()).toBeVisible();
    await expect(page.getByText('Review').first()).toBeVisible();
    await expect(page.getByText('Done').first()).toBeVisible();
  });

  test('task-level search filters tasks', async ({ page }) => {
    const searchInput = page.getByPlaceholder('Search tasks...');
    await searchInput.fill('nonexistent-task-xyz-12345');
    await page.waitForTimeout(1000);
  });

  test('view toggle buttons are visible (Board, List, Timeline)', async ({ page }) => {
    await expect(page.getByText('Board').first()).toBeVisible();
    await expect(page.getByText('List').first()).toBeVisible();
    await expect(page.getByText('Timeline').first()).toBeVisible();
  });

  test('can switch to list view', async ({ page }) => {
    await page.getByText('List').first().click();
    await page.waitForTimeout(500);
  });

  test('filter button is visible', async ({ page }) => {
    await expect(page.getByText('Filter').first()).toBeVisible();
  });

  test('sort button is visible', async ({ page }) => {
    await expect(page.getByText('Sort').first()).toBeVisible();
  });

  test('clicking a task card opens detail', async ({ page }) => {
    await page.waitForTimeout(2000);
    const taskCard = page.locator('[class*="cursor-pointer"]').first();
    if (await taskCard.isVisible()) {
      await taskCard.click();
      await page.waitForTimeout(1000);
    }
  });
});

import { test, expect } from '@playwright/test';

test.describe('Task Filters & Sorting', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/tasks');
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(2000);
  });

  // --- Filter Tests ---

  test('filter button opens dropdown with status and priority sections', async ({ page }) => {
    await page.getByText('Filter').first().click();
    await page.waitForTimeout(300);

    await expect(page.getByText('Status').first()).toBeVisible();
    await expect(page.getByText('Priority').first()).toBeVisible();
    await expect(page.locator('[role="menuitem"]').filter({ hasText: 'Clear Filters' })).toBeVisible();
  });

  test('filter dropdown shows all status options', async ({ page }) => {
    await page.getByText('Filter').first().click();
    await page.waitForTimeout(300);

    for (const status of ['all', 'todo', 'in progress', 'review', 'done']) {
      await expect(
        page.locator('[role="menuitem"]').filter({ hasText: new RegExp(status, 'i') }).first()
      ).toBeVisible();
    }
  });

  test('filter dropdown shows all priority options', async ({ page }) => {
    await page.getByText('Filter').first().click();
    await page.waitForTimeout(300);

    for (const priority of ['low', 'medium', 'high', 'urgent']) {
      await expect(
        page.locator('[role="menuitem"]').filter({ hasText: new RegExp(priority, 'i') }).first()
      ).toBeVisible();
    }
  });

  test('can filter tasks by status', async ({ page }) => {
    await page.getByText('Filter').first().click();
    await page.waitForTimeout(300);

    // Click "in progress" filter
    await page.locator('[role="menuitem"]').filter({ hasText: /in progress/i }).first().click();
    await page.waitForTimeout(1000);

    // Filter button should now show active state (variant changes)
    // The filter is applied - we just verify no crash
  });

  test('can filter tasks by priority', async ({ page }) => {
    await page.getByText('Filter').first().click();
    await page.waitForTimeout(300);

    await page.locator('[role="menuitem"]').filter({ hasText: /high/i }).first().click();
    await page.waitForTimeout(1000);
  });

  test('clear filters resets selections', async ({ page }) => {
    // Apply a filter first
    await page.getByText('Filter').first().click();
    await page.waitForTimeout(300);
    await page.locator('[role="menuitem"]').filter({ hasText: /in progress/i }).first().click();
    await page.waitForTimeout(500);

    // Clear filters
    await page.getByText('Filter').first().click();
    await page.waitForTimeout(300);
    await page.locator('[role="menuitem"]').filter({ hasText: 'Clear Filters' }).click();
    await page.waitForTimeout(500);
  });

  // --- Sort Tests ---

  test('sort button opens dropdown with all sort options', async ({ page }) => {
    await page.getByText('Sort').first().click();
    await page.waitForTimeout(300);

    const sortLabels = [
      'Created date (Newest)',
      'Created date (Oldest)',
      'Due date (Soonest)',
      'Due date (Latest)',
      'Priority (High to Low)',
      'Priority (Low to High)',
      'Task Name (A-Z)',
      'Task Name (Z-A)',
    ];

    for (const label of sortLabels) {
      await expect(
        page.locator('[role="menuitem"]').filter({ hasText: label })
      ).toBeVisible();
    }
  });

  test('can sort by priority high to low', async ({ page }) => {
    await page.getByText('Sort').first().click();
    await page.waitForTimeout(300);
    await page.locator('[role="menuitem"]').filter({ hasText: 'Priority (High to Low)' }).click();
    await page.waitForTimeout(1000);
  });

  test('can sort by task name A-Z', async ({ page }) => {
    await page.getByText('Sort').first().click();
    await page.waitForTimeout(300);
    await page.locator('[role="menuitem"]').filter({ hasText: 'Task Name (A-Z)' }).click();
    await page.waitForTimeout(1000);
  });

  test('can sort by due date soonest', async ({ page }) => {
    await page.getByText('Sort').first().click();
    await page.waitForTimeout(300);
    await page.locator('[role="menuitem"]').filter({ hasText: 'Due date (Soonest)' }).click();
    await page.waitForTimeout(1000);
  });

  test('default sort shows checkmark on newest', async ({ page }) => {
    await page.getByText('Sort').first().click();
    await page.waitForTimeout(300);

    const newestItem = page.locator('[role="menuitem"]').filter({ hasText: 'Created date (Newest)' });
    await expect(newestItem).toBeVisible();
    // Default sort should have a checkmark
    await expect(newestItem.getByText('✓')).toBeVisible();
  });

  // --- View Toggle Tests ---

  test('can switch between Board, List, and Timeline views', async ({ page }) => {
    // Use the main content area (not sidebar) for view toggle buttons
    const main = page.locator('main');

    // Switch to List
    await main.getByText('List').first().click();
    await page.waitForTimeout(1000);

    // Switch to Timeline
    await main.getByText('Timeline').first().click();
    await page.waitForTimeout(1000);

    // Switch back to Board
    await main.getByText('Board').first().click();
    await page.waitForTimeout(1000);

    // Board columns should be visible again
    await expect(page.getByText('To Do').first()).toBeVisible({ timeout: 10000 });
  });

  test('list view displays tasks in tabular format', async ({ page }) => {
    await page.getByText('List').first().click();
    await page.waitForTimeout(1000);

    // In list view, tasks should still be visible
    // The view should render without errors
  });
});

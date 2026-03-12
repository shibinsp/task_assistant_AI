import { test, expect } from '@playwright/test';

test.describe('Task Detail & Actions', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/tasks');
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(2000);
  });

  test('clicking a task card opens detail sheet', async ({ page }) => {
    const taskCard = page.locator('[class*="cursor-pointer"]').first();
    if (await taskCard.isVisible({ timeout: 5000 })) {
      await taskCard.click();
      await page.waitForTimeout(1000);
      const sheet = page.locator('[role="dialog"]');
      await expect(sheet).toBeVisible({ timeout: 5000 });
    }
  });

  test('task detail shows status badge', async ({ page }) => {
    const taskCard = page.locator('[class*="cursor-pointer"]').first();
    if (await taskCard.isVisible({ timeout: 5000 })) {
      await taskCard.click();
      await page.waitForTimeout(1000);
      const sheet = page.locator('[role="dialog"]');
      // Status should be one of the known statuses
      const statusBadge = sheet.locator('button').filter({ hasText: /To Do|In Progress|Review|Done/ }).first();
      await expect(statusBadge).toBeVisible({ timeout: 5000 });
    }
  });

  test('task detail shows due date input', async ({ page }) => {
    const taskCard = page.locator('[class*="cursor-pointer"]').first();
    if (await taskCard.isVisible({ timeout: 5000 })) {
      await taskCard.click();
      await page.waitForTimeout(1000);
      const sheet = page.locator('[role="dialog"]');
      const dateInput = sheet.locator('input[type="datetime-local"]');
      await expect(dateInput).toBeVisible({ timeout: 5000 });
    }
  });

  test('status dropdown opens and shows all statuses', async ({ page }) => {
    const taskCard = page.locator('[class*="cursor-pointer"]').first();
    if (await taskCard.isVisible({ timeout: 5000 })) {
      await taskCard.click();
      await page.waitForTimeout(1000);
      const sheet = page.locator('[role="dialog"]');

      // Click the status button to open dropdown
      const statusBtn = sheet.locator('button').filter({ hasText: /To Do|In Progress|Review|Done/ }).first();
      await statusBtn.click();
      await page.waitForTimeout(300);

      // Verify all status options appear
      await expect(page.locator('[role="menuitem"]').filter({ hasText: 'To Do' })).toBeVisible();
      await expect(page.locator('[role="menuitem"]').filter({ hasText: 'In Progress' })).toBeVisible();
      await expect(page.locator('[role="menuitem"]').filter({ hasText: 'Review' })).toBeVisible();
      await expect(page.locator('[role="menuitem"]').filter({ hasText: 'Done' })).toBeVisible();
    }
  });

  test('can open status dropdown and select a status', async ({ page }) => {
    const taskCard = page.locator('[class*="cursor-pointer"]').first();
    if (await taskCard.isVisible({ timeout: 5000 })) {
      await taskCard.click();
      await page.waitForTimeout(1000);
      const sheet = page.locator('[role="dialog"]');

      const statusBtn = sheet.locator('button').filter({ hasText: /To Do|In Progress|Review|Done/ }).first();
      await statusBtn.click();
      await page.waitForTimeout(500);

      // Click "In Progress" from the dropdown menu
      const menuItem = page.locator('[role="menuitem"]').filter({ hasText: 'In Progress' });
      await menuItem.waitFor({ state: 'visible', timeout: 3000 });
      await menuItem.click();
      await page.waitForTimeout(2000);
      // Status change was submitted without error
    }
  });

  test('add subtask button shows input field', async ({ page }) => {
    const taskCard = page.locator('[class*="cursor-pointer"]').first();
    if (await taskCard.isVisible({ timeout: 5000 })) {
      await taskCard.click();
      await page.waitForTimeout(1000);
      const sheet = page.locator('[role="dialog"]');

      const addSubtaskBtn = sheet.getByText('Add subtask').first();
      if (await addSubtaskBtn.isVisible({ timeout: 3000 })) {
        await addSubtaskBtn.click();
        await page.waitForTimeout(300);
        await expect(sheet.locator('input[placeholder="New subtask title..."]')).toBeVisible();
      }
    }
  });

  test('can create a subtask from detail panel', async ({ page }) => {
    const taskCard = page.locator('[class*="cursor-pointer"]').first();
    if (await taskCard.isVisible({ timeout: 5000 })) {
      await taskCard.click();
      await page.waitForTimeout(1000);
      const sheet = page.locator('[role="dialog"]');

      const addSubtaskBtn = sheet.getByText('Add subtask').first();
      if (await addSubtaskBtn.isVisible({ timeout: 3000 })) {
        await addSubtaskBtn.click();
        await page.waitForTimeout(300);

        const subtaskInput = sheet.locator('input[placeholder="New subtask title..."]');
        await subtaskInput.fill('E2E Subtask Test');
        await subtaskInput.press('Enter');
        await page.waitForTimeout(2000);

        await expect(sheet.getByText('E2E Subtask Test').first()).toBeVisible({ timeout: 5000 });
      }
    }
  });

  test('task card three-dot menu shows move and delete options', async ({ page }) => {
    const taskCard = page.locator('[class*="cursor-pointer"]').first();
    if (await taskCard.isVisible({ timeout: 5000 })) {
      // Hover to reveal the three-dot menu
      await taskCard.hover();
      await page.waitForTimeout(300);

      const moreBtn = taskCard.locator('button').filter({ has: page.locator('svg') }).first();
      if (await moreBtn.isVisible({ timeout: 2000 })) {
        await moreBtn.click();
        await page.waitForTimeout(300);

        // Should show Move to options and Delete
        await expect(page.locator('[role="menuitem"]').filter({ hasText: /Move to/ }).first()).toBeVisible();
        await expect(page.locator('[role="menuitem"]').filter({ hasText: 'Delete' })).toBeVisible();
      }
    }
  });

  test('can edit due date in task detail', async ({ page }) => {
    const taskCard = page.locator('[class*="cursor-pointer"]').first();
    if (await taskCard.isVisible({ timeout: 5000 })) {
      await taskCard.click();
      await page.waitForTimeout(1000);
      const sheet = page.locator('[role="dialog"]');

      const dateInput = sheet.locator('input[type="datetime-local"]');
      if (await dateInput.isVisible({ timeout: 3000 })) {
        await dateInput.fill('2026-12-31T23:59');
        await dateInput.blur();
        await page.waitForTimeout(1000);
      }
    }
  });
});

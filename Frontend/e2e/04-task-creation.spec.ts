import { test, expect } from '@playwright/test';

test.describe('Task Creation - Manual', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/tasks');
    await page.waitForLoadState('domcontentloaded');
  });

  test('tasks page loads with controls', async ({ page }) => {
    await expect(page.getByPlaceholder('Search tasks...')).toBeVisible();
    await expect(page.getByRole('button', { name: /AI Describe/i })).toBeVisible();
    await expect(page.locator('button:has-text("Create Task")').first()).toBeVisible();
  });

  test('opens manual task creation modal', async ({ page }) => {
    await page.locator('button:has-text("Create Task")').first().click();
    await page.waitForTimeout(500);

    await expect(page.getByText('Create New Task').first()).toBeVisible();
    await expect(page.getByPlaceholder('Enter task title...')).toBeVisible();
  });

  test('validates that title is required', async ({ page }) => {
    await page.locator('button:has-text("Create Task")').first().click();
    await page.waitForTimeout(500);

    const dialog = page.locator('[role="dialog"]');
    const submitBtn = dialog.getByRole('button', { name: 'Create Task' });
    await expect(submitBtn).toBeDisabled();
  });

  test('creates a task with all fields', async ({ page }) => {
    await page.locator('button:has-text("Create Task")').first().click();
    await page.waitForTimeout(500);

    const dialog = page.locator('[role="dialog"]');

    // Fill title
    await dialog.getByPlaceholder('Enter task title...').fill('E2E Test Task - Playwright');

    // Fill description
    await dialog.getByPlaceholder('Describe the task in detail...').fill(
      'This is an automated test task created by Playwright E2E tests.'
    );

    // Set priority to High
    await dialog.getByText('Medium').first().click();
    await page.waitForTimeout(200);
    await page.getByText('High').first().click();
    await page.waitForTimeout(200);

    // Set estimated hours
    await dialog.getByPlaceholder('e.g., 4').fill('8');

    // Add a tag
    const tagInput = dialog.getByPlaceholder(/tag/i);
    if (await tagInput.isVisible()) {
      await tagInput.fill('e2e-test');
      await tagInput.press('Enter');
      await page.waitForTimeout(200);
    }

    // Add subtask
    const subtaskInput = dialog.getByPlaceholder(/add a subtask/i);
    if (await subtaskInput.isVisible()) {
      await subtaskInput.fill('Subtask from E2E test');
      await subtaskInput.press('Enter');
      await page.waitForTimeout(200);
    }

    // Submit
    const submitBtn = dialog.getByRole('button', { name: 'Create Task' });
    await expect(submitBtn).toBeEnabled();
    await submitBtn.click();

    await page.waitForTimeout(3000);
    await expect(page.getByText('E2E Test Task - Playwright').first()).toBeVisible({ timeout: 10_000 });
  });

  test('creates a minimal task with just a title', async ({ page }) => {
    await page.locator('button:has-text("Create Task")').first().click();
    await page.waitForTimeout(500);

    const dialog = page.locator('[role="dialog"]');
    await dialog.getByPlaceholder('Enter task title...').fill('Minimal Test Task');

    const submitBtn = dialog.getByRole('button', { name: 'Create Task' });
    await expect(submitBtn).toBeEnabled();
    await submitBtn.click();

    await page.waitForTimeout(3000);
    await expect(page.getByText('Minimal Test Task').first()).toBeVisible({ timeout: 10_000 });
  });

  test('can cancel task creation', async ({ page }) => {
    await page.locator('button:has-text("Create Task")').first().click();
    await page.waitForTimeout(500);

    const dialog = page.locator('[role="dialog"]');
    await dialog.getByPlaceholder('Enter task title...').fill('Cancelled Task');
    await dialog.getByRole('button', { name: /cancel/i }).click();

    await page.waitForTimeout(500);
    await expect(page.getByText('Create New Task')).not.toBeVisible();
  });

  test('assignment type toggle works', async ({ page }) => {
    await page.locator('button:has-text("Create Task")').first().click();
    await page.waitForTimeout(500);

    const dialog = page.locator('[role="dialog"]');

    // Default should be "Team Member" selected
    await expect(dialog.getByText('Team Member', { exact: true })).toBeVisible();

    // Click AI Agent option
    await dialog.locator('text=AI Agent').first().click({ force: true });
    await page.waitForTimeout(300);
    await expect(dialog.getByText(/autonomously work/i)).toBeVisible();

    // Click Agent Helper option
    await dialog.locator('text=Agent Helper').first().click({ force: true });
    await page.waitForTimeout(300);
    await expect(dialog.getByText(/assist.*assigned/i)).toBeVisible();
  });
});

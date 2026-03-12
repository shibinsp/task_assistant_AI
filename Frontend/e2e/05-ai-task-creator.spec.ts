import { test, expect } from '@playwright/test';

test.describe('AI Task Creator', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/tasks');
    await page.waitForLoadState('domcontentloaded');
  });

  test('opens AI Task Creator dialog', async ({ page }) => {
    await page.getByRole('button', { name: /AI Describe/i }).click();
    await page.waitForTimeout(500);
    await expect(page.getByText('AI Task Creator').first()).toBeVisible();
  });

  test('shows the initial input form with textarea and file upload', async ({ page }) => {
    await page.getByRole('button', { name: /AI Describe/i }).click();
    await page.waitForTimeout(500);

    await expect(page.getByText('Describe what you need to do')).toBeVisible();
    await expect(page.getByPlaceholder(/I need to fix the login bug/i)).toBeVisible();
    await expect(page.getByText(/click to upload/i).first()).toBeVisible();

    const startBtn = page.getByRole('button', { name: /Start AI Task Creation/i });
    await expect(startBtn).toBeDisabled();
  });

  test('enables start button when description is entered', async ({ page }) => {
    await page.getByRole('button', { name: /AI Describe/i }).click();
    await page.waitForTimeout(500);

    await page.getByPlaceholder(/I need to fix the login bug/i).fill(
      'Build a REST API for user authentication with JWT tokens'
    );

    const startBtn = page.getByRole('button', { name: /Start AI Task Creation/i });
    await expect(startBtn).toBeEnabled();
  });

  test('starts AI chat when description is submitted', async ({ page }) => {
    test.setTimeout(90_000);

    await page.getByRole('button', { name: /AI Describe/i }).click();
    await page.waitForTimeout(500);

    await page.getByPlaceholder(/I need to fix the login bug/i).fill(
      'Create a user dashboard page with charts showing task completion rate and upcoming deadlines.'
    );

    await page.getByRole('button', { name: /Start AI Task Creation/i }).click();

    // Wait for AI response - the chat input should eventually appear
    const chatInput = page.getByPlaceholder(/type your reply/i);
    await expect(chatInput).toBeVisible({ timeout: 60_000 });
  });

  test('can interact with AI chat after initial message', async ({ page }) => {
    test.setTimeout(90_000);

    await page.getByRole('button', { name: /AI Describe/i }).click();
    await page.waitForTimeout(500);

    await page.getByPlaceholder(/I need to fix the login bug/i).fill(
      'Fix the payment processing bug where users get a 500 error'
    );

    await page.getByRole('button', { name: /Start AI Task Creation/i }).click();

    const chatInput = page.getByPlaceholder(/type your reply/i);
    await expect(chatInput).toBeVisible({ timeout: 60_000 });

    // Send a follow-up message
    await chatInput.fill('The deadline is next Friday and priority is high');

    const sendBtn = page.locator('[role="dialog"]').getByRole('button').filter({ has: page.locator('svg') }).last();
    await sendBtn.click();

    await page.waitForTimeout(10_000);
  });

  test('can close AI task creator dialog with Escape', async ({ page }) => {
    await page.getByRole('button', { name: /AI Describe/i }).click();
    await page.waitForTimeout(500);

    await expect(page.getByText('AI Task Creator').first()).toBeVisible();

    await page.keyboard.press('Escape');

    await page.waitForTimeout(500);
    await expect(page.getByText('AI Task Creator')).not.toBeVisible();
  });
});

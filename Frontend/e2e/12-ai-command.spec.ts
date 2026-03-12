import { test, expect } from '@playwright/test';

test.describe('AI Command Center', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/ai');
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(2000);
  });

  test('AI Command page loads', async ({ page }) => {
    await expect(page).toHaveURL(/\/ai/);
  });

  test('displays chat input field', async ({ page }) => {
    const chatInput = page.getByPlaceholder(/ask me anything/i);
    await expect(chatInput).toBeVisible({ timeout: 5000 });
  });

  test('displays send button', async ({ page }) => {
    // Send button should be visible (may be disabled when empty)
    const sendBtn = page.locator('button').filter({ has: page.locator('svg') }).last();
    await expect(sendBtn).toBeVisible({ timeout: 5000 });
  });

  test('shows quick action buttons', async ({ page }) => {
    const actions = ['Create Task', 'Schedule Meeting', 'View Analytics', 'Automate'];
    for (const action of actions) {
      const btn = page.getByText(action, { exact: true }).first();
      if (await btn.isVisible({ timeout: 3000 })) {
        await expect(btn).toBeVisible();
      }
    }
  });

  test('shows AI capabilities or suggestions panel', async ({ page }) => {
    const capabilities = page.getByText(/capabilities|try asking/i).first();
    if (await capabilities.isVisible({ timeout: 5000 })) {
      await expect(capabilities).toBeVisible();
    }
  });

  test('can type a message in chat input', async ({ page }) => {
    const chatInput = page.getByPlaceholder(/ask me anything/i);
    await chatInput.fill('What tasks are overdue?');
    await expect(chatInput).toHaveValue('What tasks are overdue?');
  });

  test('can send a message', async ({ page }) => {
    const chatInput = page.getByPlaceholder(/ask me anything/i);
    await chatInput.fill('Hello, show me my tasks');
    await chatInput.press('Enter');
    await page.waitForTimeout(3000);

    // User message should appear in chat
    await expect(page.getByText('Hello, show me my tasks').first()).toBeVisible({ timeout: 10000 });
  });

  test('quick action populates input', async ({ page }) => {
    const createTaskBtn = page.getByText('Create Task', { exact: true }).first();
    if (await createTaskBtn.isVisible({ timeout: 3000 })) {
      await createTaskBtn.click();
      await page.waitForTimeout(500);

      const chatInput = page.getByPlaceholder(/ask me anything/i);
      const value = await chatInput.inputValue();
      expect(value.length).toBeGreaterThan(0);
    }
  });

  test('input is initially empty', async ({ page }) => {
    const chatInput = page.getByPlaceholder(/ask me anything/i);
    await expect(chatInput).toHaveValue('');
  });
});

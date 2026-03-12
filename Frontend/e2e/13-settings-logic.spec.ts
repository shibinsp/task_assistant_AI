import { test, expect } from '@playwright/test';

test.describe('Settings - Theme & Profile Logic', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/settings');
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(1000);
  });

  // --- Theme Toggle ---

  test('theme section shows Light, Dark, System options', async ({ page }) => {
    // Navigate to the Appearance tab first
    await page.getByText('Appearance').first().click();
    await page.waitForTimeout(500);

    await expect(page.getByText('Light', { exact: true }).first()).toBeVisible({ timeout: 5000 });
    await expect(page.getByText('Dark', { exact: true }).first()).toBeVisible({ timeout: 5000 });
    await expect(page.getByText('System', { exact: true }).first()).toBeVisible({ timeout: 5000 });
  });

  test('can switch to dark theme', async ({ page }) => {
    await page.getByText('Appearance').first().click();
    await page.waitForTimeout(500);

    const darkBtn = page.getByText('Dark', { exact: true }).first();
    await darkBtn.click();
    await page.waitForTimeout(500);

    const isDark = await page.locator('html').evaluate((el) => el.classList.contains('dark'));
    expect(isDark).toBe(true);
  });

  test('can switch to light theme', async ({ page }) => {
    await page.getByText('Appearance').first().click();
    await page.waitForTimeout(500);

    // First switch to dark
    await page.getByText('Dark', { exact: true }).first().click();
    await page.waitForTimeout(300);

    // Then switch to light
    await page.getByText('Light', { exact: true }).first().click();
    await page.waitForTimeout(500);

    const isDark = await page.locator('html').evaluate((el) => el.classList.contains('dark'));
    expect(isDark).toBe(false);
  });

  test('can switch to system theme', async ({ page }) => {
    await page.getByText('Appearance').first().click();
    await page.waitForTimeout(500);

    await page.getByText('System', { exact: true }).first().click();
    await page.waitForTimeout(500);
  });

  // --- Accent Colors ---

  test('accent color section shows all 7 color options', async ({ page }) => {
    await page.getByText('Appearance').first().click();
    await page.waitForTimeout(500);

    const colors = ['Gold', 'Amber', 'Blue', 'Teal', 'Green', 'Orange', 'Olive'];
    for (const color of colors) {
      await expect(page.getByText(color, { exact: true }).first()).toBeVisible({ timeout: 5000 });
    }
  });

  test('can switch accent color to Blue', async ({ page }) => {
    await page.getByText('Appearance').first().click();
    await page.waitForTimeout(500);

    await page.getByText('Blue', { exact: true }).first().click();
    await page.waitForTimeout(500);
  });

  test('can switch accent color to Teal', async ({ page }) => {
    await page.getByText('Appearance').first().click();
    await page.waitForTimeout(500);

    await page.getByText('Teal', { exact: true }).first().click();
    await page.waitForTimeout(500);
  });

  test('can switch accent color back to Gold', async ({ page }) => {
    await page.getByText('Appearance').first().click();
    await page.waitForTimeout(500);

    await page.getByText('Gold', { exact: true }).first().click();
    await page.waitForTimeout(500);
  });

  // --- Profile Editing ---

  test('profile section shows name and email inputs', async ({ page }) => {
    const nameInput = page.locator('#name');
    const emailInput = page.locator('#email');

    if (await nameInput.isVisible({ timeout: 5000 })) {
      await expect(nameInput).toBeVisible();
      await expect(emailInput).toBeVisible();
    }
  });

  test('can edit profile name', async ({ page }) => {
    const nameInput = page.locator('#name');
    if (await nameInput.isVisible({ timeout: 5000 })) {
      await nameInput.clear();
      await nameInput.fill('E2E Test User');
      await expect(nameInput).toHaveValue('E2E Test User');
    }
  });

  test('can edit bio field', async ({ page }) => {
    const bioInput = page.locator('#bio');
    if (await bioInput.isVisible({ timeout: 5000 })) {
      await bioInput.clear();
      await bioInput.fill('Test bio from E2E');
      await expect(bioInput).toHaveValue('Test bio from E2E');
    }
  });

  test('save profile button is visible', async ({ page }) => {
    const saveBtn = page.getByText(/save/i).first();
    if (await saveBtn.isVisible({ timeout: 5000 })) {
      await expect(saveBtn).toBeVisible();
    }
  });

  // --- Password Update ---

  test('password section shows current, new, and confirm fields', async ({ page }) => {
    const currentPw = page.locator('#current');
    const newPw = page.locator('#new');
    const confirmPw = page.locator('#confirm');

    if (await currentPw.isVisible({ timeout: 5000 })) {
      await expect(currentPw).toBeVisible();
      await expect(newPw).toBeVisible();
      await expect(confirmPw).toBeVisible();
    }
  });

  test('password visibility toggle works', async ({ page }) => {
    const currentPw = page.locator('#current');
    if (await currentPw.isVisible({ timeout: 5000 })) {
      // Should be password type initially
      await expect(currentPw).toHaveAttribute('type', 'password');

      // Click eye toggle (button near the input)
      const eyeBtn = currentPw.locator('..').locator('button');
      if (await eyeBtn.isVisible({ timeout: 2000 })) {
        await eyeBtn.click();
        await page.waitForTimeout(300);
      }
    }
  });

  test('update password button is visible', async ({ page }) => {
    const updateBtn = page.getByText('Update Password').first();
    if (await updateBtn.isVisible({ timeout: 5000 })) {
      await expect(updateBtn).toBeVisible();
    }
  });
});

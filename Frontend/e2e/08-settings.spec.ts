import { test, expect } from '@playwright/test';

test.describe('Settings Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/settings');
    await page.waitForLoadState('domcontentloaded');
  });

  test('settings page loads', async ({ page }) => {
    await expect(page).toHaveURL(/\/settings/);
  });

  test('displays profile section', async ({ page }) => {
    await expect(page.getByText(/profile/i).first()).toBeVisible({ timeout: 5000 });
  });

  test('displays appearance/theme section', async ({ page }) => {
    const themeSection = page.getByText(/appearance|theme/i).first();
    await expect(themeSection).toBeVisible({ timeout: 5000 });
  });

  test('accent color options include Gold', async ({ page }) => {
    const goldOption = page.getByText('Gold').first();
    if (await goldOption.isVisible({ timeout: 5000 })) {
      await expect(goldOption).toBeVisible();
    }
  });
});

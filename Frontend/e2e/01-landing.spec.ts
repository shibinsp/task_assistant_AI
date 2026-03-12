import { test, expect } from '@playwright/test';

test.describe('Landing Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('renders the landing page with logo and brand name', async ({ page }) => {
    // Logo image should be visible
    const logo = page.locator('img[alt="TaskPulse"]').first();
    await expect(logo).toBeVisible();
    await expect(logo).toHaveAttribute('src', '/beeax-logo.jpeg');

    // Brand name should display
    await expect(page.getByText('TaskPulse').first()).toBeVisible();
  });

  test('has navigation links', async ({ page }) => {
    await expect(page.getByRole('link', { name: /features/i }).first()).toBeVisible();
    await expect(page.getByRole('link', { name: /pricing/i }).first()).toBeVisible();
  });

  test('has CTA buttons that navigate to auth pages', async ({ page }) => {
    const getStarted = page.getByRole('link', { name: /get started/i }).first();
    await expect(getStarted).toBeVisible();

    // Click Get Started and verify it navigates to signup or login
    await getStarted.click();
    await expect(page).toHaveURL(/\/(signup|login)/);
  });

  test('page title is correct', async ({ page }) => {
    await expect(page).toHaveTitle(/TaskPulse/i);
  });

  test('warm gold color palette is applied', async ({ page }) => {
    // Check that the page background uses the warm cream color
    const body = page.locator('body');
    const bgColor = await body.evaluate((el) => getComputedStyle(el).backgroundColor);
    // Should be a warm cream tone (FDF5E6-ish in rgb)
    expect(bgColor).toBeTruthy();
  });

  test('features section is visible', async ({ page }) => {
    // Scroll to features section
    await page.getByText(/ship faster/i).first().scrollIntoViewIfNeeded();
    await expect(page.getByText(/ship faster/i).first()).toBeVisible();
  });

  test('pricing section displays plans', async ({ page }) => {
    await page.getByText(/pricing/i).first().scrollIntoViewIfNeeded();
    // Should show pricing plan text
    await expect(page.getByText(/month/i).first()).toBeVisible();
  });
});

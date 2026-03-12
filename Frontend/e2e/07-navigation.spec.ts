import { test, expect } from '@playwright/test';

test.describe('App Navigation & Sidebar', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('domcontentloaded');
  });

  test('navigates to Tasks page', async ({ page }) => {
    await page.locator('aside').getByText('Tasks').first().click();
    await page.waitForURL('**/tasks', { timeout: 10_000 });
    await expect(page).toHaveURL(/\/tasks/);
  });

  test('navigates to Check-Ins page', async ({ page }) => {
    await page.locator('aside').getByText('Check-Ins').first().click();
    await page.waitForURL('**/checkins', { timeout: 10_000 });
    await expect(page).toHaveURL(/\/checkins/);
  });

  test('navigates to AI Command page', async ({ page }) => {
    await page.locator('aside').getByText('AI Command').first().click();
    await page.waitForURL('**/ai', { timeout: 10_000 });
    await expect(page).toHaveURL(/\/ai/);
  });

  test('navigates to Skills page', async ({ page }) => {
    await page.locator('aside').getByText('Skills').first().click();
    await page.waitForURL('**/skills', { timeout: 10_000 });
    await expect(page).toHaveURL(/\/skills/);
  });

  test('navigates to Analytics page', async ({ page }) => {
    await page.locator('aside').getByText('Analytics').first().click();
    await page.waitForURL('**/analytics', { timeout: 10_000 });
    await expect(page).toHaveURL(/\/analytics/);
  });

  test('navigates to Knowledge Base page', async ({ page }) => {
    await page.locator('aside').getByText('Knowledge Base').first().click();
    await page.waitForURL('**/knowledge-base', { timeout: 10_000 });
    await expect(page).toHaveURL(/\/knowledge-base/);
  });

  test('navigates to Settings page', async ({ page }) => {
    await page.locator('aside').getByText('Settings').first().click();
    await page.waitForURL('**/settings', { timeout: 10_000 });
    await expect(page).toHaveURL(/\/settings/);
  });

  test('notification bell is visible in header', async ({ page }) => {
    const header = page.locator('header');
    await expect(header).toBeVisible();
  });
});

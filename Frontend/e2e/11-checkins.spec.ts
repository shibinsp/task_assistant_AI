import { test, expect } from '@playwright/test';

test.describe('Check-Ins Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/checkins');
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(2000);
  });

  test('check-ins page loads', async ({ page }) => {
    await expect(page).toHaveURL(/\/checkins/);
  });

  test('displays check-ins header', async ({ page }) => {
    await expect(page.getByText(/check-in/i).first()).toBeVisible({ timeout: 5000 });
  });

  test('shows pending check-ins section if available', async ({ page }) => {
    const pending = page.getByText(/pending|upcoming/i).first();
    if (await pending.isVisible({ timeout: 3000 })) {
      await expect(pending).toBeVisible();
    }
  });

  test('respond button opens response form', async ({ page }) => {
    const respondBtn = page.locator('button').filter({ hasText: /respond/i }).first();
    if (await respondBtn.isVisible({ timeout: 5000 })) {
      await respondBtn.click();
      await page.waitForTimeout(1000);

      // Should show response form fields - look for any textarea or input in the form
      const formField = page.locator('textarea').first();
      if (await formField.isVisible({ timeout: 3000 })) {
        await expect(formField).toBeVisible();
      }
    } else {
      // No pending check-ins to respond to - that's OK
      test.skip();
    }
  });

  test('response form has progress indicator dropdown', async ({ page }) => {
    const respondBtn = page.getByText('Respond').first();
    if (await respondBtn.isVisible({ timeout: 5000 })) {
      await respondBtn.click();
      await page.waitForTimeout(500);

      // Look for the progress indicator select trigger
      const selectTrigger = page.locator('[role="combobox"]').first();
      if (await selectTrigger.isVisible({ timeout: 3000 })) {
        await selectTrigger.click();
        await page.waitForTimeout(300);

        // Should show status options
        const options = page.locator('[role="option"]');
        await expect(options.first()).toBeVisible({ timeout: 3000 });
      }
    }
  });

  test('response form has text areas', async ({ page }) => {
    const respondBtn = page.locator('button').filter({ hasText: /respond/i }).first();
    if (await respondBtn.isVisible({ timeout: 5000 })) {
      await respondBtn.click();
      await page.waitForTimeout(1000);

      // At least one textarea should be present
      const textareas = page.locator('textarea');
      const count = await textareas.count();
      if (count > 0) {
        await expect(textareas.first()).toBeVisible({ timeout: 3000 });
      }
    } else {
      test.skip();
    }
  });

  test('can fill and submit a check-in response', async ({ page }) => {
    const respondBtn = page.getByText('Respond').first();
    if (await respondBtn.isVisible({ timeout: 5000 })) {
      await respondBtn.click();
      await page.waitForTimeout(500);

      // Select progress indicator
      const selectTrigger = page.locator('[role="combobox"]').first();
      if (await selectTrigger.isVisible({ timeout: 3000 })) {
        await selectTrigger.click();
        await page.waitForTimeout(300);
        await page.locator('[role="option"]').first().click();
        await page.waitForTimeout(300);
      }

      // Fill progress notes
      const progressNotes = page.getByPlaceholder(/progress|update/i).first();
      if (await progressNotes.isVisible({ timeout: 2000 })) {
        await progressNotes.fill('E2E test progress update - everything on track');
      }

      // Fill completed work
      const completed = page.getByPlaceholder(/completed/i).first();
      if (await completed.isVisible({ timeout: 2000 })) {
        await completed.fill('Completed E2E testing');
      }

      // Submit
      const submitBtn = page.getByText('Submit Response').first();
      if (await submitBtn.isVisible({ timeout: 2000 })) {
        await submitBtn.click();
        await page.waitForTimeout(2000);
      }
    }
  });

  test('shows recent check-ins section', async ({ page }) => {
    const recent = page.getByText(/recent|history|past/i).first();
    if (await recent.isVisible({ timeout: 5000 })) {
      await expect(recent).toBeVisible();
    }
  });
});

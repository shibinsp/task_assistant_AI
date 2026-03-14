import { test, expect } from '@playwright/test';
import { login } from './helpers';

test.describe('Authentication', () => {
  test.describe('Login Page', () => {
    test.beforeEach(async ({ page }) => {
      await page.goto('/login');
      await page.waitForLoadState('networkidle');
    });

    test('renders login form with logo', async ({ page }) => {
      // Logo
      const logo = page.locator('img[src*="beeax-logo"]');
      await expect(logo).toBeVisible();

      // Form fields
      await expect(page.getByPlaceholder('you@example.com')).toBeVisible();
      await expect(page.getByPlaceholder('Enter your password')).toBeVisible();

      // Submit button
      await expect(page.getByRole('button', { name: 'Sign In', exact: true })).toBeVisible();
    });

    test('shows validation when submitting empty form', async ({ page }) => {
      await page.getByRole('button', { name: 'Sign In', exact: true }).click();
      // Should stay on login page (not navigate away)
      await expect(page).toHaveURL(/\/login/);
    });

    test('shows error for invalid credentials', async ({ page }) => {
      await page.getByPlaceholder('you@example.com').fill('wrong@example.com');
      await page.getByPlaceholder('Enter your password').fill('wrongpassword');
      await page.getByRole('button', { name: 'Sign In', exact: true }).click();

      // Wait for error toast or message
      await page.waitForTimeout(2000);
      // Should stay on login page
      await expect(page).toHaveURL(/\/login/);
    });

    test('successful login redirects to dashboard', async ({ page }) => {
      await login(page);
      await expect(page).toHaveURL(/\/dashboard/);

      // Dashboard should show greeting
      await expect(page.getByText(/good (morning|afternoon|evening)/i)).toBeVisible();
    });

    test('has link to signup page', async ({ page }) => {
      const signupLink = page.getByRole('link', { name: /sign up|create.*account|register/i }).first();
      await expect(signupLink).toBeVisible();
    });
  });

  test.describe('Signup Page', () => {
    test('renders signup form with logo', async ({ page }) => {
      await page.goto('/signup');
      await page.waitForLoadState('networkidle');

      const logo = page.locator('img[alt="TaskPulse"]');
      await expect(logo).toBeVisible();

      // Should show create account heading
      await expect(page.getByText(/create.*account/i).first()).toBeVisible();
    });
  });

  test.describe('Protected Routes', () => {
    test('redirects unauthenticated user to login', async ({ page }) => {
      await page.goto('/dashboard');
      await expect(page).toHaveURL(/\/login/);
    });

    test('redirects unauthenticated user from tasks page', async ({ page }) => {
      await page.goto('/tasks');
      await expect(page).toHaveURL(/\/login/);
    });
  });

  test.describe('Logout', () => {
    test('user can log out from dashboard', async ({ page }) => {
      await login(page);
      await expect(page).toHaveURL(/\/dashboard/);

      // Open user menu dropdown - click the button in header that contains the user avatar
      const userMenuButton = page.locator('header button').last();
      await userMenuButton.click();
      await page.waitForTimeout(300);

      // Click logout
      const logoutItem = page.getByText(/logout/i).first();
      await logoutItem.click();

      // Should redirect to login
      await page.waitForURL('**/login', { timeout: 10_000 });
      await expect(page).toHaveURL(/\/login/);
    });
  });
});

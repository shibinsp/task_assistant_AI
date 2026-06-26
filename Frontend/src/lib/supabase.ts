import { createClient, type SupabaseClient } from '@supabase/supabase-js';

type BrowserSupabaseClient = SupabaseClient;

const rawSupabaseUrl = import.meta.env.VITE_SUPABASE_URL?.trim();
const rawSupabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY?.trim();

export class SupabaseConfigurationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'SupabaseConfigurationError';
  }
}

function getValidatedSupabaseConfig() {
  if (!rawSupabaseUrl || !rawSupabaseAnonKey) {
    throw new SupabaseConfigurationError(
      'Missing Supabase environment variables. Set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY for this deployment.'
    );
  }

  let parsedUrl: URL;
  try {
    parsedUrl = new URL(rawSupabaseUrl);
  } catch {
    throw new SupabaseConfigurationError(
      `VITE_SUPABASE_URL is not a valid URL: ${rawSupabaseUrl}`
    );
  }

  if (!['http:', 'https:'].includes(parsedUrl.protocol)) {
    throw new SupabaseConfigurationError(
      `VITE_SUPABASE_URL must use http or https: ${rawSupabaseUrl}`
    );
  }

  if (rawSupabaseUrl.includes('your-project.supabase.co')) {
    throw new SupabaseConfigurationError(
      'VITE_SUPABASE_URL is still set to the example placeholder value.'
    );
  }

  return {
    anonKey: rawSupabaseAnonKey,
    url: parsedUrl.toString().replace(/\/$/, ''),
  };
}

let supabaseConfigError: SupabaseConfigurationError | null = null;
let supabaseConfig: ReturnType<typeof getValidatedSupabaseConfig> | null = null;

try {
  supabaseConfig = getValidatedSupabaseConfig();
} catch (error) {
  supabaseConfigError = error instanceof SupabaseConfigurationError
    ? error
    : new SupabaseConfigurationError('Supabase configuration is invalid for this deployment.');
}

let supabaseClient: BrowserSupabaseClient | null = null;
let supabaseClientPromise: Promise<BrowserSupabaseClient> | null = null;
let reachabilityProbe: Promise<void> | null = null;

async function ensureSupabaseReachable() {
  if (supabaseConfigError) {
    throw supabaseConfigError;
  }

  if (!supabaseConfig) {
    throw new SupabaseConfigurationError('Supabase configuration is missing for this deployment.');
  }

  if (!reachabilityProbe) {
    const probeUrl = `${supabaseConfig.url}/auth/v1/settings`;
    reachabilityProbe = fetch(probeUrl, {
      headers: {
        apikey: supabaseConfig.anonKey,
      },
    })
      .then((response) => {
        if (!response.ok) {
          throw new SupabaseConfigurationError(
            `Supabase auth endpoint responded with ${response.status} at ${probeUrl}`
          );
        }
      })
      .catch((error: unknown) => {
        reachabilityProbe = null;
        if (error instanceof SupabaseConfigurationError) {
          throw error;
        }
        throw new SupabaseConfigurationError(
          `Supabase auth endpoint is unreachable at ${probeUrl}. Check VITE_SUPABASE_URL for this deployment.`
        );
      });
  }

  return reachabilityProbe;
}

export function getSupabaseConfigError() {
  return supabaseConfigError;
}

export async function getSupabase() {
  if (supabaseClient) {
    return supabaseClient;
  }

  if (supabaseConfigError) {
    throw supabaseConfigError;
  }

  if (!supabaseConfig) {
    throw new SupabaseConfigurationError('Supabase configuration is missing for this deployment.');
  }

  if (!supabaseClientPromise) {
    supabaseClientPromise = (async () => {
      await ensureSupabaseReachable();
      supabaseClient = createClient(supabaseConfig!.url, supabaseConfig!.anonKey);
      return supabaseClient;
    })().catch((error) => {
      supabaseClientPromise = null;
      throw error;
    });
  }

  return supabaseClientPromise;
}

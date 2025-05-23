// Environment configuration for the application
// This centralizes all environment-specific values

interface EnvironmentConfig {
  apiBaseUrl: string;
  wsBaseUrl: string;
  defaultRefreshInterval: number;
  taskExpirationDays: number;
}

// Development environment configuration
const devConfig: EnvironmentConfig = {
  apiBaseUrl: 'http://localhost:8098',
  wsBaseUrl: 'ws://localhost:8098',
  defaultRefreshInterval: 2000, // 2 seconds
  taskExpirationDays: 7,
};

// Production environment configuration
const prodConfig: EnvironmentConfig = {
  apiBaseUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8098',
  wsBaseUrl: process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8098',
  defaultRefreshInterval: 5000, // 5 seconds
  taskExpirationDays: 7,
};

// Determine which environment to use
const isProduction = process.env.NODE_ENV === 'production';
const config = isProduction ? prodConfig : devConfig;

export default config;

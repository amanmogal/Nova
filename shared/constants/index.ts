// Shared constants for Notion Agent SaaS Platform

// ============================================================================
// API ENDPOINTS
// ============================================================================

export const API_ENDPOINTS = {
  // Auth endpoints
  AUTH: {
    LOGIN: '/api/auth/login',
    LOGOUT: '/api/auth/logout',
    REFRESH: '/api/auth/refresh',
    CALLBACK: '/api/auth/callback',
  },
  
  // User endpoints
  USERS: {
    PROFILE: '/api/users/profile',
    CONFIG: '/api/users/config',
    PREFERENCES: '/api/users/preferences',
  },
  
  // Notion integration
  NOTION: {
    CONNECT: '/api/notion/connect',
    DISCONNECT: '/api/notion/disconnect',
    WORKSPACES: '/api/notion/workspaces',
    DATABASES: '/api/notion/databases',
    SYNC: '/api/notion/sync',
  },
  
  // Agent endpoints
  AGENT: {
    CHAT: '/api/agent/chat',
    STATE: '/api/agent/state',
    ACTIONS: '/api/agent/actions',
    HISTORY: '/api/agent/history',
  },
  
  // Tasks endpoints
  TASKS: {
    LIST: '/api/tasks',
    CREATE: '/api/tasks',
    UPDATE: '/api/tasks/:id',
    DELETE: '/api/tasks/:id',
    COMPLETE: '/api/tasks/:id/complete',
  },
  
  // Routines endpoints
  ROUTINES: {
    LIST: '/api/routines',
    CREATE: '/api/routines',
    UPDATE: '/api/routines/:id',
    DELETE: '/api/routines/:id',
    EXECUTE: '/api/routines/:id/execute',
  },
  
  // Analytics endpoints
  ANALYTICS: {
    USAGE: '/api/analytics/usage',
    DASHBOARD: '/api/analytics/dashboard',
    REPORTS: '/api/analytics/reports',
  },
} as const;

// ============================================================================
// SUBSCRIPTION TIERS
// ============================================================================

export const SUBSCRIPTION_TIERS = {
  FREE: {
    name: 'free',
    max_tasks: 50,
    max_routines: 10,
    daily_operations: 100,
    features: ['basic_agent', 'notion_integration', 'email_notifications'],
    price: 0,
  },
  PRO: {
    name: 'pro',
    max_tasks: 500,
    max_routines: 50,
    daily_operations: 1000,
    features: ['advanced_agent', 'priority_support', 'analytics', 'custom_preferences'],
    price: 9.99,
  },
  ENTERPRISE: {
    name: 'enterprise',
    max_tasks: -1, // unlimited
    max_routines: -1, // unlimited
    daily_operations: -1, // unlimited
    features: ['all_features', 'dedicated_support', 'custom_integrations', 'team_management'],
    price: 29.99,
  },
} as const;

// ============================================================================
// RATE LIMITS
// ============================================================================

export const RATE_LIMITS = {
  FREE: {
    requests_per_minute: 10,
    requests_per_hour: 100,
    requests_per_day: 1000,
  },
  PRO: {
    requests_per_minute: 60,
    requests_per_hour: 1000,
    requests_per_day: 10000,
  },
  ENTERPRISE: {
    requests_per_minute: 300,
    requests_per_hour: 10000,
    requests_per_day: 100000,
  },
} as const;

// ============================================================================
// NOTION API LIMITS
// ============================================================================

export const NOTION_LIMITS = {
  REQUESTS_PER_SECOND: 3,
  REQUESTS_PER_MINUTE: 180,
  MAX_PAGE_SIZE: 100,
  RATE_LIMIT_RETRY_DELAY: 1000, // ms
} as const;

// ============================================================================
// AGENT CONSTANTS
// ============================================================================

export const AGENT_CONSTANTS = {
  MAX_CONVERSATION_HISTORY: 50,
  MAX_TOKENS_PER_REQUEST: 4000,
  MAX_RESPONSE_TIME: 30000, // 30 seconds
  DEFAULT_CONVERSATION_STYLE: 'professional',
  DEFAULT_RESPONSE_LENGTH: 'detailed',
} as const;

// ============================================================================
// DATABASE CONSTANTS
// ============================================================================

export const DATABASE_CONSTANTS = {
  MAX_PAGE_SIZE: 100,
  DEFAULT_PAGE_SIZE: 20,
  MAX_SEARCH_RESULTS: 1000,
  CACHE_TTL: 300, // 5 minutes
} as const;

// ============================================================================
// TIME CONSTANTS
// ============================================================================

export const TIME_CONSTANTS = {
  ONE_MINUTE: 60 * 1000,
  ONE_HOUR: 60 * 60 * 1000,
  ONE_DAY: 24 * 60 * 60 * 1000,
  ONE_WEEK: 7 * 24 * 60 * 60 * 1000,
  ONE_MONTH: 30 * 24 * 60 * 60 * 1000,
} as const;

// ============================================================================
// ERROR MESSAGES
// ============================================================================

export const ERROR_MESSAGES = {
  AUTHENTICATION: {
    INVALID_TOKEN: 'Invalid or expired authentication token',
    MISSING_TOKEN: 'Authentication token is required',
    INSUFFICIENT_PERMISSIONS: 'Insufficient permissions for this operation',
  },
  NOTION: {
    CONNECTION_FAILED: 'Failed to connect to Notion workspace',
    INVALID_CREDENTIALS: 'Invalid Notion credentials',
    RATE_LIMIT_EXCEEDED: 'Notion API rate limit exceeded',
    DATABASE_NOT_FOUND: 'Specified Notion database not found',
  },
  AGENT: {
    OPERATION_FAILED: 'Agent operation failed',
    TIMEOUT: 'Agent operation timed out',
    INVALID_REQUEST: 'Invalid agent request',
  },
  USER: {
    NOT_FOUND: 'User not found',
    ALREADY_EXISTS: 'User already exists',
    QUOTA_EXCEEDED: 'User quota exceeded',
  },
  VALIDATION: {
    INVALID_EMAIL: 'Invalid email address',
    INVALID_PASSWORD: 'Password must be at least 8 characters',
    REQUIRED_FIELD: 'This field is required',
  },
} as const;

// ============================================================================
// SUCCESS MESSAGES
// ============================================================================

export const SUCCESS_MESSAGES = {
  AUTHENTICATION: {
    LOGIN_SUCCESS: 'Successfully logged in',
    LOGOUT_SUCCESS: 'Successfully logged out',
    TOKEN_REFRESHED: 'Authentication token refreshed',
  },
  NOTION: {
    CONNECTED: 'Successfully connected to Notion workspace',
    DISCONNECTED: 'Successfully disconnected from Notion workspace',
    SYNC_COMPLETED: 'Notion data synchronization completed',
  },
  AGENT: {
    OPERATION_COMPLETED: 'Agent operation completed successfully',
    TASK_CREATED: 'Task created successfully',
    ROUTINE_CREATED: 'Routine created successfully',
  },
  USER: {
    PROFILE_UPDATED: 'Profile updated successfully',
    PREFERENCES_SAVED: 'Preferences saved successfully',
  },
} as const;

// ============================================================================
// UI CONSTANTS
// ============================================================================

export const UI_CONSTANTS = {
  SIDEBAR_WIDTH: 280,
  HEADER_HEIGHT: 64,
  FOOTER_HEIGHT: 60,
  MODAL_BACKDROP_BLUR: 'blur(4px)',
  TRANSITION_DURATION: 200,
  ANIMATION_DURATION: 300,
} as const;

// ============================================================================
// FEATURE FLAGS
// ============================================================================

export const FEATURE_FLAGS = {
  ENABLE_ANALYTICS: true,
  ENABLE_NOTIFICATIONS: true,
  ENABLE_BILLING: false, // Will be enabled in production
  ENABLE_TEAM_FEATURES: false,
  ENABLE_ADVANCED_AGENT: true,
  ENABLE_CUSTOM_INTEGRATIONS: false,
} as const;

// ============================================================================
// ENVIRONMENT CONSTANTS
// ============================================================================

export const ENVIRONMENT = {
  DEVELOPMENT: 'development',
  STAGING: 'staging',
  PRODUCTION: 'production',
  TEST: 'test',
} as const;

// ============================================================================
// DEPLOYMENT CONSTANTS
// ============================================================================

export const DEPLOYMENT = {
  FRONTEND_URL: process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000',
  API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  WEBSOCKET_URL: process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000',
} as const; 
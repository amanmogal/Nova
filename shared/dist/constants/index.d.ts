export declare const API_ENDPOINTS: {
    readonly AUTH: {
        readonly LOGIN: "/api/auth/login";
        readonly LOGOUT: "/api/auth/logout";
        readonly REFRESH: "/api/auth/refresh";
        readonly CALLBACK: "/api/auth/callback";
    };
    readonly USERS: {
        readonly PROFILE: "/api/users/profile";
        readonly CONFIG: "/api/users/config";
        readonly PREFERENCES: "/api/users/preferences";
    };
    readonly NOTION: {
        readonly CONNECT: "/api/notion/connect";
        readonly DISCONNECT: "/api/notion/disconnect";
        readonly WORKSPACES: "/api/notion/workspaces";
        readonly DATABASES: "/api/notion/databases";
        readonly SYNC: "/api/notion/sync";
    };
    readonly AGENT: {
        readonly CHAT: "/api/agent/chat";
        readonly STATE: "/api/agent/state";
        readonly ACTIONS: "/api/agent/actions";
        readonly HISTORY: "/api/agent/history";
    };
    readonly TASKS: {
        readonly LIST: "/api/tasks";
        readonly CREATE: "/api/tasks";
        readonly UPDATE: "/api/tasks/:id";
        readonly DELETE: "/api/tasks/:id";
        readonly COMPLETE: "/api/tasks/:id/complete";
    };
    readonly ROUTINES: {
        readonly LIST: "/api/routines";
        readonly CREATE: "/api/routines";
        readonly UPDATE: "/api/routines/:id";
        readonly DELETE: "/api/routines/:id";
        readonly EXECUTE: "/api/routines/:id/execute";
    };
    readonly ANALYTICS: {
        readonly USAGE: "/api/analytics/usage";
        readonly DASHBOARD: "/api/analytics/dashboard";
        readonly REPORTS: "/api/analytics/reports";
    };
};
export declare const SUBSCRIPTION_TIERS: {
    readonly FREE: {
        readonly name: "free";
        readonly max_tasks: 50;
        readonly max_routines: 10;
        readonly daily_operations: 100;
        readonly features: readonly ["basic_agent", "notion_integration", "email_notifications"];
        readonly price: 0;
    };
    readonly PRO: {
        readonly name: "pro";
        readonly max_tasks: 500;
        readonly max_routines: 50;
        readonly daily_operations: 1000;
        readonly features: readonly ["advanced_agent", "priority_support", "analytics", "custom_preferences"];
        readonly price: 9.99;
    };
    readonly ENTERPRISE: {
        readonly name: "enterprise";
        readonly max_tasks: -1;
        readonly max_routines: -1;
        readonly daily_operations: -1;
        readonly features: readonly ["all_features", "dedicated_support", "custom_integrations", "team_management"];
        readonly price: 29.99;
    };
};
export declare const RATE_LIMITS: {
    readonly FREE: {
        readonly requests_per_minute: 10;
        readonly requests_per_hour: 100;
        readonly requests_per_day: 1000;
    };
    readonly PRO: {
        readonly requests_per_minute: 60;
        readonly requests_per_hour: 1000;
        readonly requests_per_day: 10000;
    };
    readonly ENTERPRISE: {
        readonly requests_per_minute: 300;
        readonly requests_per_hour: 10000;
        readonly requests_per_day: 100000;
    };
};
export declare const NOTION_LIMITS: {
    readonly REQUESTS_PER_SECOND: 3;
    readonly REQUESTS_PER_MINUTE: 180;
    readonly MAX_PAGE_SIZE: 100;
    readonly RATE_LIMIT_RETRY_DELAY: 1000;
};
export declare const AGENT_CONSTANTS: {
    readonly MAX_CONVERSATION_HISTORY: 50;
    readonly MAX_TOKENS_PER_REQUEST: 4000;
    readonly MAX_RESPONSE_TIME: 30000;
    readonly DEFAULT_CONVERSATION_STYLE: "professional";
    readonly DEFAULT_RESPONSE_LENGTH: "detailed";
};
export declare const DATABASE_CONSTANTS: {
    readonly MAX_PAGE_SIZE: 100;
    readonly DEFAULT_PAGE_SIZE: 20;
    readonly MAX_SEARCH_RESULTS: 1000;
    readonly CACHE_TTL: 300;
};
export declare const TIME_CONSTANTS: {
    readonly ONE_MINUTE: number;
    readonly ONE_HOUR: number;
    readonly ONE_DAY: number;
    readonly ONE_WEEK: number;
    readonly ONE_MONTH: number;
};
export declare const ERROR_MESSAGES: {
    readonly AUTHENTICATION: {
        readonly INVALID_TOKEN: "Invalid or expired authentication token";
        readonly MISSING_TOKEN: "Authentication token is required";
        readonly INSUFFICIENT_PERMISSIONS: "Insufficient permissions for this operation";
    };
    readonly NOTION: {
        readonly CONNECTION_FAILED: "Failed to connect to Notion workspace";
        readonly INVALID_CREDENTIALS: "Invalid Notion credentials";
        readonly RATE_LIMIT_EXCEEDED: "Notion API rate limit exceeded";
        readonly DATABASE_NOT_FOUND: "Specified Notion database not found";
    };
    readonly AGENT: {
        readonly OPERATION_FAILED: "Agent operation failed";
        readonly TIMEOUT: "Agent operation timed out";
        readonly INVALID_REQUEST: "Invalid agent request";
    };
    readonly USER: {
        readonly NOT_FOUND: "User not found";
        readonly ALREADY_EXISTS: "User already exists";
        readonly QUOTA_EXCEEDED: "User quota exceeded";
    };
    readonly VALIDATION: {
        readonly INVALID_EMAIL: "Invalid email address";
        readonly INVALID_PASSWORD: "Password must be at least 8 characters";
        readonly REQUIRED_FIELD: "This field is required";
    };
};
export declare const SUCCESS_MESSAGES: {
    readonly AUTHENTICATION: {
        readonly LOGIN_SUCCESS: "Successfully logged in";
        readonly LOGOUT_SUCCESS: "Successfully logged out";
        readonly TOKEN_REFRESHED: "Authentication token refreshed";
    };
    readonly NOTION: {
        readonly CONNECTED: "Successfully connected to Notion workspace";
        readonly DISCONNECTED: "Successfully disconnected from Notion workspace";
        readonly SYNC_COMPLETED: "Notion data synchronization completed";
    };
    readonly AGENT: {
        readonly OPERATION_COMPLETED: "Agent operation completed successfully";
        readonly TASK_CREATED: "Task created successfully";
        readonly ROUTINE_CREATED: "Routine created successfully";
    };
    readonly USER: {
        readonly PROFILE_UPDATED: "Profile updated successfully";
        readonly PREFERENCES_SAVED: "Preferences saved successfully";
    };
};
export declare const UI_CONSTANTS: {
    readonly SIDEBAR_WIDTH: 280;
    readonly HEADER_HEIGHT: 64;
    readonly FOOTER_HEIGHT: 60;
    readonly MODAL_BACKDROP_BLUR: "blur(4px)";
    readonly TRANSITION_DURATION: 200;
    readonly ANIMATION_DURATION: 300;
};
export declare const FEATURE_FLAGS: {
    readonly ENABLE_ANALYTICS: true;
    readonly ENABLE_NOTIFICATIONS: true;
    readonly ENABLE_BILLING: false;
    readonly ENABLE_TEAM_FEATURES: false;
    readonly ENABLE_ADVANCED_AGENT: true;
    readonly ENABLE_CUSTOM_INTEGRATIONS: false;
};
export declare const ENVIRONMENT: {
    readonly DEVELOPMENT: "development";
    readonly STAGING: "staging";
    readonly PRODUCTION: "production";
    readonly TEST: "test";
};
export declare const DEPLOYMENT: {
    readonly FRONTEND_URL: string;
    readonly API_URL: string;
    readonly WEBSOCKET_URL: string;
};
//# sourceMappingURL=index.d.ts.map
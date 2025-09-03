export interface User {
    id: string;
    email: string;
    name?: string;
    avatar?: string;
    created_at: string;
    updated_at: string;
    notion_access_token?: string;
    notion_workspace_id?: string;
    notion_workspace_name?: string;
    subscription_tier: SubscriptionTier;
    is_active: boolean;
    last_login?: string;
}
export type SubscriptionTier = 'free' | 'pro' | 'enterprise';
export interface UserConfig {
    id: string;
    user_id: string;
    notion_tasks_db_id?: string;
    notion_routines_db_id?: string;
    daily_planning_time: string;
    notification_preferences: NotificationPreferences;
    agent_preferences: AgentPreferences;
    created_at: string;
    updated_at: string;
}
export interface NotificationPreferences {
    email_notifications: boolean;
    push_notifications: boolean;
    daily_summary: boolean;
    task_reminders: boolean;
    routine_reminders: boolean;
}
export interface AgentPreferences {
    auto_planning: boolean;
    auto_task_creation: boolean;
    auto_routine_suggestions: boolean;
    conversation_style: 'professional' | 'casual' | 'friendly';
    response_length: 'concise' | 'detailed' | 'comprehensive';
}
export interface NotionWorkspace {
    id: string;
    name: string;
    icon?: string;
    is_connected: boolean;
    databases: NotionDatabase[];
}
export interface NotionDatabase {
    id: string;
    name: string;
    type: 'tasks' | 'routines' | 'other';
    is_connected: boolean;
    last_synced?: string;
}
export interface NotionPage {
    id: string;
    title: string;
    url: string;
    created_time: string;
    last_edited_time: string;
    properties: Record<string, any>;
}
export interface AgentState {
    id: string;
    user_id: string;
    conversation_history: ConversationMessage[];
    current_context: AgentContext;
    preferences: AgentPreferences;
    last_activity: string;
    created_at: string;
    updated_at: string;
}
export interface ConversationMessage {
    id: string;
    role: 'user' | 'assistant' | 'system';
    content: string;
    timestamp: string;
    metadata?: {
        tokens_used?: number;
        cost_usd?: number;
        operation_type?: string;
    };
}
export interface AgentContext {
    current_task?: string;
    current_routine?: string;
    recent_actions: string[];
    user_intent?: string;
    conversation_summary?: string;
}
export interface Task {
    id: string;
    user_id: string;
    notion_page_id?: string;
    title: string;
    description?: string;
    status: TaskStatus;
    priority: TaskPriority;
    due_date?: string;
    completed_at?: string;
    tags: string[];
    created_at: string;
    updated_at: string;
}
export type TaskStatus = 'not_started' | 'in_progress' | 'completed' | 'cancelled';
export type TaskPriority = 'low' | 'medium' | 'high' | 'urgent';
export interface Routine {
    id: string;
    user_id: string;
    notion_page_id?: string;
    title: string;
    description?: string;
    frequency: RoutineFrequency;
    time_of_day?: string;
    days_of_week?: number[];
    is_active: boolean;
    last_executed?: string;
    next_execution?: string;
    created_at: string;
    updated_at: string;
}
export type RoutineFrequency = 'daily' | 'weekly' | 'monthly' | 'custom';
export interface UsageLog {
    id: string;
    user_id: string;
    operation_type: string;
    tokens_used: number;
    cost_usd: number;
    duration_ms: number;
    success: boolean;
    error_message?: string;
    metadata?: Record<string, any>;
    timestamp: string;
}
export interface UserAnalytics {
    user_id: string;
    total_operations: number;
    total_tokens_used: number;
    total_cost_usd: number;
    average_response_time_ms: number;
    success_rate: number;
    most_used_features: string[];
    last_activity: string;
    period: 'day' | 'week' | 'month';
}
export interface ApiResponse<T = any> {
    success: boolean;
    data?: T;
    error?: string;
    message?: string;
    timestamp: string;
}
export interface PaginatedResponse<T> {
    data: T[];
    pagination: {
        page: number;
        limit: number;
        total: number;
        total_pages: number;
        has_next: boolean;
        has_prev: boolean;
    };
}
export interface DashboardStats {
    total_tasks: number;
    completed_tasks: number;
    active_routines: number;
    total_cost_this_month: number;
    average_response_time: number;
    success_rate: number;
}
export interface SidebarItem {
    id: string;
    label: string;
    icon: string;
    href: string;
    badge?: number;
    children?: SidebarItem[];
}
export interface Notification {
    id: string;
    type: 'info' | 'success' | 'warning' | 'error';
    title: string;
    message: string;
    timestamp: string;
    read: boolean;
    action_url?: string;
}
export interface EnvironmentConfig {
    NODE_ENV: 'development' | 'production' | 'test';
    NEXT_PUBLIC_API_URL: string;
    NEXT_PUBLIC_APP_URL: string;
    DATABASE_URL: string;
    NEXTAUTH_SECRET: string;
    NEXTAUTH_URL: string;
    NOTION_CLIENT_ID: string;
    NOTION_CLIENT_SECRET: string;
    GOOGLE_API_KEY: string;
    SUPABASE_URL: string;
    SUPABASE_ANON_KEY: string;
    SUPABASE_SERVICE_ROLE_KEY: string;
}
export interface AppError {
    code: string;
    message: string;
    details?: any;
    timestamp: string;
    user_id?: string;
}
export type ErrorCode = 'AUTHENTICATION_FAILED' | 'NOTION_CONNECTION_FAILED' | 'RATE_LIMIT_EXCEEDED' | 'INVALID_REQUEST' | 'DATABASE_ERROR' | 'AGENT_ERROR' | 'QUOTA_EXCEEDED' | 'FEATURE_NOT_AVAILABLE';
export type DeepPartial<T> = {
    [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
};
export type Optional<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;
export type RequiredFields<T, K extends keyof T> = T & Required<Pick<T, K>>;
//# sourceMappingURL=index.d.ts.map
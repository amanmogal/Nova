/**
 * Format a date to a human-readable string
 */
export declare function formatDate(date: Date | string, options?: Intl.DateTimeFormatOptions): string;
/**
 * Get relative time string (e.g., "2 hours ago")
 */
export declare function getRelativeTime(date: Date | string): string;
/**
 * Check if a date is today
 */
export declare function isToday(date: Date | string): boolean;
/**
 * Check if a date is in the past
 */
export declare function isPast(date: Date | string): boolean;
/**
 * Add days to a date
 */
export declare function addDays(date: Date | string, days: number): Date;
/**
 * Capitalize first letter of a string
 */
export declare function capitalize(str: string): string;
/**
 * Convert string to title case
 */
export declare function toTitleCase(str: string): string;
/**
 * Truncate string to specified length
 */
export declare function truncate(str: string, length: number, suffix?: string): string;
/**
 * Generate a random string
 */
export declare function generateRandomString(length?: number): string;
/**
 * Convert string to slug
 */
export declare function toSlug(str: string): string;
/**
 * Validate email address
 */
export declare function isValidEmail(email: string): boolean;
/**
 * Validate URL
 */
export declare function isValidUrl(url: string): boolean;
/**
 * Validate Notion page ID
 */
export declare function isValidNotionPageId(id: string): boolean;
/**
 * Validate UUID
 */
export declare function isValidUuid(uuid: string): boolean;
/**
 * Remove duplicates from array
 */
export declare function removeDuplicates<T>(array: T[]): T[];
/**
 * Group array by key
 */
export declare function groupBy<T>(array: T[], key: keyof T): Record<string, T[]>;
/**
 * Sort array by key
 */
export declare function sortBy<T>(array: T[], key: keyof T, direction?: 'asc' | 'desc'): T[];
/**
 * Deep clone object
 */
export declare function deepClone<T>(obj: T): T;
/**
 * Format number with commas
 */
export declare function formatNumber(num: number): string;
/**
 * Format currency
 */
export declare function formatCurrency(amount: number, currency?: string): string;
/**
 * Calculate percentage
 */
export declare function calculatePercentage(value: number, total: number): number;
/**
 * Clamp number between min and max
 */
export declare function clamp(value: number, min: number, max: number): number;
/**
 * Generate random color
 */
export declare function generateRandomColor(): string;
/**
 * Get color based on status
 */
export declare function getStatusColor(status: string): string;
/**
 * Create standardized error object
 */
export declare function createError(code: string, message: string, details?: any): {
    code: string;
    message: string;
    details: any;
    timestamp: string;
};
/**
 * Check if error is network error
 */
export declare function isNetworkError(error: any): boolean;
/**
 * Retry function with exponential backoff
 */
export declare function retry<T>(fn: () => Promise<T>, maxRetries?: number, delay?: number): Promise<T>;
/**
 * Safe localStorage get
 */
export declare function safeLocalStorageGet(key: string): any;
/**
 * Safe localStorage set
 */
export declare function safeLocalStorageSet(key: string, value: any): boolean;
/**
 * Safe localStorage remove
 */
export declare function safeLocalStorageRemove(key: string): boolean;
/**
 * Debounce function
 */
export declare function debounce<T extends (...args: any[]) => any>(func: T, wait: number): (...args: Parameters<T>) => void;
/**
 * Throttle function
 */
export declare function throttle<T extends (...args: any[]) => any>(func: T, limit: number): (...args: Parameters<T>) => void;
//# sourceMappingURL=index.d.ts.map
"use strict";
// Shared utility fun
Object.defineProperty(exports, "__esModule", { value: true });
exports.formatDate = formatDate;
exports.getRelativeTime = getRelativeTime;
exports.isToday = isToday;
exports.isPast = isPast;
exports.addDays = addDays;
exports.capitalize = capitalize;
exports.toTitleCase = toTitleCase;
exports.truncate = truncate;
exports.generateRandomString = generateRandomString;
exports.toSlug = toSlug;
exports.isValidEmail = isValidEmail;
exports.isValidUrl = isValidUrl;
exports.isValidNotionPageId = isValidNotionPageId;
exports.isValidUuid = isValidUuid;
exports.removeDuplicates = removeDuplicates;
exports.groupBy = groupBy;
exports.sortBy = sortBy;
exports.deepClone = deepClone;
exports.formatNumber = formatNumber;
exports.formatCurrency = formatCurrency;
exports.calculatePercentage = calculatePercentage;
exports.clamp = clamp;
exports.generateRandomColor = generateRandomColor;
exports.getStatusColor = getStatusColor;
exports.createError = createError;
exports.isNetworkError = isNetworkError;
exports.retry = retry;
exports.safeLocalStorageGet = safeLocalStorageGet;
exports.safeLocalStorageSet = safeLocalStorageSet;
exports.safeLocalStorageRemove = safeLocalStorageRemove;
exports.debounce = debounce;
exports.throttle = throttle;
// ============================================================================
// DATE & TIME UTILITIES
// ============================================================================
/**
 * Format a date to a human-readable string
 */
function formatDate(date, options) {
    const dateObj = typeof date === 'string' ? new Date(date) : date;
    const defaultOptions = {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
    };
    return dateObj.toLocaleDateString('en-US', { ...defaultOptions, ...options });
}
/**
 * Get relative time string (e.g., "2 hours ago")
 */
function getRelativeTime(date) {
    const dateObj = typeof date === 'string' ? new Date(date) : date;
    const now = new Date();
    const diffInSeconds = Math.floor((now.getTime() - dateObj.getTime()) / 1000);
    if (diffInSeconds < 60)
        return 'just now';
    if (diffInSeconds < 3600)
        return `${Math.floor(diffInSeconds / 60)} minutes ago`;
    if (diffInSeconds < 86400)
        return `${Math.floor(diffInSeconds / 3600)} hours ago`;
    if (diffInSeconds < 2592000)
        return `${Math.floor(diffInSeconds / 86400)} days ago`;
    return formatDate(dateObj, { year: 'numeric', month: 'short', day: 'numeric' });
}
/**
 * Check if a date is today
 */
function isToday(date) {
    const dateObj = typeof date === 'string' ? new Date(date) : date;
    const today = new Date();
    return dateObj.toDateString() === today.toDateString();
}
/**
 * Check if a date is in the past
 */
function isPast(date) {
    const dateObj = typeof date === 'string' ? new Date(date) : date;
    return dateObj < new Date();
}
/**
 * Add days to a date
 */
function addDays(date, days) {
    const dateObj = typeof date === 'string' ? new Date(date) : date;
    const result = new Date(dateObj);
    result.setDate(result.getDate() + days);
    return result;
}
// ============================================================================
// STRING UTILITIES
// ============================================================================
/**
 * Capitalize first letter of a string
 */
function capitalize(str) {
    return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
}
/**
 * Convert string to title case
 */
function toTitleCase(str) {
    return str.replace(/\w\S*/g, (txt) => txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase());
}
/**
 * Truncate string to specified length
 */
function truncate(str, length, suffix = '...') {
    if (str.length <= length)
        return str;
    return str.substring(0, length - suffix.length) + suffix;
}
/**
 * Generate a random string
 */
function generateRandomString(length = 8) {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let result = '';
    for (let i = 0; i < length; i++) {
        result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
}
/**
 * Convert string to slug
 */
function toSlug(str) {
    return str
        .toLowerCase()
        .trim()
        .replace(/[^\w\s-]/g, '')
        .replace(/[\s_-]+/g, '-')
        .replace(/^-+|-+$/g, '');
}
// ============================================================================
// VALIDATION UTILITIES
// ============================================================================
/**
 * Validate email address
 */
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}
/**
 * Validate URL
 */
function isValidUrl(url) {
    try {
        new URL(url);
        return true;
    }
    catch {
        return false;
    }
}
/**
 * Validate Notion page ID
 */
function isValidNotionPageId(id) {
    const notionIdRegex = /^[a-zA-Z0-9]{32}$/;
    return notionIdRegex.test(id);
}
/**
 * Validate UUID
 */
function isValidUuid(uuid) {
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
    return uuidRegex.test(uuid);
}
// ============================================================================
// ARRAY & OBJECT UTILITIES
// ============================================================================
/**
 * Remove duplicates from array
 */
function removeDuplicates(array) {
    return [...new Set(array)];
}
/**
 * Group array by key
 */
function groupBy(array, key) {
    return array.reduce((groups, item) => {
        const group = String(item[key]);
        groups[group] = groups[group] || [];
        groups[group].push(item);
        return groups;
    }, {});
}
/**
 * Sort array by key
 */
function sortBy(array, key, direction = 'asc') {
    return [...array].sort((a, b) => {
        const aVal = a[key];
        const bVal = b[key];
        if (aVal < bVal)
            return direction === 'asc' ? -1 : 1;
        if (aVal > bVal)
            return direction === 'asc' ? 1 : -1;
        return 0;
    });
}
/**
 * Deep clone object
 */
function deepClone(obj) {
    if (obj === null || typeof obj !== 'object')
        return obj;
    if (obj instanceof Date)
        return new Date(obj.getTime());
    if (obj instanceof Array)
        return obj.map(item => deepClone(item));
    if (typeof obj === 'object') {
        const clonedObj = {};
        for (const key in obj) {
            if (obj.hasOwnProperty(key)) {
                clonedObj[key] = deepClone(obj[key]);
            }
        }
        return clonedObj;
    }
    return obj;
}
// ============================================================================
// NUMBER UTILITIES
// ============================================================================
/**
 * Format number with commas
 */
function formatNumber(num) {
    return num.toLocaleString();
}
/**
 * Format currency
 */
function formatCurrency(amount, currency = 'USD') {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency,
    }).format(amount);
}
/**
 * Calculate percentage
 */
function calculatePercentage(value, total) {
    if (total === 0)
        return 0;
    return Math.round((value / total) * 100);
}
/**
 * Clamp number between min and max
 */
function clamp(value, min, max) {
    return Math.min(Math.max(value, min), max);
}
// ============================================================================
// COLOR UTILITIES
// ============================================================================
/**
 * Generate random color
 */
function generateRandomColor() {
    const colors = [
        '#3B82F6', '#EF4444', '#10B981', '#F59E0B', '#8B5CF6',
        '#06B6D4', '#84CC16', '#F97316', '#EC4899', '#6366F1'
    ];
    return colors[Math.floor(Math.random() * colors.length)];
}
/**
 * Get color based on status
 */
function getStatusColor(status) {
    const statusColors = {
        'not_started': '#6B7280',
        'in_progress': '#F59E0B',
        'completed': '#10B981',
        'cancelled': '#EF4444',
        'low': '#10B981',
        'medium': '#F59E0B',
        'high': '#EF4444',
        'urgent': '#DC2626',
    };
    return statusColors[status] || '#6B7280';
}
// ============================================================================
// ERROR HANDLING UTILITIES
// ============================================================================
/**
 * Create standardized error object
 */
function createError(code, message, details) {
    return {
        code,
        message,
        details,
        timestamp: new Date().toISOString(),
    };
}
/**
 * Check if error is network error
 */
function isNetworkError(error) {
    return error.code === 'NETWORK_ERROR' ||
        error.message?.includes('network') ||
        error.message?.includes('fetch');
}
/**
 * Retry function with exponential backoff
 */
async function retry(fn, maxRetries = 3, delay = 1000) {
    let lastError;
    for (let i = 0; i < maxRetries; i++) {
        try {
            return await fn();
        }
        catch (error) {
            lastError = error;
            if (i < maxRetries - 1) {
                await new Promise(resolve => setTimeout(resolve, delay * Math.pow(2, i)));
            }
        }
    }
    throw lastError;
}
// ============================================================================
// STORAGE UTILITIES
// ============================================================================
/**
 * Safe localStorage get
 */
function safeLocalStorageGet(key) {
    try {
        const item = localStorage.getItem(key);
        return item ? JSON.parse(item) : null;
    }
    catch {
        return null;
    }
}
/**
 * Safe localStorage set
 */
function safeLocalStorageSet(key, value) {
    try {
        localStorage.setItem(key, JSON.stringify(value));
        return true;
    }
    catch {
        return false;
    }
}
/**
 * Safe localStorage remove
 */
function safeLocalStorageRemove(key) {
    try {
        localStorage.removeItem(key);
        return true;
    }
    catch {
        return false;
    }
}
// ============================================================================
// DEBOUNCE & THROTTLE
// ============================================================================
/**
 * Debounce function
 */
function debounce(func, wait) {
    let timeout;
    return (...args) => {
        clearTimeout(timeout);
        timeout = setTimeout(() => func(...args), wait);
    };
}
/**
 * Throttle function
 */
function throttle(func, limit) {
    let inThrottle;
    return (...args) => {
        if (!inThrottle) {
            func(...args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}
//# sourceMappingURL=index.js.map
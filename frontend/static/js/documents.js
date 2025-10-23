/**
 * Documents Page JavaScript
 * 
 * Handles audit trail display, document management,
 * and system action logging for The Luggage Room Boys Fund.
 */

document.addEventListener('DOMContentLoaded', function() {
    init();
});

/**
 * Initialize the documents page
 */
async function init() {
    try {
        // Check if audit trail section exists (admin only)
        const auditTable = document.getElementById('auditTable');
        if (auditTable) {
            await loadAuditLog();
        }
        
    } catch (error) {
        console.error('Initialization error:', error);
        showSnackbar('Failed to load page data. Please refresh.', 'error');
    }
}

/**
 * Load and display audit log data
 */
async function loadAuditLog() {
    try {
        const response = await fetch('/api/documents/audit-log');
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const logs = await response.json();
        
        const tbody = document.getElementById('auditTable');
        if (!tbody) return;
        
        tbody.innerHTML = '';
        
        if (!logs || logs.length === 0) {
            // Empty state
            tbody.innerHTML = `
                <tr>
                    <td colspan="5" style="text-align: center; padding: 40px;">
                        <span class="material-icons" style="font-size: 48px; color: var(--md-sys-color-on-surface-variant); opacity: 0.5;">history</span>
                        <div class="body-medium" style="margin-top: 12px; color: var(--md-sys-color-on-surface-variant);">
                            No audit events yet
                        </div>
                        <div class="body-small" style="margin-top: 4px; color: var(--md-sys-color-on-surface-variant);">
                            System actions will be logged here
                        </div>
                    </td>
                </tr>
            `;
            return;
        }
        
        // Populate table with audit logs
        logs.forEach(log => {
            const row = tbody.insertRow();
            
            // Timestamp
            const timestampCell = row.insertCell();
            timestampCell.textContent = formatTimestamp(log.timestamp);
            timestampCell.style.textAlign = 'left';
            timestampCell.style.fontFamily = 'monospace';
            timestampCell.style.fontSize = '13px';
            
            // User
            const userCell = row.insertCell();
            userCell.textContent = log.user || 'System';
            userCell.style.textAlign = 'left';
            
            // Action (with badge)
            const actionCell = row.insertCell();
            const actionBadge = createActionBadge(log.action);
            actionCell.appendChild(actionBadge);
            actionCell.style.textAlign = 'left';
            
            // Details
            const detailsCell = row.insertCell();
            detailsCell.textContent = formatDetails(log.details) || '—';
            detailsCell.style.textAlign = 'left';
            detailsCell.style.color = 'var(--md-sys-color-on-surface-variant)';
            detailsCell.style.fontSize = '14px';
            
            // IP Address
            const ipCell = row.insertCell();
            ipCell.textContent = log.ip_address || '—';
            ipCell.style.textAlign = 'left';
            ipCell.style.fontFamily = 'monospace';
            ipCell.style.fontSize = '13px';
            ipCell.style.color = 'var(--md-sys-color-on-surface-variant)';
        });
        
    } catch (error) {
        console.error('Error loading audit log:', error);
        showSnackbar('Failed to load audit trail', 'error');
        
        const tbody = document.getElementById('auditTable');
        if (tbody) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="5" style="text-align: center; padding: 40px;">
                        <span class="material-icons" style="font-size: 48px; color: var(--md-sys-color-error); opacity: 0.5;">error</span>
                        <div class="body-medium" style="margin-top: 12px; color: var(--md-sys-color-error);">
                            Failed to load audit trail
                        </div>
                        <div class="body-small" style="margin-top: 4px; color: var(--md-sys-color-on-surface-variant);">
                            Please try refreshing the page
                        </div>
                    </td>
                </tr>
            `;
        }
    }
}

/**
 * Refresh audit log data
 */
async function refreshAuditLog() {
    const auditTable = document.getElementById('auditTable');
    if (!auditTable) return;
    
    // Show loading state
    auditTable.innerHTML = `
        <tr>
            <td colspan="5" style="text-align: center; padding: 40px;">
                <span class="loading-spinner" style="display: inline-block; width: 24px; height: 24px; border: 3px solid var(--md-sys-color-outline); border-top-color: var(--md-sys-color-primary); border-radius: 50%; animation: spin 1s linear infinite;"></span>
                <div class="body-medium" style="margin-top: 12px; color: var(--md-sys-color-on-surface-variant);">
                    Refreshing audit log...
                </div>
            </td>
        </tr>
    `;
    
    await loadAuditLog();
    showSnackbar('Audit log refreshed', 'success');
}

/**
 * Create action badge element
 * @param {string} action - Action type
 * @returns {HTMLElement} Badge element
 */
function createActionBadge(action) {
    if (!action) return document.createTextNode('—');
    
    const badge = document.createElement('span');
    badge.className = 'action-badge';
    
    // Determine badge type based on action
    const actionLower = action.toLowerCase();
    
    if (actionLower.includes('invite') || actionLower.includes('join')) {
        badge.classList.add('invite');
    } else if (actionLower.includes('transaction') || actionLower.includes('contribution') || 
               actionLower.includes('distribution') || actionLower.includes('withdrawal')) {
        badge.classList.add('transaction');
    } else if (actionLower.includes('profile') || actionLower.includes('password') || 
               actionLower.includes('update')) {
        badge.classList.add('profile');
    } else {
        badge.classList.add('system');
    }
    
    // Format action text (replace underscores with spaces, capitalize)
    const formattedAction = action
        .replace(/_/g, ' ')
        .split(' ')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
        .join(' ');
    
    badge.textContent = formattedAction;
    
    return badge;
}

/**
 * Format timestamp for display
 * @param {string} timestamp - ISO timestamp string
 * @returns {string} Formatted timestamp
 */
function formatTimestamp(timestamp) {
    if (!timestamp) return '—';
    
    try {
        const date = new Date(timestamp);
        
        // Check if date is valid
        if (isNaN(date.getTime())) {
            return timestamp; // Return original if invalid
        }
        
        // Format as "Jan 15, 2025 3:45 PM"
        const dateOptions = { 
            year: 'numeric', 
            month: 'short', 
            day: 'numeric' 
        };
        
        const timeOptions = {
            hour: 'numeric',
            minute: '2-digit',
            hour12: true
        };
        
        const dateStr = date.toLocaleDateString('en-US', dateOptions);
        const timeStr = date.toLocaleTimeString('en-US', timeOptions);
        
        return `${dateStr} ${timeStr}`;
        
    } catch (error) {
        console.error('Error formatting timestamp:', error);
        return timestamp;
    }
}

/**
 * Format details object for display
 * @param {string|object} details - Details string or JSON object
 * @returns {string} Formatted details string
 */
function formatDetails(details) {
    if (!details) return null;
    
    try {
        // If it's already a string, return it
        if (typeof details === 'string') {
            // Try to parse as JSON
            try {
                const parsed = JSON.parse(details);
                return formatDetailsObject(parsed);
            } catch (e) {
                // Not JSON, return as-is
                return details;
            }
        }
        
        // If it's an object, format it
        if (typeof details === 'object') {
            return formatDetailsObject(details);
        }
        
        return String(details);
        
    } catch (error) {
        console.error('Error formatting details:', error);
        return String(details);
    }
}

/**
 * Format details object into readable string
 * @param {object} obj - Details object
 * @returns {string} Formatted string
 */
function formatDetailsObject(obj) {
    if (!obj || typeof obj !== 'object') return '';
    
    const parts = [];
    
    for (const [key, value] of Object.entries(obj)) {
        if (value !== null && value !== undefined) {
            // Format key (capitalize, remove underscores)
            const formattedKey = key
                .replace(/_/g, ' ')
                .split(' ')
                .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
                .join(' ');
            
            // Format value
            let formattedValue = value;
            
            // If value is a number and looks like money, format as currency
            if (typeof value === 'number' && (key.includes('amount') || key.includes('balance'))) {
                formattedValue = formatCurrency(value);
            }
            // If value is a date string, format as date
            else if (typeof value === 'string' && value.match(/^\d{4}-\d{2}-\d{2}/)) {
                formattedValue = formatDate(value);
            }
            
            parts.push(`${formattedKey}: ${formattedValue}`);
        }
    }
    
    return parts.join(', ');
}

/**
 * Format currency value
 * @param {number} amount - Amount to format
 * @returns {string} Formatted currency string
 */
function formatCurrency(amount) {
    if (amount === null || amount === undefined || isNaN(amount)) {
        return '$0.00';
    }
    
    const formatted = new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(amount);
    
    return formatted;
}

/**
 * Format date string
 * @param {string} dateString - ISO date string
 * @returns {string} Formatted date string
 */
function formatDate(dateString) {
    if (!dateString) return '—';
    
    try {
        const date = new Date(dateString);
        
        // Check if date is valid
        if (isNaN(date.getTime())) {
            return dateString; // Return original if invalid
        }
        
        // Format as "Jan 15, 2025"
        const options = { 
            year: 'numeric', 
            month: 'short', 
            day: 'numeric' 
        };
        
        return date.toLocaleDateString('en-US', options);
        
    } catch (error) {
        console.error('Error formatting date:', error);
        return dateString;
    }
}

/**
 * Show snackbar notification
 * @param {string} message - Message to display
 * @param {string} type - Type of notification ('success', 'error', 'info')
 */
function showSnackbar(message, type = 'info') {
    // Check if snackbar function exists in common.js
    if (typeof window.showSnackbar === 'function') {
        window.showSnackbar(message, type);
        return;
    }
    
    // Fallback: Create temporary snackbar if common.js not available
    const snackbar = document.createElement('div');
    snackbar.textContent = message;
    snackbar.style.cssText = `
        position: fixed;
        bottom: 20px;
        left: 50%;
        transform: translateX(-50%);
        background: var(--md-sys-color-inverse-surface);
        color: var(--md-sys-color-inverse-on-surface);
        padding: 16px 24px;
        border-radius: 8px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.3);
        z-index: 10000;
        font-family: 'Roboto', sans-serif;
        font-size: 14px;
        max-width: 90%;
    `;
    
    if (type === 'error') {
        snackbar.style.background = 'var(--md-sys-color-error)';
        snackbar.style.color = 'var(--md-sys-color-on-error)';
    } else if (type === 'success') {
        snackbar.style.background = 'var(--md-sys-color-tertiary)';
        snackbar.style.color = 'var(--md-sys-color-on-tertiary)';
    }
    
    document.body.appendChild(snackbar);
    
    setTimeout(() => {
        snackbar.remove();
    }, 3000);
}

/**
 * Download document (placeholder function)
 * @param {string} documentType - Type of document to download
 * @param {string} documentId - Document identifier
 */
function downloadDocument(documentType, documentId) {
    // Placeholder for future implementation
    console.log(`Download requested: ${documentType} - ${documentId}`);
    showSnackbar('Document download not yet available', 'info');
}

/**
 * Export audit log to CSV (future feature)
 */
function exportAuditLog() {
    // Placeholder for future implementation
    showSnackbar('Export feature coming soon', 'info');
}

/**
 * Filter audit log by action type (future feature)
 * @param {string} actionType - Action type to filter by
 */
function filterAuditLog(actionType) {
    // Placeholder for future implementation
    console.log(`Filter requested: ${actionType}`);
    showSnackbar('Filter feature coming soon', 'info');
}

// Add CSS for loading spinner animation
const style = document.createElement('style');
style.textContent = `
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
`;
document.head.appendChild(style);

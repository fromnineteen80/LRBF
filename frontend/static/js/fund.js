/**
 * Fund Management Page JavaScript
 * Handles fund overview, co-founder list, and invitation system
 * Railyard Markets - The Luggage Room Boys Fund
 */

document.addEventListener('DOMContentLoaded', function() {
    initializeFundPage();
});

/**
 * Initialize fund page and load data
 */
function initializeFundPage() {
    // Load all data
    loadFundOverview();
    loadCofounders();
    
    // Load pending invitations if admin section exists
    const pendingInvitesTable = document.getElementById('pendingInvitesTable');
    if (pendingInvitesTable) {
        loadPendingInvitations();
    }
    
    // Set up invitation form if it exists (admin only)
    const inviteForm = document.getElementById('inviteForm');
    if (inviteForm) {
        inviteForm.addEventListener('submit', handleSendInvitation);
    }
}

/**
 * Load fund overview statistics
 */
async function loadFundOverview() {
    try {
        const response = await fetch('/api/fund/overview');
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        
        // Update UI with fund statistics
        document.getElementById('totalCapital').textContent = formatCurrency(data.total_capital || 0);
        document.getElementById('cofounderCount').textContent = data.cofounder_count || 0;
        document.getElementById('yourOwnership').textContent = (data.user_ownership || 0).toFixed(2) + '%';
        
    } catch (error) {
        console.error('Error loading fund overview:', error);
        showSnackbar('Failed to load fund overview');
        
        // Show error state
        document.getElementById('totalCapital').textContent = 'Error';
        document.getElementById('cofounderCount').textContent = '-';
        document.getElementById('yourOwnership').textContent = '-';
    }
}

/**
 * Load co-founders list
 */
async function loadCofounders() {
    const tbody = document.getElementById('cofoundersTable');
    
    try {
        const response = await fetch('/api/fund/cofounders');
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const cofounders = await response.json();
        
        // Clear loading state
        tbody.innerHTML = '';
        
        if (cofounders.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="5" style="padding: 40px; text-align: center; color: var(--md-sys-color-on-surface-variant);">
                        No co-founders yet
                    </td>
                </tr>
            `;
            return;
        }
        
        // Populate table with co-founders
        cofounders.forEach(cofounder => {
            const row = document.createElement('tr');
            row.style.borderBottom = '1px solid var(--md-sys-color-outline-variant)';
            
            row.innerHTML = `
                <td style="padding: 16px;">
                    <div style="display: flex; align-items: center; gap: 12px;">
                        <span class="material-symbols-outlined" style="color: var(--md-sys-color-primary);">person</span>
                        <span style="font-weight: 500;">${escapeHtml(cofounder.name)}</span>
                    </div>
                </td>
                <td style="padding: 16px; color: var(--md-sys-color-on-surface-variant);">
                    ${escapeHtml(cofounder.email)}
                </td>
                <td style="padding: 16px; text-align: right; font-weight: 500;">
                    ${formatCurrency(cofounder.contribution)}
                </td>
                <td style="padding: 16px; text-align: right;">
                    <span style="display: inline-block; padding: 4px 12px; background: var(--md-sys-color-tertiary-container); color: var(--md-sys-color-on-tertiary-container); border-radius: 8px; font-weight: 500;">
                        ${cofounder.ownership.toFixed(2)}%
                    </span>
                </td>
                <td style="padding: 16px; color: var(--md-sys-color-on-surface-variant);">
                    ${formatDate(cofounder.joined_date)}
                </td>
            `;
            
            tbody.appendChild(row);
        });
        
    } catch (error) {
        console.error('Error loading co-founders:', error);
        tbody.innerHTML = `
            <tr>
                <td colspan="5" style="padding: 40px; text-align: center; color: var(--md-sys-color-error);">
                    <span class="material-symbols-outlined" style="font-size: 48px;">error</span>
                    <div style="margin-top: 16px;">Failed to load co-founders</div>
                </td>
            </tr>
        `;
        showSnackbar('Failed to load co-founders');
    }
}

/**
 * Load pending invitations (admin only)
 */
async function loadPendingInvitations() {
    const tbody = document.getElementById('pendingInvitesTable');
    
    try {
        const response = await fetch('/api/auth/pending-invitations');
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const invitations = await response.json();
        
        // Clear loading state
        tbody.innerHTML = '';
        
        if (invitations.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="4" style="padding: 40px; text-align: center; color: var(--md-sys-color-on-surface-variant);">
                        No pending invitations
                    </td>
                </tr>
            `;
            return;
        }
        
        // Populate table with pending invitations
        invitations.forEach(invite => {
            const row = document.createElement('tr');
            row.style.borderBottom = '1px solid var(--md-sys-color-outline-variant)';
            
            // Check if expired
            const expiresDate = new Date(invite.expires_date);
            const isExpired = expiresDate < new Date();
            
            row.innerHTML = `
                <td style="padding: 16px;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        ${escapeHtml(invite.email)}
                        ${isExpired ? '<span style="color: var(--md-sys-color-error); font-size: 12px;">(Expired)</span>' : ''}
                    </div>
                </td>
                <td style="padding: 16px; color: var(--md-sys-color-on-surface-variant);">
                    ${escapeHtml(invite.first_name || '-')}
                </td>
                <td style="padding: 16px; color: var(--md-sys-color-on-surface-variant);">
                    ${formatDate(invite.sent_date)}
                </td>
                <td style="padding: 16px; color: ${isExpired ? 'var(--md-sys-color-error)' : 'var(--md-sys-color-on-surface-variant)'};">
                    ${formatDate(invite.expires_date)}
                </td>
            `;
            
            tbody.appendChild(row);
        });
        
    } catch (error) {
        console.error('Error loading pending invitations:', error);
        tbody.innerHTML = `
            <tr>
                <td colspan="4" style="padding: 40px; text-align: center; color: var(--md-sys-color-error);">
                    <span class="material-symbols-outlined" style="font-size: 48px;">error</span>
                    <div style="margin-top: 16px;">Failed to load invitations</div>
                </td>
            </tr>
        `;
        showSnackbar('Failed to load pending invitations');
    }
}

/**
 * Handle send invitation form submission
 */
async function handleSendInvitation(event) {
    event.preventDefault();
    
    const form = event.target;
    const submitButton = form.querySelector('md-filled-button[type="submit"]');
    
    // Get form data
    const email = document.getElementById('inviteEmail').value.trim();
    const firstName = document.getElementById('inviteFirstName').value.trim();
    
    // Validate email
    if (!isValidEmail(email)) {
        showSnackbar('Please enter a valid email address');
        return;
    }
    
    // Validate first name
    if (!firstName) {
        showSnackbar('Please enter the recipient\'s first name');
        return;
    }
    
    // Disable submit button during request
    if (submitButton) {
        submitButton.disabled = true;
    }
    
    try {
        const response = await fetch('/api/auth/send-invitation', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                email: email,
                first_name: firstName
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            showSnackbar(`Invitation sent to ${email}`);
            
            // Clear form
            form.reset();
            
            // Reload pending invitations
            loadPendingInvitations();
        } else {
            showSnackbar(data.error || 'Failed to send invitation');
        }
    } catch (error) {
        console.error('Error sending invitation:', error);
        showSnackbar('Error sending invitation. Please try again.');
    } finally {
        // Re-enable submit button
        if (submitButton) {
            submitButton.disabled = false;
        }
    }
}

/**
 * Validate email address format
 */
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

/**
 * Format currency value
 */
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(amount);
}

/**
 * Format date string
 */
function formatDate(dateString) {
    if (!dateString) return '-';
    
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Show snackbar notification
 */
function showSnackbar(message) {
    const snackbar = document.getElementById('snackbar');
    if (!snackbar) return;
    
    const textElement = snackbar.querySelector('.snackbar-text');
    if (textElement) {
        textElement.textContent = message;
    }
    
    snackbar.classList.add('active');
    
    setTimeout(() => {
        snackbar.classList.remove('active');
    }, 4000);
}

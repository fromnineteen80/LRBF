/**
 * Ledger Page JavaScript
 * 
 * Handles capital transaction management, account summary display,
 * and transaction recording for The Luggage Room Boys Fund.
 */

document.addEventListener('DOMContentLoaded', function() {
    init();
});

/**
 * Initialize the ledger page
 */
async function init() {
    try {
        await loadLedgerSummary();
        await loadTransactions();
        
        // Load users for transaction modal if admin
        const transactionForm = document.getElementById('transactionForm');
        if (transactionForm) {
            await loadUsersForTransaction();
            
            // Set default date to today
            const dateInput = document.getElementById('transactionDate');
            if (dateInput) {
                dateInput.valueAsDate = new Date();
            }
            
            // Add form submit handler
            transactionForm.addEventListener('submit', function(e) {
                e.preventDefault();
                recordTransaction();
            });
        }
        
    } catch (error) {
        console.error('Initialization error:', error);
        showSnackbar('Failed to load page data. Please refresh.', 'error');
    }
}

/**
 * Load and display ledger summary metrics
 */
async function loadLedgerSummary() {
    try {
        const response = await fetch('/api/ledger/summary');
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        
        if (!data) {
            throw new Error('No data received');
        }
        
        // Update summary metrics
        document.getElementById('currentBalance').textContent = formatCurrency(data.current_balance || 0);
        document.getElementById('totalContributions').textContent = formatCurrency(data.total_contributions || 0);
        
        // Format YTD P&L with color
        const ytdElement = document.getElementById('ytdPL');
        const ytdValue = data.ytd_pl || 0;
        ytdElement.textContent = formatCurrency(ytdValue);
        
        if (ytdValue > 0) {
            ytdElement.style.color = 'var(--md-sys-color-tertiary)';
        } else if (ytdValue < 0) {
            ytdElement.style.color = 'var(--md-sys-color-error)';
        } else {
            ytdElement.style.color = 'var(--md-sys-color-on-surface)';
        }
        
        // Update ownership percentage
        document.getElementById('ownership').textContent = formatPercentage(data.ownership || 0);
        
    } catch (error) {
        console.error('Error loading ledger summary:', error);
        showSnackbar('Failed to load account summary', 'error');
        
        // Show error state
        document.getElementById('currentBalance').textContent = 'Error';
        document.getElementById('totalContributions').textContent = 'Error';
        document.getElementById('ytdPL').textContent = 'Error';
        document.getElementById('ownership').textContent = 'Error';
    }
}

/**
 * Load and display transaction history
 */
async function loadTransactions() {
    try {
        const response = await fetch('/api/ledger/transactions');
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const transactions = await response.json();
        
        const tbody = document.getElementById('transactionsTable');
        tbody.innerHTML = '';
        
        if (!transactions || transactions.length === 0) {
            // Empty state
            tbody.innerHTML = `
                <tr>
                    <td colspan="5" style="text-align: center; padding: 40px;">
                        <span class="material-icons" style="font-size: 48px; color: var(--md-sys-color-on-surface-variant); opacity: 0.5;">receipt_long</span>
                        <div class="body-medium" style="margin-top: 12px; color: var(--md-sys-color-on-surface-variant);">
                            No transactions yet
                        </div>
                        <div class="body-small" style="margin-top: 4px; color: var(--md-sys-color-on-surface-variant);">
                            Transactions will appear here once recorded
                        </div>
                    </td>
                </tr>
            `;
            return;
        }
        
        // Populate table with transactions
        transactions.forEach(tx => {
            const row = tbody.insertRow();
            
            // Date
            const dateCell = row.insertCell();
            dateCell.textContent = formatDate(tx.date);
            dateCell.style.textAlign = 'left';
            
            // Type (with chip)
            const typeCell = row.insertCell();
            typeCell.innerHTML = `<span class="chip ${tx.type}">${tx.type}</span>`;
            typeCell.style.textAlign = 'left';
            
            // Amount
            const amountCell = row.insertCell();
            amountCell.textContent = formatCurrency(tx.amount);
            amountCell.style.textAlign = 'right';
            amountCell.style.fontWeight = '500';
            
            // Apply color based on transaction type
            if (tx.type === 'contribution') {
                amountCell.style.color = 'var(--md-sys-color-tertiary)';
            } else if (tx.type === 'distribution') {
                amountCell.style.color = 'var(--md-sys-color-primary)';
            } else if (tx.type === 'withdrawal') {
                amountCell.style.color = 'var(--md-sys-color-error)';
            }
            
            // Balance After
            const balanceCell = row.insertCell();
            balanceCell.textContent = formatCurrency(tx.balance_after);
            balanceCell.style.textAlign = 'right';
            
            // Notes
            const notesCell = row.insertCell();
            notesCell.textContent = tx.notes || '—';
            notesCell.style.textAlign = 'left';
            notesCell.style.color = 'var(--md-sys-color-on-surface-variant)';
        });
        
    } catch (error) {
        console.error('Error loading transactions:', error);
        showSnackbar('Failed to load transaction history', 'error');
        
        const tbody = document.getElementById('transactionsTable');
        tbody.innerHTML = `
            <tr>
                <td colspan="5" style="text-align: center; padding: 40px;">
                    <span class="material-icons" style="font-size: 48px; color: var(--md-sys-color-error); opacity: 0.5;">error</span>
                    <div class="body-medium" style="margin-top: 12px; color: var(--md-sys-color-error);">
                        Failed to load transactions
                    </div>
                    <div class="body-small" style="margin-top: 4px; color: var(--md-sys-color-on-surface-variant);">
                        Please try refreshing the page
                    </div>
                </td>
            </tr>
        `;
    }
}

/**
 * Load co-founders list for transaction user dropdown (admin only)
 */
async function loadUsersForTransaction() {
    try {
        const response = await fetch('/api/fund/cofounders');
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const cofounders = await response.json();
        
        const select = document.getElementById('transactionUser');
        if (!select) return;
        
        // Clear existing options except the first one
        select.innerHTML = '<option value="">Select co-founder...</option>';
        
        if (!cofounders || cofounders.length === 0) {
            select.innerHTML = '<option value="">No co-founders found</option>';
            select.disabled = true;
            return;
        }
        
        // Add option for each co-founder
        cofounders.forEach(cf => {
            const option = document.createElement('option');
            // Need to get user_id from the API - for now use the name as identifier
            // This will need the API to return user_id
            option.value = cf.user_id || cf.email; // Fallback to email if user_id not available
            option.textContent = cf.name;
            select.appendChild(option);
        });
        
    } catch (error) {
        console.error('Error loading users for transaction:', error);
        const select = document.getElementById('transactionUser');
        if (select) {
            select.innerHTML = '<option value="">Error loading users</option>';
            select.disabled = true;
        }
    }
}

/**
 * Open the transaction recording modal
 */
function openTransactionModal() {
    const modal = document.getElementById('transactionModal');
    if (modal) {
        modal.style.display = 'flex';
        
        // Focus first input
        const firstInput = document.getElementById('transactionUser');
        if (firstInput) {
            setTimeout(() => firstInput.focus(), 100);
        }
    }
}

/**
 * Close the transaction recording modal
 */
function closeTransactionModal() {
    const modal = document.getElementById('transactionModal');
    if (modal) {
        modal.style.display = 'none';
        
        // Reset form
        const form = document.getElementById('transactionForm');
        if (form) {
            form.reset();
            
            // Reset date to today
            const dateInput = document.getElementById('transactionDate');
            if (dateInput) {
                dateInput.valueAsDate = new Date();
            }
        }
    }
}

/**
 * Record a new capital transaction
 */
async function recordTransaction() {
    try {
        // Get form data
        const userId = document.getElementById('transactionUser').value;
        const transactionType = document.getElementById('transactionType').value;
        const amount = parseFloat(document.getElementById('transactionAmount').value);
        const transactionDate = document.getElementById('transactionDate').value;
        const notes = document.getElementById('transactionNotes').value.trim();
        
        // Validate form data
        if (!userId) {
            showSnackbar('Please select a co-founder', 'error');
            return;
        }
        
        if (!transactionType) {
            showSnackbar('Please select a transaction type', 'error');
            return;
        }
        
        if (!amount || amount <= 0) {
            showSnackbar('Please enter a valid amount greater than zero', 'error');
            return;
        }
        
        if (!transactionDate) {
            showSnackbar('Please select a transaction date', 'error');
            return;
        }
        
        // Prepare request data
        const data = {
            user_id: userId,
            transaction_type: transactionType,
            amount: amount,
            transaction_date: transactionDate,
            notes: notes
        };
        
        // Show loading state
        const submitButton = document.querySelector('#transactionForm button[type="submit"]');
        const originalText = submitButton.textContent;
        submitButton.textContent = 'Recording...';
        submitButton.disabled = true;
        
        // Send request
        const response = await fetch('/api/ledger/record-transaction', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        // Restore button
        submitButton.textContent = originalText;
        submitButton.disabled = false;
        
        if (!response.ok) {
            throw new Error(result.error || `HTTP ${response.status}`);
        }
        
        if (result.success) {
            showSnackbar('Transaction recorded successfully', 'success');
            closeTransactionModal();
            
            // Refresh data
            await loadLedgerSummary();
            await loadTransactions();
        } else {
            throw new Error(result.error || 'Unknown error');
        }
        
    } catch (error) {
        console.error('Error recording transaction:', error);
        showSnackbar(error.message || 'Failed to record transaction', 'error');
        
        // Restore button if error occurred
        const submitButton = document.querySelector('#transactionForm button[type="submit"]');
        if (submitButton) {
            submitButton.textContent = 'Record Transaction';
            submitButton.disabled = false;
        }
    }
}

/**
 * Format currency value
 * @param {number} amount - The amount to format
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
 * Format percentage value
 * @param {number} value - The percentage to format
 * @returns {string} Formatted percentage string
 */
function formatPercentage(value) {
    if (value === null || value === undefined || isNaN(value)) {
        return '0.00%';
    }
    
    return value.toFixed(2) + '%';
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

// Close modal when clicking outside of it
document.addEventListener('DOMContentLoaded', function() {
    const modal = document.getElementById('transactionModal');
    if (modal) {
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                closeTransactionModal();
            }
        });
    }
});

// Close modal on Escape key
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        const modal = document.getElementById('transactionModal');
        if (modal && modal.style.display === 'flex') {
            closeTransactionModal();
        }
    }
});

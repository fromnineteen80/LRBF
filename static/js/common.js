/**
 * Common JavaScript Functions
 * Railyard Markets
 */

async function apiCall(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {'Content-Type': 'application/json', ...options.headers},
            ...options
        });
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error('API call failed:', error);
        showSnackbar('Error: ' + error.message);
        throw error;
    }
}

function showSnackbar(message) {
    const snackbar = document.getElementById('snackbar');
    snackbar.querySelector('.snackbar-text').textContent = message;
    snackbar.classList.add('active');
    setTimeout(() => snackbar.classList.remove('active'), 4000);
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {style: 'currency', currency: 'USD'}).format(amount);
}

function formatPercentage(value, decimals = 2) {
    return (value >= 0 ? '+' : '') + value.toFixed(decimals) + '%';
}

function formatNumber(num, decimals = 0) {
    return num.toFixed(decimals).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

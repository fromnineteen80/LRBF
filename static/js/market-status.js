/**
 * Market Status Module
 * 
 * Handles real-time market status updates and progress bar animation
 * for the railroad-themed Denver to DC market progress indicator.
 * 
 * Author: The Luggage Room Boys Fund
 * Date: October 2025
 */

class MarketStatusManager {
    constructor() {
        this.updateInterval = 30000; // 30 seconds
        this.intervalId = null;
        this.isInitialized = false;
        
        // DOM elements
        this.elements = {
            container: null,
            progressBar: null,
            indicator: null,
            trainIcon: null,
            timeRemaining: null,
            timeRemainingMobile: null
        };
        
        // Status styles
        this.statusStyles = {
            open: {
                barColor: '#4caf50',
                iconColor: '#2e7d32',
                icon: 'train'
            },
            pre_market: {
                barColor: '#ff9800',
                iconColor: '#e65100',
                icon: 'schedule'
            },
            after_hours: {
                barColor: '#2196f3',
                iconColor: '#1565c0',
                icon: 'bedtime'
            },
            closed: {
                barColor: '#9e9e9e',
                iconColor: '#616161',
                icon: 'night_sight_max'
            }
        };
    }
    
    init() {
        if (this.isInitialized) return;
        
        this.elements.container = document.getElementById('marketProgressContainer');
        this.elements.progressBar = document.getElementById('marketProgressBar');
        this.elements.indicator = document.getElementById('marketProgressIndicator');
        this.elements.trainIcon = document.getElementById('marketTrainIcon');
        this.elements.timeRemaining = document.getElementById('marketTimeRemaining');
        this.elements.timeRemainingMobile = document.getElementById('marketTimeRemainingMobile');
        
        if (!this.elements.container || !this.elements.progressBar || !this.elements.indicator) {
            console.warn('[MarketStatus] Required DOM elements not found');
            return;
        }
        
        this.isInitialized = true;
        this.updateMarketStatus();
        this.startUpdates();
        
        console.log('[MarketStatus] Initialized - updating every 30 seconds');
    }
    
    async fetchMarketStatus() {
        try {
            const response = await fetch('/api/market-status');
            if (!response.ok) throw new Error('HTTP ' + response.status);
            return await response.json();
        } catch (error) {
            console.error('[MarketStatus] Fetch error:', error);
            return { status: 'error', is_trading_day: false, progress_pct: 0, time_remaining: 'Error', error: error.message };
        }
    }
    
    async updateMarketStatus() {
        const data = await this.fetchMarketStatus();
        if (!data || data.status === 'error') {
            this.showError(data?.error || 'Unknown error');
            return;
        }
        this.updateProgressBar(data.progress_pct);
        this.updateStatusStyle(data.status);
        this.updateTimeDisplay(data.time_remaining, data.status);
        this.updateTooltip(data);
    }
    
    updateProgressBar(progressPct) {
        if (!this.elements.progressBar || !this.elements.indicator) return;
        const pct = Math.max(0, Math.min(100, progressPct));
        this.elements.progressBar.style.width = pct + '%';
        this.elements.indicator.style.left = 'calc(' + pct + '% - 12px)';
        this.elements.progressBar.style.transition = 'width 1s ease-in-out';
        this.elements.indicator.style.transition = 'left 1s ease-in-out';
    }
    
    updateStatusStyle(status) {
        const style = this.statusStyles[status] || this.statusStyles.closed;
        if (this.elements.progressBar) {
            this.elements.progressBar.style.backgroundColor = style.barColor;
        }
        if (this.elements.trainIcon) {
            this.elements.trainIcon.textContent = style.icon;
            this.elements.trainIcon.style.color = style.iconColor;
        }
        if (this.elements.indicator) {
            this.elements.indicator.style.backgroundColor = style.barColor;
            this.elements.indicator.style.borderColor = style.iconColor;
        }
    }
    
    updateTimeDisplay(timeRemaining, status) {
        if (this.elements.timeRemaining) this.elements.timeRemaining.textContent = timeRemaining;
        if (this.elements.timeRemainingMobile) this.elements.timeRemainingMobile.textContent = timeRemaining;
    }
    
    updateTooltip(data) {
        if (!this.elements.container) return;
        let tooltip = 'Market Progress: Denver to DC';
        if (data.is_trading_day) {
            tooltip += ' - ' + this.formatStatus(data.status);
            if (data.progress_pct > 0) tooltip += ' - ' + Math.round(data.progress_pct) + '% complete';
        } else {
            tooltip += ' - Market Closed';
            if (data.next_trading_day) {
                const nextDay = new Date(data.next_trading_day);
                tooltip += ' - Next: ' + nextDay.toLocaleDateString();
            }
        }
        this.elements.container.title = tooltip;
    }
    
    formatStatus(status) {
        const labels = {
            'open': 'Market Open',
            'pre_market': 'Pre-Market',
            'after_hours': 'After Hours',
            'closed': 'Market Closed'
        };
        return labels[status] || 'Unknown';
    }
    
    showError(errorMsg) {
        console.error('[MarketStatus] Error:', errorMsg);
        if (this.elements.timeRemaining) this.elements.timeRemaining.textContent = 'Error';
        if (this.elements.timeRemainingMobile) this.elements.timeRemainingMobile.textContent = 'Error';
        this.updateStatusStyle('closed');
    }
    
    startUpdates() {
        if (this.intervalId) clearInterval(this.intervalId);
        this.intervalId = setInterval(() => { this.updateMarketStatus(); }, this.updateInterval);
    }
    
    stopUpdates() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
    }
    
    destroy() {
        this.stopUpdates();
        this.isInitialized = false;
    }
}

window.marketStatusManager = new MarketStatusManager();

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => { window.marketStatusManager.init(); });
} else {
    window.marketStatusManager.init();
}

window.addEventListener('beforeunload', () => { window.marketStatusManager.destroy(); });

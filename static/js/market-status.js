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

        // Countdown timer for real-time clock updates
        this.countdownSeconds = 0;
        this.countdownInterval = null;
        this.lastAPIUpdate = null;
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
        this.updateTimeDisplay(data.time_remaining, data.status, data);
            this.startCountdown(data.time_remaining, data.status);
        this.updateTooltip(data);
    }
    
    updateProgressBar(progressPct) {
        if (!this.elements.progressBar || !this.elements.indicator) return;
        const pct = Math.max(0, Math.min(100, progressPct));
        this.elements.progressBar.style.width = pct + '%';
        this.elements.indicator.style.left = pct + '%';
        this.elements.progressBar.style.transition = 'width 1s ease-in-out';
        this.elements.indicator.style.transition = 'left 1s ease-in-out';
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
    startCountdown(timeStr, status) {
        // Clear any existing countdown
        if (this.countdownInterval) {
            clearInterval(this.countdownInterval);
        }
        
        // Only countdown during market hours
        if (status !== 'open' || !timeStr || timeStr === 'Closed' || timeStr === 'Pre-Market') {
            this.countdownSeconds = 0;
            return;
        }
        
        // Parse time string (H:MM:SS or MM:SS)
        this.countdownSeconds = this.parseTimeToSeconds(timeStr);
        this.lastAPIUpdate = Date.now();
        
        // Update display immediately
        this.updateCountdownDisplay();
        
        // Start countdown (every second)
        this.countdownInterval = setInterval(() => {
            if (this.countdownSeconds > 0) {
                this.countdownSeconds--;
                this.updateCountdownDisplay();
                this.updateProgressBarSmooth();
            }
        }, 1000);
    }
    
    parseTimeToSeconds(timeStr) {
        if (!timeStr) return 0;
        const parts = timeStr.split(':').map(p => parseInt(p) || 0);
        if (parts.length === 3) {
            // H:MM:SS format
            return parts[0] * 3600 + parts[1] * 60 + parts[2];
        } else if (parts.length === 2) {
            // MM:SS format
            return parts[0] * 60 + parts[1];
        }
        return 0;
    }
    
    formatSecondsToTime(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;
        
        if (hours > 0) {
            return hours + ':' + String(minutes).padStart(2, '0') + ':' + String(secs).padStart(2, '0');
        }
        return String(minutes).padStart(2, '0') + ':' + String(secs).padStart(2, '0');
    }
    
    updateCountdownDisplay() {
        if (!this.elements.timeRemaining || !this.elements.timeRemainingMobile) return;
        
        if (this.countdownSeconds > 0) {
            const timeStr = this.formatSecondsToTime(this.countdownSeconds);
            this.elements.timeRemaining.textContent = timeStr;
            this.elements.timeRemainingMobile.textContent = timeStr;
        }
    }
    
    updateProgressBarSmooth() {
        // Smooth progress bar movement during countdown
        // 6.5 hour trading day = 23,400 seconds
        const totalTradingSeconds = 23400;
        const elapsedSeconds = totalTradingSeconds - this.countdownSeconds;
        const progressPct = (elapsedSeconds / totalTradingSeconds) * 100;
        
        if (this.elements.progressBar && this.elements.indicator) {
            const pct = Math.max(0, Math.min(100, progressPct));
            this.elements.progressBar.style.width = pct + '%';
            this.elements.indicator.style.left = pct + '%';
        }
    }



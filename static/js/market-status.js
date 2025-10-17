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
        
        // Countdown properties
        this.countdownInterval = null;
        this.remainingSeconds = 0;
        this.lastSyncTime = 0;
        
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
        this.updateTimeDisplay(data.time_remaining, data.status);
        this.updateTooltip(data);
        
        // Start countdown if market is open and time_remaining is valid
        if (data.status === 'open' && data.time_remaining && data.time_remaining !== 'Error') {
            this.startCountdown(data.time_remaining);
        }
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
    
    // Countdown methods
    startCountdown(timeString) {
        // Stop existing countdown
        if (this.countdownInterval) {
            clearInterval(this.countdownInterval);
        }
        
        // Parse time string to seconds
        this.remainingSeconds = this.parseTimeToSeconds(timeString);
        this.lastSyncTime = Date.now();
        
        // Update display immediately
        this.updateCountdownDisplay();
        
        // Start countdown timer (updates every 1 second)
        this.countdownInterval = setInterval(() => {
            if (this.remainingSeconds > 0) {
                this.remainingSeconds--;
                this.updateCountdownDisplay();
                this.updateProgressBarSmooth();
            } else {
                // Market closed, stop countdown
                clearInterval(this.countdownInterval);
                this.countdownInterval = null;
            }
        }, 1000);
        
        console.log('[MarketStatus] Countdown started:', timeString);
    }
    
    parseTimeToSeconds(timeString) {
        // Parse "H:MM:SS" format to total seconds
        const parts = timeString.split(':');
        if (parts.length !== 3) return 0;
        
        const hours = parseInt(parts[0], 10);
        const minutes = parseInt(parts[1], 10);
        const seconds = parseInt(parts[2], 10);
        
        if (isNaN(hours) || isNaN(minutes) || isNaN(seconds)) return 0;
        
        return (hours * 3600) + (minutes * 60) + seconds;
    }
    
    formatSecondsToTime(totalSeconds) {
        // Format total seconds to "H:MM:SS"
        const hours = Math.floor(totalSeconds / 3600);
        const minutes = Math.floor((totalSeconds % 3600) / 60);
        const seconds = totalSeconds % 60;
        
        return hours + ':' + 
               String(minutes).padStart(2, '0') + ':' + 
               String(seconds).padStart(2, '0');
    }
    
    updateCountdownDisplay() {
        const timeString = this.formatSecondsToTime(this.remainingSeconds);
        if (this.elements.timeRemaining) {
            this.elements.timeRemaining.textContent = timeString;
        }
        if (this.elements.timeRemainingMobile) {
            this.elements.timeRemainingMobile.textContent = timeString;
        }
    }
    
    updateProgressBarSmooth() {
        // Smooth progress bar update during countdown
        // Assuming 6.5 hour trading day (9:30 AM - 4:00 PM) = 23400 seconds
        const TRADING_DAY_SECONDS = 23400;
        const elapsedSeconds = TRADING_DAY_SECONDS - this.remainingSeconds;
        const progressPct = (elapsedSeconds / TRADING_DAY_SECONDS) * 100;
        
        if (this.elements.progressBar && this.elements.indicator) {
            const pct = Math.max(0, Math.min(100, progressPct));
            this.elements.progressBar.style.width = pct + '%';
            this.elements.indicator.style.left = pct + '%';
        }
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
        if (this.countdownInterval) {
            clearInterval(this.countdownInterval);
            this.countdownInterval = null;
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

/**
 * Railyard Markets - Theme Controller
 * Handles light/dark theme switching using Material Design 3 tokens
 */

class ThemeController {
    constructor() {
        this.theme = this.getSavedTheme() || 'light';
        this.initializeTheme();
        this.setupThemeToggle();
    }
    
    /**
     * Get saved theme from localStorage
     */
    getSavedTheme() {
        return localStorage.getItem('railyard-theme');
    }
    
    /**
     * Save theme to localStorage
     */
    saveTheme(theme) {
        localStorage.setItem('railyard-theme', theme);
    }
    
    /**
     * Initialize theme on page load
     */
    initializeTheme() {
        this.applyTheme(this.theme);
    }
    
    /**
     * Apply theme to HTML element
     */
    applyTheme(theme) {
        const html = document.documentElement;
        
        // Remove both classes first
        html.classList.remove('light', 'dark');
        
        // Add the selected theme class
        html.classList.add(theme);
        
        // Update color scheme
        html.style.colorScheme = theme;
        
        // Update theme icon
        this.updateThemeIcon(theme);
        
        // Save to localStorage
        this.saveTheme(theme);
        
        // Update current theme
        this.theme = theme;
        
        // Dispatch custom event for other components
        window.dispatchEvent(new CustomEvent('themeChanged', {
            detail: { theme }
        }));
    }
    
    /**
     * Toggle between light and dark themes
     */
    toggleTheme() {
        const newTheme = this.theme === 'light' ? 'dark' : 'light';
        this.applyTheme(newTheme);
    }
    
    /**
     * Update theme icon in the UI
     */
    updateThemeIcon(theme) {
        const icon = document.getElementById('themeIcon');
        if (icon) {
            icon.textContent = theme === 'light' ? 'dark_mode' : 'light_mode';
        }
    }
    
    /**
     * Setup theme toggle button listeners
     */
    setupThemeToggle() {
        // Listen for keyboard shortcut (Ctrl/Cmd + Shift + L)
        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'L') {
                e.preventDefault();
                this.toggleTheme();
            }
        });
    }
    
    /**
     * Get current theme
     */
    getCurrentTheme() {
        return this.theme;
    }
    
    /**
     * Check if dark theme is active
     */
    isDark() {
        return this.theme === 'dark';
    }
    
    /**
     * Check if light theme is active
     */
    isLight() {
        return this.theme === 'light';
    }
}

// Initialize theme controller
const themeController = new ThemeController();

/**
 * Global function for theme toggle (called from HTML)
 */
function toggleTheme() {
    themeController.toggleTheme();
}

/**
 * Detect system theme preference
 */
function detectSystemTheme() {
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        return 'dark';
    }
    return 'light';
}

/**
 * Listen for system theme changes
 */
if (window.matchMedia) {
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
        if (!localStorage.getItem('railyard-theme')) {
            // Only auto-switch if user hasn't manually set a preference
            themeController.applyTheme(e.matches ? 'dark' : 'light');
        }
    });
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ThemeController, themeController, toggleTheme };
}

/**
 * Session Manager - Handles sliding window session renewal
 * 
 * Features:
 * - Activity tracking (keypress, mouse, file operations)
 * - Automatic session renewal on activity
 * - Sliding window: each activity resets 24-hour timer
 */

class SessionManager {
    constructor() {
        this.isActive = false;
        this.lastActivity = Date.now();
        this.renewalInProgress = false;
        this.activityThreshold = 30 * 1000; // 30 seconds of inactivity before renewal eligible
        this.renewalCheckInterval = 60 * 1000; // Check every minute
        this.renewalTimer = null;
        
        // Track various activity types
        this.activityEvents = [
            'keydown', 'keyup', 'keypress',
            'mousedown', 'mouseup', 'mousemove', 'click',
            'scroll', 'wheel',
            'touchstart', 'touchmove', 'touchend'
        ];
        
        this.init();
    }
    
    init() {
        if (this.hasValidSession()) {
            this.startTracking();
        }
    }
    
    hasValidSession() {
        const sessionId = localStorage.getItem('session_id');
        const username = localStorage.getItem('username');
        return !!(sessionId && username);
    }
    
    startTracking() {
        this.isActive = true;
        this.setupActivityListeners();
        this.startRenewalChecker();
        console.log('🔄 [SessionManager] Started activity tracking and renewal system');
    }
    
    stopTracking() {
        this.isActive = false;
        this.removeActivityListeners();
        this.stopRenewalChecker();
        console.log('🛑 [SessionManager] Stopped activity tracking');
    }
    
    setupActivityListeners() {
        this.activityHandler = this.onActivity.bind(this);
        
        // Listen for user activity
        this.activityEvents.forEach(event => {
            document.addEventListener(event, this.activityHandler, true);
        });
        
        // Listen for IDE-specific activities
        this.listenForIDEActivity();
    }
    
    removeActivityListeners() {
        this.activityEvents.forEach(event => {
            document.removeEventListener(event, this.activityHandler, true);
        });
    }
    
    listenForIDEActivity() {
        // Listen for custom IDE events (file save, code run, etc.)
        document.addEventListener('ide:file-save', this.activityHandler);
        document.addEventListener('ide:code-run', this.activityHandler);
        document.addEventListener('ide:file-open', this.activityHandler);
        document.addEventListener('ide:console-input', this.activityHandler);
    }
    
    onActivity() {
        if (!this.isActive) return;
        
        this.lastActivity = Date.now();
        
        // Throttle renewal checks - don't renew more than once every 30 seconds
        if (!this.renewalInProgress && this.shouldCheckRenewal()) {
            this.checkAndRenewSession();
        }
    }
    
    shouldCheckRenewal() {
        const timeSinceLastRenewal = Date.now() - (this.lastRenewalAttempt || 0);
        return timeSinceLastRenewal > this.activityThreshold;
    }
    
    startRenewalChecker() {
        // Periodic check for session renewal (backup to activity-based)
        this.renewalTimer = setInterval(() => {
            if (this.isActive && this.hasRecentActivity()) {
                this.checkAndRenewSession();
            }
        }, this.renewalCheckInterval);
    }
    
    stopRenewalChecker() {
        if (this.renewalTimer) {
            clearInterval(this.renewalTimer);
            this.renewalTimer = null;
        }
    }
    
    hasRecentActivity() {
        const timeSinceActivity = Date.now() - this.lastActivity;
        return timeSinceActivity < this.activityThreshold;
    }
    
    async checkAndRenewSession() {
        if (this.renewalInProgress || !this.hasValidSession()) return;
        
        try {
            this.renewalInProgress = true;
            this.lastRenewalAttempt = Date.now();
            
            const sessionId = localStorage.getItem('session_id');
            
            console.log('🔄 [SessionManager] Renewing session due to activity...');
            
            const response = await fetch('/api/renew-session', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ session_id: sessionId })
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Update localStorage with new expiration time
                localStorage.setItem('session_expires_at', data.expires_at);
                console.log('✅ [SessionManager] Session renewed until:', new Date(data.expires_at).toLocaleString());
            } else {
                console.warn('⚠️ [SessionManager] Session renewal failed:', data.error);
                this.handleRenewalFailure(data.error);
            }
            
        } catch (error) {
            console.error('❌ [SessionManager] Session renewal error:', error);
            this.handleRenewalFailure(error.message);
        } finally {
            this.renewalInProgress = false;
        }
    }
    
    handleRenewalFailure(error) {
        // Session might be expired or invalid
        if (error.includes('Invalid session') || error.includes('expired')) {
            console.log('🚪 [SessionManager] Session expired, will need re-authentication');
            
            // Clear invalid session data
            localStorage.removeItem('session_id');
            localStorage.removeItem('username');
            localStorage.removeItem('role');
            localStorage.removeItem('full_name');
            localStorage.removeItem('session_expires_at');
            
            // Stop tracking since session is invalid
            this.stopTracking();
            
            // Could trigger a re-login modal here if needed
            // this.triggerReLoginModal();
        }
    }
    
    // Manual session renewal (can be called from IDE actions)
    async renewSession() {
        return await this.checkAndRenewSession();
    }
    
    // Get session info
    getSessionInfo() {
        if (!this.hasValidSession()) return null;
        
        const expiresAt = localStorage.getItem('session_expires_at');
        const now = new Date();
        const expiry = expiresAt ? new Date(expiresAt) : null;
        
        return {
            username: localStorage.getItem('username'),
            role: localStorage.getItem('role'),
            expiresAt: expiry,
            timeLeft: expiry ? expiry - now : null,
            isNearExpiry: expiry ? (expiry - now) < (2 * 60 * 60 * 1000) : false // Less than 2 hours
        };
    }
    
    // Emit custom IDE events for activity tracking
    static emitIDEActivity(eventType, data = {}) {
        const event = new CustomEvent(`ide:${eventType}`, { detail: data });
        document.dispatchEvent(event);
    }
}

// Create singleton instance
const sessionManager = new SessionManager();

// Export for use in components
export default sessionManager;

// Also make available globally for debugging
if (typeof window !== 'undefined') {
    window.sessionManager = sessionManager;
}
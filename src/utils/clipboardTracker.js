/**
 * Clipboard tracking system for preventing external copy-paste in IDE
 * Only allows students to paste content that was previously copied within the IDE
 */

import { ElMessage } from 'element-plus';

class ClipboardTracker {
  constructor() {
    this.allowedContentHashes = new Set();
    this.hashSalt = 'ide_clipboard_salt_2025';
  }

  /**
   * Generate a hash for content to track IDE-internal copies
   */
  generateContentHash(content) {
    if (!content || typeof content !== 'string') return null;

    // Simple hash function - normalize content first
    const normalized = content.trim().replace(/\s+/g, ' ');
    let hash = 0;

    for (let i = 0; i < normalized.length; i++) {
      const char = normalized.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32bit integer
    }

    return `${hash}_${normalized.length}`;
  }

  /**
   * Track content as IDE-internal when copied
   */
  trackIDECopy(content) {
    if (!content) return;

    const hash = this.generateContentHash(content);
    if (hash) {
      this.allowedContentHashes.add(hash);
      console.log('[ClipboardTracker] Tracked IDE copy:', hash);
    }
  }

  /**
   * Check if content is allowed for pasting (was copied from IDE)
   */
  isContentAllowed(content) {
    if (!content) return false;

    const hash = this.generateContentHash(content);
    const isAllowed = hash && this.allowedContentHashes.has(hash);

    console.log('[ClipboardTracker] Paste validation:', {
      hash,
      isAllowed,
      trackedHashes: Array.from(this.allowedContentHashes)
    });

    return isAllowed;
  }

  /**
   * Get current user role from localStorage
   */
  getCurrentUserRole() {
    const role = localStorage.getItem('role') || 'student';
    console.log('[ClipboardTracker] Current user role:', role, {
      allLocalStorage: {
        role: localStorage.getItem('role'),
        username: localStorage.getItem('username'),
        session_id: localStorage.getItem('session_id')
      }
    });
    return role;
  }

  /**
   * Check if current user is a student
   */
  isStudent() {
    const role = this.getCurrentUserRole();
    return role === 'student';
  }

  /**
   * Check if current user has professor/admin privileges
   */
  isProfessor() {
    const role = this.getCurrentUserRole();
    const username = localStorage.getItem('username');

    // Check for admin/professor roles OR admin usernames
    const isAdminRole = ['admin', 'professor'].includes(role);
    const isAdminUser = ['admin_editor', 'test_admin', 'sl7927', 'sa9082', 'et2434'].includes(username);

    console.log('[ClipboardTracker] Admin check:', {
      role,
      username,
      isAdminRole,
      isAdminUser,
      finalResult: isAdminRole || isAdminUser
    });

    return isAdminRole || isAdminUser;
  }

  /**
   * Show restriction toast notification
   */
  showRestrictionToast() {
    ElMessage({
      message: 'Cannot paste from external websites. Only content copied within the IDE is allowed.',
      type: 'warning',
      duration: 5000,
      showClose: true
    });
  }

  /**
   * Validate paste operation for students
   * Returns true if paste should be allowed, false if blocked
   */
  async validatePaste(pasteContent) {
    console.log('[ClipboardTracker] validatePaste called:', {
      contentLength: pasteContent?.length,
      userRole: this.getCurrentUserRole(),
      isStudent: this.isStudent(),
      isProfessor: this.isProfessor(),
      environment: window.location.origin
    });

    // Always allow professors to paste anything
    if (this.isProfessor()) {
      console.log('[ClipboardTracker] Professor paste - allowed');
      return true;
    }

    // For students, check if content was copied from IDE
    if (this.isStudent()) {
      const isAllowed = this.isContentAllowed(pasteContent);

      if (!isAllowed) {
        console.log('[ClipboardTracker] Student external paste - blocked', {
          contentPreview: pasteContent?.substring(0, 100),
          trackedHashes: Array.from(this.allowedContentHashes)
        });
        this.showRestrictionToast();
        return false;
      }

      console.log('[ClipboardTracker] Student IDE paste - allowed');
      return true;
    }

    // Default allow for unknown roles
    console.log('[ClipboardTracker] Unknown role - defaulting to allow');
    return true;
  }

  /**
   * Clear old tracked content (optional cleanup)
   */
  clearTrackedContent() {
    this.allowedContentHashes.clear();
    console.log('[ClipboardTracker] Cleared all tracked content');
  }

  /**
   * Get stats about tracked content (for debugging)
   */
  getStats() {
    return {
      trackedItems: this.allowedContentHashes.size,
      userRole: this.getCurrentUserRole(),
      isStudent: this.isStudent()
    };
  }
}

// Create singleton instance
const clipboardTracker = new ClipboardTracker();

export default clipboardTracker;
# Bulk Upload Button - UI Theme Guide

## Button Location

The **Bulk Upload** button is located in the **left sidebar file tree header**, as the **5th button** (after New Folder, New File, Import, and before Refresh).

### Button Order (Left to Right):
```
1. 📁 New Folder
2. 📄 New File
3. ⬆️ Import Files (admin only)
4. 👥 Bulk Upload  (admin only) ← NEW BUTTON
5. 🔄 Refresh
```

---

## Theme Colors

### Dark Theme (Default)
- **Default state**: `rgba(255, 255, 255, 0.6)` (semi-transparent white)
- **Hover state**: `#9c27b0` (Purple) with background `rgba(255, 255, 255, 0.1)`
- **Active state**: Slightly scaled down (0.95)

### Light Theme
- **Default state**: `rgba(0, 0, 0, 0.6)` (semi-transparent black)
- **Hover state**: `#7b1fa2` (Darker purple)
- **Background on hover**: `rgba(0, 0, 0, 0.08)`

### High Contrast Theme
- **Default state**: `#ffffff` (Pure white)
- **Hover state**: `#ff00ff` (Bright magenta)
- **Background on hover**: `#333333` with yellow border `#ffff00`

---

## Color Meanings

Each button has a distinctive color when hovered:

| Button | Color on Hover | Meaning |
|--------|---------------|---------|
| New Folder | Green (`#67c23a`) | Create/Add |
| New File | Green (`#67c23a`) | Create/Add |
| Import Files | Orange (`#e6a23c`) | Upload/Import |
| **Bulk Upload** | **Purple** (`#9c27b0`) | **Bulk Operation** |
| Refresh | Blue (`#409eff`) | Reload/Sync |

---

## Visual Appearance

### Before Hover (All Buttons):
```
[📁] [📄] [⬆️] [👥] [🔄]  ← All gray/semi-transparent
```

### After Hovering Bulk Upload:
```
[📁] [📄] [⬆️] [👥] [🔄]
              ↑
            Purple glow + light background
```

---

## How to Identify the Button

1. **Icon**: Users icon (group of people)
2. **Tooltip**: "Bulk Upload to Students" (appears on hover)
3. **Color**: Purple when hovered
4. **Position**: 4th button from left (5th total)
5. **Visibility**: Only visible to admin users

---

## Admin Accounts (Who Can See It)

The button is visible ONLY when logged in as:
- `sl7927`
- `sa9082`
- `et2434`
- `admin_editor`
- `test_admin`

---

## CSS Classes Applied

```css
.action-btn {
  background: transparent;
  border: none;
  color: rgba(255, 255, 255, 0.6); /* Default state */
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.bulk-upload-btn:hover {
  color: #9c27b0; /* Purple for dark theme */
}

[data-theme="light"] .bulk-upload-btn:hover {
  color: #7b1fa2; /* Darker purple for light theme */
}

[data-theme="high-contrast"] .bulk-upload-btn:hover {
  color: #ff00ff; /* Bright magenta for accessibility */
}
```

---

## Testing Theme Changes

To test different themes in the IDE:

1. **Dark Theme** (default): Should see purple on hover
2. **Light Theme**: Go to Settings → Switch to light theme → Should see darker purple
3. **High Contrast Theme**: Go to Settings → Accessibility → Should see bright magenta

---

## Troubleshooting

### Issue: Button not visible at all
**Cause**: Not logged in as admin
**Solution**: Login with admin account (sa9082, sl7927, et2434)

### Issue: Button visible but no color change on hover
**Cause**: CSS not loaded or browser cache
**Solution**:
```bash
# Hard refresh browser
Ctrl + Shift + R (Windows/Linux)
Cmd + Shift + R (Mac)
```

### Issue: Button appears gray and doesn't change
**Cause**: Icon library not loaded
**Solution**: Check console for errors, verify lucide-vue-next is installed

---

## Expected Behavior

### On Page Load:
✅ Button appears in header (admin only)
✅ Button is semi-transparent white/gray
✅ Tooltip shows "Bulk Upload to Students"

### On Hover:
✅ Button changes to purple color
✅ Background becomes slightly lighter
✅ Smooth transition animation (0.2s)

### On Click:
✅ Bulk Upload Dialog opens
✅ Student list loads dynamically
✅ Shows count (e.g., "All Students (40)")

---

## Updated Testing Guide

When testing the UI:

1. **Start Backend**: `python server/server.py --port 10086`
2. **Start Frontend**: `npm run dev`
3. **Login as Admin**: Use `sa9082`
4. **Check Sidebar**: Look at file tree header
5. **Verify Button Order**: Should be 5 buttons total
6. **Hover Each Button**: Verify colors
   - New Folder/File: Green
   - Import: Orange
   - **Bulk Upload: Purple** ← Verify this!
   - Refresh: Blue
7. **Click Bulk Upload**: Dialog should open
8. **Test Theme Switch**: Change theme and verify colors update

---

## Color Accessibility

The purple color was chosen because:
- ✅ Distinct from other button colors (green, orange, blue)
- ✅ Indicates special/advanced operation
- ✅ Good contrast against dark background
- ✅ Accessible for color-blind users (different hue from other buttons)
- ✅ Maintains consistency across all three themes

---

**Last Updated**: January 2025
**Theme Colors Configured**: Dark, Light, High Contrast

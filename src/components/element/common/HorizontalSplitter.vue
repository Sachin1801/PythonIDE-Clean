<template>
  <div 
    class="horizontal-splitter"
    @mousedown="startDrag"
    @touchstart="startDrag"
    :class="{ 'dragging': isDragging }"
  >
    <div class="splitter-line"></div>
    <div class="splitter-handle">
      <div class="splitter-dots">
        <div class="dot"></div>
        <div class="dot"></div>
        <div class="dot"></div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'HorizontalSplitter',
  props: {
    currentHeight: {
      type: Number,
      default: 200
    },
    minHeight: {
      type: Number,
      default: 80
    },
    maxHeight: {
      type: Number,
      default: 400
    }
  },
  emits: ['resize'],
  data() {
    return {
      isDragging: false,
      startY: 0,
      startHeight: 0,
    }
  },
  methods: {
    startDrag(event) {
      event.preventDefault();
      
      this.isDragging = true;
      this.startY = event.type === 'mousedown' ? event.clientY : event.touches[0].clientY;
      
      // Get the current console height from parent
      this.startHeight = this.currentHeight;
      
      // Add global event listeners
      document.addEventListener('mousemove', this.handleDrag);
      document.addEventListener('mouseup', this.stopDrag);
      document.addEventListener('touchmove', this.handleDrag);
      document.addEventListener('touchend', this.stopDrag);
      
      // Prevent text selection during drag
      document.body.style.userSelect = 'none';
      document.body.style.cursor = 'ns-resize';
      
      this.$emit('resize', { type: 'start', height: this.startHeight });
    },
    
    handleDrag(event) {
      if (!this.isDragging) return;
      
      event.preventDefault();
      
      const currentY = event.type === 'mousemove' ? event.clientY : event.touches[0].clientY;
      const deltaY = this.startY - currentY; // Inverted because we want upward drag to increase height
      
      const newHeight = Math.max(
        this.minHeight, 
        Math.min(this.maxHeight, this.startHeight + deltaY)
      );
      
      this.$emit('resize', { type: 'drag', height: newHeight, delta: deltaY });
    },
    
    stopDrag() {
      if (!this.isDragging) return;
      
      this.isDragging = false;
      
      // Remove global event listeners
      document.removeEventListener('mousemove', this.handleDrag);
      document.removeEventListener('mouseup', this.stopDrag);
      document.removeEventListener('touchmove', this.handleDrag);
      document.removeEventListener('touchend', this.stopDrag);
      
      // Restore normal cursor and selection
      document.body.style.userSelect = '';
      document.body.style.cursor = '';
      
      this.$emit('resize', { type: 'end', height: this.currentHeight });
    }
  },

  
  beforeUnmount() {
    // Clean up event listeners if component is destroyed during drag
    if (this.isDragging) {
      this.stopDrag();
    }
  }
}
</script>

<style scoped>
.horizontal-splitter {
  position: relative;
  height: 6px;
  background: transparent;
  cursor: ns-resize;
  user-select: none;
  transition: background-color 0.2s ease;
  z-index: 10;
}

.horizontal-splitter:hover {
  background: rgba(0, 122, 204, 0.2);
}

.horizontal-splitter.dragging {
  background: rgba(0, 122, 204, 0.4);
}

.splitter-line {
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 1px;
  background: var(--border-primary, #3c3c3c);
  transform: translateY(-50%);
}

.splitter-handle {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 40px;
  height: 6px;
  background: var(--bg-secondary, #3C3F41);
  border-radius: 3px;
  opacity: 0;
  transition: opacity 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.horizontal-splitter:hover .splitter-handle,
.horizontal-splitter.dragging .splitter-handle {
  opacity: 1;
}

.splitter-dots {
  display: flex;
  gap: 3px;
}

.dot {
  width: 3px;
  height: 3px;
  background: var(--text-secondary, #969696);
  border-radius: 50%;
}

/* Visual feedback during drag */
.horizontal-splitter.dragging {
  position: relative;
}

.horizontal-splitter.dragging::before {
  content: '';
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.1);
  z-index: -1;
  pointer-events: none;
}

/* Theme support */
:root[data-theme="light"] .splitter-line {
  background: #e0e0e0;
}

:root[data-theme="light"] .splitter-handle {
  background: #f5f5f5;
}

:root[data-theme="light"] .dot {
  background: #666666;
}
</style>

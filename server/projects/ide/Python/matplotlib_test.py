import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
import os

# Get the directory of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))
output_path = os.path.join(current_dir, 'test_plot.png')

# Create sample data
x = np.linspace(0, 10, 100)
y1 = np.sin(x)
y2 = np.cos(x)
y3 = np.sin(x) * np.cos(x)

# Create a figure with subplots
fig, axes = plt.subplots(2, 2, figsize=(10, 8))
fig.suptitle('Matplotlib Test Plot', fontsize=16)

# Plot 1: Sine wave
axes[0, 0].plot(x, y1, 'b-', linewidth=2)
axes[0, 0].set_title('Sine Wave')
axes[0, 0].set_xlabel('x')fffffffffffffffffffffffffffff
axes[0, 0].set_ylabel('sin(x)')
axes[0, 0].grid(True, alpha=0.3)

# Plot 2: Cosine wave
axes[0, 1].plot(x, y2, 'r-', linewidth=2)
axes[0, 1].set_title('Cosine Wave')
axes[0, 1].set_xlabel('x')
axes[0, 1].set_ylabel('cos(x)')
axes[0, 1].grid(True, alpha=0.3)

# Plot 3: Combined plot
axes[1, 0].plot(x, y1, 'b-', label='sin(x)', linewidth=2)
axes[1, 0].plot(x, y2, 'r-', label='cos(x)', linewidth=2)
axes[1, 0].set_title('Sine and Cosine')
axes[1, 0].set_xlabel('x')
axes[1, 0].set_ylabel('y')
axes[1, 0].legend()
axes[1, 0].grid(True, alpha=0.3)

# Plot 4: Product
axes[1, 1].plot(x, y3, 'g-', linewidth=2)
axes[1, 1].set_title('sin(x) * cos(x)')
axes[1, 1].set_xlabel('x')
axes[1, 1].set_ylabel('sin(x) * cos(x)')
axes[1, 1].grid(True, alpha=0.3)

# Adjust layout and save
plt.tight_layout()
plt.savefig(output_path, dpi=100, bbox_inches='tight')
print(f"Plot saved successfully to: {output_path}")
print(f"File size: {os.path.getsize(output_path)} bytes")

# Show plot (if supported by the environment)
# plt.show()  # Commented out as it may not work in non-interactive environments
"""
Create a test PNG image to verify image viewer functionality
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import os

# Get the directory of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))

# Create a simple test image
fig, ax = plt.subplots(figsize=(8, 6))

# Create some test data
x = np.linspace(0, 10, 100)
y = np.sin(x)

# Plot the data
ax.plot(x, y, 'b-', linewidth=2, label='sin(x)')
ax.fill_between(x, 0, y, alpha=0.3)
ax.set_title('Test Image for IDE Viewer', fontsize=16)
ax.set_xlabel('X axis')
ax.set_ylabel('Y axis')
ax.grid(True, alpha=0.3)
ax.legend()

# Save as PNG in the same directory as the script
png_path = os.path.join(current_dir, 'test_image.png')
plt.savefig(png_path, dpi=100, bbox_inches='tight')
print(f"Test image saved as {png_path}")
plt.close()

# Also create a simple PDF
fig, axes = plt.subplots(2, 1, figsize=(8, 10))

# First plot
axes[0].plot(x, np.cos(x), 'r-', linewidth=2)
axes[0].set_title('Cosine Wave')
axes[0].grid(True, alpha=0.3)

# Second plot
axes[1].plot(x, np.tan(x), 'g-', linewidth=2)
axes[1].set_title('Tangent Wave')
axes[1].set_ylim(-10, 10)
axes[1].grid(True, alpha=0.3)

# Save as PDF in the same directory as the script
pdf_path = os.path.join(current_dir, 'test_document.pdf')
plt.tight_layout()
plt.savefig(pdf_path, format='pdf', bbox_inches='tight')
print(f"Test PDF saved as {pdf_path}")
plt.close()
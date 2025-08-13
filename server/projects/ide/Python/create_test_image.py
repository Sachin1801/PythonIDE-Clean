"""
Create a test PNG image to verify image viewer functionality
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import os
import sys

# Get the directory of the current script - handles both __file__ and sys.argv[0]
if hasattr(sys.modules[__name__], '__file__'):
    script_path = os.path.abspath(__file__)
else:
    script_path = os.path.abspath(sys.argv[0])

current_dir = os.path.dirname(script_path)
# Ensure we're in the Python directory under server/projects/ide
if 'temp' in current_dir:
    # If running from temp, find the actual script location
    import inspect
    frame = inspect.currentframe()
    if frame:
        filename = inspect.getfile(frame)
        if filename and os.path.exists(filename):
            current_dir = os.path.dirname(os.path.abspath(filename))
    # Fallback to the known Python directory
    if 'temp' in current_dir:
        current_dir = '/home/sachinadlakha/on-campus/PythonIDE-Clean/server/projects/ide/Python'

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
plt.close()

# Ensure file is fully written to disk
import time
time.sleep(0.1)  # Small delay to ensure file system sync

# Verify file was created
if os.path.exists(png_path):
    print(f"Test image saved as {png_path}")
    print(f"File size: {os.path.getsize(png_path)} bytes")
else:
    print(f"Error: PNG file was not created at {png_path}")

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
plt.close()

# Ensure file is fully written to disk
time.sleep(0.1)  # Small delay to ensure file system sync

# Verify file was created
if os.path.exists(pdf_path):
    print(f"Test PDF saved as {pdf_path}")
    print(f"File size: {os.path.getsize(pdf_path)} bytes")
else:
    print(f"Error: PDF file was not created at {pdf_path}")
import matplotlib.pyplot as plt
import numpy as np

x = np.linspace(0, 10, 100)
y = np.sin(x)

plt.figure(figsize=(8, 6))
plt.plot(x, y, 'b-', linewidth=2)
plt.title('Simple Sine Wave')
plt.xlabel('X')
plt.ylabel('Y')
plt.grid(True)

plt.savefig('graph.png', dpi=300, bbox_inches='tight')
plt.savefig('graph.pdf', bbox_inches='tight')
plt.close()

print("Files saved: graph.png and graph.pdf")
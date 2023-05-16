import matplotlib, os

# To avoid possible display issues when Matplotlib uses a non-GUI backend
if 'DISPLAY' not in os.environ:
    matplotlib.use('agg')
else:
    matplotlib.use('TKagg')

# Plot the figure
import matplotlib.pyplot as plt
plt.figure()
plt.plot(rho,te)
plt.show()

"""Numerical check of the square-wave Fourier series and the Gibbs overshoot.
f(x) = sign(sin x), period 2*pi, jumps of height 2 at multiples of pi."""
import numpy as np
from scipy.integrate import quad
from scipy.special import sici

# 1) coefficients b_n = (1/pi) * int_{-pi}^{pi} f(x) sin(nx) dx
for n in range(1, 10):
    val = quad(lambda x: np.sign(np.sin(x)) * np.sin(n * x), -np.pi, np.pi, points=[0])[0] / np.pi
    exp = 4 / (np.pi * n) if n % 2 else 0.0
    print(f"b_{n}: numeric {val:+.6f}   4/(pi n) for odd n: {exp:+.6f}")

# 2) Gibbs: peak of the partial sum S_N just right of the jump at x=0
def S(x, N):
    return sum(4 / (np.pi * n) * np.sin(n * x) for n in range(1, N + 1, 2))

limit = 2 / np.pi * sici(np.pi)[0]           # (2/pi) Si(pi)
print(f"\n(2/pi) Si(pi) = {limit:.6f}; overshoot above 1 = {limit-1:.6f}; as fraction of jump 2 = {(limit-1)/2*100:.3f}%")
for N in [1, 3, 5, 7, 9, 25, 49, 99, 199]:
    x = np.linspace(1e-6, 2 * np.pi / (N + 1), 20001)
    y = S(x, N)
    i = y.argmax()
    print(f"N={N:>3}: max S_N = {y[i]:.5f} at x = {x[i]:.5f} (pi/(N+1) = {np.pi/(N+1):.5f}); overshoot/jump = {(y[i]-1)/2*100:.3f}%")

import ctypes
import sys
from gmpy2 import xmpz

if __name__ == '__main__':
    a = xmpz(0)
    print(bin(a))

    a[64] = 1
    print(bin(a))
    a = a << 1
    print(bin(a))

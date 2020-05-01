import copy
import ctypes
import io
from math import floor

rot = [
    [0, 36, 3, 41, 18],
    [1, 44, 10, 45, 2],
    [62, 6, 43, 15, 61],
    [28, 55, 25, 21, 56],
    [27, 20, 39, 8, 14]
]

rc_24 = (ctypes.c_ulonglong * 24)(*[
    0x1,
    0x8082,
    0x800000000000808a,
    0x8000000080008000,
    0x808b,
    0x80000001,
    0x8000000080008081,
    0x8000000000008009,
    0x8a,
    0x88,
    0x80008009,
    0x8000000a,
    0x8000808b,
    0x800000000000008b,
    0x8000000000008089,
    0x8000000000008003,
    0x8000000000008002,
    0x8000000000000080,
    0x800a,
    0x800000008000000a,
    0x8000000080008081,
    0x8000000000008080,
    0x80000001,
    0x8000000080008008
])


def roll_reg_left(arr, beg):
        arr[beg] =  ((arr[beg] << 1) | (arr[beg] >> 63))


def rolln_reg_left(arr, beg, nbits):
    for n in range(nbits):
        roll_reg_left(arr, beg)


def chi_operation(dst, ai, b, r1, r2, r3):
    for i in range(8):
        dst[ai + i] = b[r1 + i] ^ (~b[r2 + i] & b[r3 + i])


def dump_array(b: bytearray, n):
    for z in range(n):
        if z != 0 and z % 8 == 0:
            print("")
        v = b[z]
        print(f"{v:02x}|", end="")

    print("")


def dump_buffer(b: bytearray):
    for i in range(len(b)):
        x = floor((i / 8) % 5)
        y = floor((i / 40) % 5)
        if i != 0 and i % 8 == 0: print("")

        if i % 8 == 0 : print(f"({x},{y}):", end="")
        v = b[i]
        print(f"{v:02x}|", end="")

    print("")



class StateUnion(ctypes.Union):
    _fields_ = [("buffer", ctypes.c_ubyte * 200),
                ("register", ctypes.c_ulonglong * 25)]

    def check_shift(self):
        self.buffer[0] = 0x01;

        for x in range(65):
            self.register[0] = ((self.register[0] << 1) | (self.register[0] >> 63))
            dump_buffer(self.buffer)
            print("--------")


class State(ctypes.Union):
    _fields_ = [("buffer", ctypes.c_ubyte * 200),
                ("register", ctypes.c_ulonglong * 25)]

class B(ctypes.Union):
    _fields_ = [("bite", ctypes.c_ubyte * 40),
                ("register", ctypes.c_ulonglong * 5)]


class Keccak:
    # 25 * 64 = 25 * 8 * 8 = 200 * 8 = 1600
    # 64 * 5 = 8 * 8 * 5 = 8 * 40 = 320
    RATE = 136
    STATE_SIZE = 200
    state = State()
    b = State()

    def _theta(self):
        tmp1 = B()

        for i in range(25):
            tmp1.register[i % 5] ^= self.state.register[i]

        tmp2 = B()
        tmp2.bite = copy.deepcopy(tmp1.bite)
        for x in range(5):
            rolln_reg_left(tmp2.register, x, 1)

        d = B()
        for i in range(5):
            x1 = (i + 4) % 5
            x2 = (i + 1) % 5
            d.register[i] = tmp1.register[x1] ^ tmp2.register[x2]

        for i in range(25):
            self.state.register[i] ^= d.register[i%5]

    def _rho_pi(self):
        b = self.b
        for x in range(200): b.buffer[x] = 0x0

        for x in range(5):
            for y in range(5):
                bx = y
                by = (2 * x + 3 * y) % 5
                rv = rot[x][y]
                #print(f"({x},{y})=>({bx},{by}) : {rv}")
                b_i = by + bx * 5
                i = x + y * 5
                b.register[b_i] = self.state.register[i]

                rolln_reg_left(b.register, b_i, rv)


    def _chi(self):
        a = self.state.buffer
        B = self.b
        for x in range(5):
            for y in range(5):
                x1 = (x + 1) % 5
                x2 = (x + 2) % 5
                bi = x * 5 + y
                b1 = x1 * 5 + y
                b2 = x2 * 5 + y
                tmp = self.b.register[bi] ^ (~B.register[b1] & B.register[b2])
                self.state.register[x + y * 5] = tmp

    def _iota(self, rnd):
        a = self.state.register
        a[0] = a[0] ^ rc_24[rnd]

    def _rounds(self):
        for x in range(24):
            self._theta()
            self._rho_pi()
            self._chi()
            self._iota(x)

    def _xorin(self, buffer: State):
        for i in range(0, len(buffer)):
            self.state.buffer[i] ^= buffer[i]

    def _absorb(self):
        self._rounds()

    def hash(self, input: io.BytesIO, in_len, security=256):
        reader = io.BufferedReader(input)
        buffer = reader.read(self.RATE)
        while len(buffer) > self.RATE:
            self._xorin(buffer)
            self._absorb()
            buffer = reader.read(self.RATE)

        self._xorin(buffer)
        self.state.buffer[len(buffer)] ^= 0x01
        self.state.buffer[self.RATE - 1] ^= 0x80
        self._absorb()

        return self.state.buffer[: int(security / 8)]

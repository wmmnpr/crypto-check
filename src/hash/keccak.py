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

class State(ctypes.Union):
    _fields_ = [("buffer", ctypes.c_ubyte * 200),
                ("register", ctypes.c_ulonglong * 25)]

class Plane(ctypes.Union):
    _fields_ = [("bite", ctypes.c_ubyte * 40),
                ("register", ctypes.c_ulonglong * 5)]


class Keccak:

    RATE = 136
    STATE_SIZE = 200
    state = State()
    aux_state = State()

    def _theta(self):
        tmp1 = Plane()
        for i in range(25):
            tmp1.register[i % 5] ^= self.state.register[i]

        tmp2 = Plane()
        tmp2.bite = copy.deepcopy(tmp1.bite)
        for x in range(5):
            rolln_reg_left(tmp2.register, x, 1)

        tmp3 = Plane()
        for i in range(5):
            x1 = (i + 4) % 5
            x2 = (i + 1) % 5
            tmp3.register[i] = tmp1.register[x1] ^ tmp2.register[x2]

        for i in range(25):
            self.state.register[i] ^= tmp3.register[i%5]


    def _rho_pi(self):
        for x in range(200): self.aux_state.buffer[x] = 0x0
        for x in range(5):
            for y in range(5):
                bx = y
                by = (2 * x + 3 * y) % 5
                rv = rot[x][y]
                b_i = by + bx * 5
                i = x + y * 5
                self.aux_state.register[b_i] = self.state.register[i]

                rolln_reg_left(self.aux_state.register, b_i, rv)

    def _chi(self):
        for x in range(5):
            for y in range(5):
                x1 = (x + 1) % 5
                x2 = (x + 2) % 5
                bi = x * 5 + y
                b1 = x1 * 5 + y
                b2 = x2 * 5 + y
                tmp = self.aux_state.register[bi] ^ (~self.aux_state.register[b1] & self.aux_state.register[b2])
                self.state.register[x + y * 5] = tmp

    def _iota(self, rnd):
        self.state.register[0] = self.state.register[0] ^ rc_24[rnd]

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
        for x in range(200): self.state.buffer[x] = 0x0
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

        return "".join(map(lambda x: f"{x:02x}", self.state.buffer[: int(security / 8)]))

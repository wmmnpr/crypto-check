import copy
import ctypes
import io

rot = [
    [0, 36, 3, 41, 18],
    [1, 44, 10, 45, 2],
    [62, 6, 43, 15, 61],
    [28, 55, 25, 21, 56],
    [27, 20, 39, 8, 14]
]

rc_24 = [
    [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01],
    [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x80, 0x82],
    [0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x80, 0x8a],
    [0x80, 0x00, 0x00, 0x00, 0x80, 0x00, 0x80, 0x00],
    [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x80, 0x8b],
    [0x00, 0x00, 0x00, 0x00, 0x80, 0x00, 0x00, 0x01],
    [0x80, 0x00, 0x00, 0x00, 0x80, 0x00, 0x80, 0x81],
    [0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x80, 0x09],
    [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x8a],
    [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x88],
    [0x00, 0x00, 0x00, 0x00, 0x80, 0x00, 0x80, 0x09],
    [0x00, 0x00, 0x00, 0x00, 0x80, 0x00, 0x00, 0x0a],
    [0x00, 0x00, 0x00, 0x00, 0x80, 0x00, 0x80, 0x8b],
    [0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x8b],
    [0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x80, 0x89],
    [0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x80, 0x03],
    [0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x80, 0x02],
    [0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x80],
    [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x80, 0x0a],
    [0x80, 0x00, 0x00, 0x00, 0x80, 0x00, 0x00, 0x0a],
    [0x80, 0x00, 0x00, 0x00, 0x80, 0x00, 0x80, 0x81],
    [0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x80, 0x80],
    [0x00, 0x00, 0x00, 0x00, 0x80, 0x00, 0x00, 0x01],
    [0x80, 0x00, 0x00, 0x00, 0x80, 0x00, 0x80, 0x08]
]


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
    for y in range(5):
        for x in range(5):
            i = x * 8 + y * 40
            print(f"({x},{y}):", end="")
            for z in range(8):
                zi = i + z
                v = b[zi]
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

def rol(self, reg_id):
    roll_reg_left(self.buffer, reg_id * 8)


def roln(self, reg_id, times):
    for x in range(times):
        self.rol(reg_id)

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
        print("_theta begin")
        #dump_buffer(self.state.buffer)
        c1 = B()
        for x in range(5):
            for y in range(5):
                for z in range(8):
                    ri = x * 8 + y * 40 + z
                    ci = z + x * 8
                    c1.bite[ci] ^= self.state.buffer[ri]

        c2 = B()
        c2.bite = copy.deepcopy(c1.bite)
        for x in range(5):
            rolln_reg_left(c2.register, x, 1)

        d = B()
        for x in range(5):
            x1 = (x + 4) % 5
            x2 = (x + 1) % 5
            for z in range(8):
                d.bite[x * 8 + z] = c1.bite[x1 * 8 + z] ^ c2.bite[x2 * 8 + z]

        for x in range(5):
            for y in range(5):
                for z in range(8):
                    si = x * 8 + y * 40 + z
                    di = z + x * 8
                    self.state.buffer[si] ^= d.bite[di]


        dump_buffer(self.state.buffer)
        print("_theta end")
    def _rho_pi(self):
        print("_rho_pi begin")

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

        dump_buffer(b.buffer)
        print("_rho_pi end")

    def _chi(self):
        print("_chi begin")
        a = self.state.buffer
        b = self.b.buffer
        for y in range(5):
            for x in range(5):
                a_i = x * 8 + y * 40
                b_i = a_i
                b2_i = (x + 1) % 5 * 8 + (y * 40)
                b3_i = (x + 2) % 5 * 8 + (y * 40)
                chi_operation(a, a_i, b, b_i, b2_i, b3_i)

        dump_buffer(a)
        print("_chi end")
    def _iota(self, rnd):
        a = self.state.buffer
        for i in range(8):
            a[i] = a[i] ^ rc_24[rnd][i]

    def _rounds(self):
        for x in range(24):
            print(f"*********  round({x}) ****************")
            self._theta()
            dump_buffer(self.state.buffer)
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

        dump_buffer(self.state.buffer)
        for i in range(32):
            v = self.state.buffer[i]
            print(f"{v:02x}|", end="")
        print("")
        return self.state.buffer[: int(security / 8)]

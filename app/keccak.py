import copy
import io
import ctypes

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
    f = arr[beg] >> 7 & 0x01
    for x in range(7):
        i = beg + x
        v1 = arr[i]
        v2 = arr[i + 1]
        t1 = 0xff & v1 << 1
        t2 = 0xff & v2 >> 7
        arr[i] = t1 ^ t2

    l = 0xff & arr[beg + 7] << 1
    arr[beg + 7] = l ^ f


def rolln_reg_left(arr: bytearray, beg, nbits):
    for n in range(nbits):
        roll_reg_left(arr, beg)

def chi_operation(dst, ai, b, r1, r2, r3):
    for i in range(8):
        dst[ai+i] = b[r1+i] ^ (~b[r2+i] & b[r3+i])

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
            self.register[0] = ((self.register[0]  << 1) | (self.register[0] >> 63))
            dump_buffer(self.buffer)
            print("--------")

class State():
    # _fields_ = [("buffer", c_ubyte * 200),
    #            ("register", c_ulonglong * 25)]

    buffer = bytearray(200)
    b = bytearray(200)

    def print(self):
        for x in range(200):
            if x % 8 == 0:
                print("", end="|")
            print(hex(self.buffer[x]), end="|")
        print("")
        for x in range(200):
            value = self.buffer[x]
            v1 = format(value, '#010b')
            print(v1, end="|")

    def rol(self, reg_id):
        roll_reg_left(self.buffer, reg_id * 8)

    def roln(self, reg_id, times):
        for x in range(times):
            self.rol(reg_id)

class Keccak:
    # 25 * 64 = 25 * 8 * 8 = 200 * 8 = 1600
    # 64 * 5 = 8 * 8 * 5 = 8 * 40 = 320
    RATE = 136
    STATE_SIZE = 200
    state = State()

    def _theta(self):
        dump_buffer(self.state.buffer)
        c1 = bytearray(40)
        for x in range(5):
            for y in range(5):
                for z in range(8):
                    ri = x * 8 + y * 40 + z
                    ci = z + x * 8
                    c1[ci] ^= self.state.buffer[ri]

        dump_array(c1, 40)
        print("")

        c2 = copy.deepcopy(c1)
        for x in range(5):
            xi = x * 8
            rolln_reg_left(c2, xi, 1)

        dump_array(c2, 40)
        print("")

        d = bytearray(40)
        for x in range(5):
            x1 = (x + 4) % 5
            x2 = (x + 1) % 5
            for z in range(8):
                d[x * 8 + z] = c1[x1 * 8 + z] ^ c2[x2 * 8 + z]

        dump_array(d, 40)
        print("")

        for x in range(5):
            for y in range(5):
                for z in range(8):
                    si = x * 8 + y * 40 + z
                    di = z + x * 8
                    self.state.buffer[si] ^= d[di]

    def _rho_pi(self):
        b = self.state.b
        for x in range(200): b[x]=0x0

        for x in range(5):
            for y in range(5):
                bx = y
                by = (2 * x + 3 * y) % 5
                rv = rot[x][y]
                #print(f"({x},{y})=>({bx},{by}) : {rv}")
                b_i = bx * 8 + by * 40
                for z in range(8):
                    b[b_i + z] = self.state.buffer[x * 8 + y * 40 + z]

                rolln_reg_left(b, b_i, rv)

    def _chi(self):
        a = self.state.buffer
        b = self.state.b
        for y in range(5):
            for x in range(5):
                a_i = x*8 + y*40
                b_i = a_i
                b2_i = (x+1)%5*8 + (y*40)
                b3_i = (x+2)%5*8 + (y*40)
                chi_operation(a, a_i, b, b_i, b2_i, b3_i)

    def _iota(self, rnd):
        a = self.state.buffer
        for i in range(8):
            a[i] =  a[i] ^ rc_24[rnd][i]

    def _rounds(self):
        for x in range(24):
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

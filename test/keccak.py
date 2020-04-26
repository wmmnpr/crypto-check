import io
import unittest
from ctypes import *


from app.keccak import Keccak, StateUnion


class TestKeccak(unittest.TestCase):

    def test_init(self):
        keccak = Keccak()

        buffer = bytearray(200)
        b1 : c_ubyte = 0x00

        for y in range(5):
            for x in range(5):
                for z in range(8):
                    buffer[x * 8 + y * 40 + z] = b1
                b1 = b1 + 1

        input = io.BytesIO(buffer)
        h = keccak.hash(input)

        self.assertEqual('foo'.upper(), 'FOO')

    def test_hello(self):
        keccak = Keccak()

        text = b'hello world'
        input = io.BytesIO(text)
        h = keccak.hash(input, len(text))



        print(f"{h}")

    def test_shift(self):

        s = StateUnion()

        s.check_shift()

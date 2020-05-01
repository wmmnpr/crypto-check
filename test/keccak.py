import io
import unittest
from ctypes import *

from hash.keccak import Keccak

class TestKeccak(unittest.TestCase):

    def test_hello_world(self):
        keccak = Keccak()

        text = b'hello world'
        input = io.BytesIO(text)
        hash_value = keccak.hash(input, len(text))

        self.assertEqual("47173285a8d7341e5e972fc677286384f802f8ef42a5ec5f03bbfa254cb01fad", hash_value)

    def test_francis(self):
        keccak = Keccak()

        text = b'francis'
        input = io.BytesIO(text)
        hash_value = keccak.hash(input, len(text))

        self.assertEqual("828e98e646107a98969689b6132c40f9bec33f0aae1cb9fab45105ff26ff8275", hash_value)


    def test_longer_input(self):
        keccak = Keccak()

        text = b'There are many variations of passages of Lorem Ipsum available, but the majority have suffered alteration in some form.'
        input = io.BytesIO(text)
        hash_value = keccak.hash(input, len(text))

        self.assertEqual("fd7af216158b36fb82382158fcaecfc8cc2f9112d09e4350e000595758d6212f", hash_value)



import os
import binascii


def generate_key():
    key = binascii.hexlify(os.urandom(4))
    return str(key)[2:-1]
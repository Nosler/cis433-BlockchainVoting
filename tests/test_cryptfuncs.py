# Authors: Sam Champer and Andi Nosler
# A suite of test functions that test the cryptography function suite.
# Uses the python unittest test suite.

from unittest import TestCase
from cryptfuncs import *


class TestCryptfuncs(TestCase):
    def setUp(self):
        self.public, self.private = new_rsa(1024)

    def test_keys(self):
        # Test that keys are generating properly.
        self.assertIsInstance(self.public, RSA.RsaKey)
        self.assertIsInstance(self.private, RSA.RsaKey)
        self.assertIsInstance(self.public.export_key().decode(), str)
        self.assertIsInstance(self.private.export_key().decode(), str)

    def test_private_to_public(self):
        # Test that private key can give public key.
        self.assertEqual(get_public_key(self.private), self.public)

    def test_encrypt_decrypt(self):
        # Test to make sure message can be encrypted/decrypted with public and private keys.
        message = "Time to test to see if a message can be encrypted and then decrypted!"
        encrypted_message = encrypt(message, self.public)
        decrypted_message = decrypt(encrypted_message, self.private)
        self.assertEqual(message, decrypted_message)

    def test_sign(self):
        # Test to make sure private key can sign a message and be verified with public key.
        message_to_sign = "Sign this message with a private key to prove the sender!"
        signature = sign(message_to_sign, self.private)
        verification = verify(message_to_sign, signature, self.public)
        self.assertTrue(verification)

class TestBatch(TestCase):
    # A test for a checking if a key is in an allowable batch of keys.
    def setUp(self):
        self.pubs = [0 for _ in range(3)]
        self.priv = [0 for _ in range(3)]
        for i in range(3):
            self.pubs[i], self.priv[i] = new_rsa(1024)
        self.other_pub, self.other_priv = new_rsa(1024)
        self.msg = "Signature text"

    def test_key_not_in_bundle(self):
        # Test to make sure an key not in the batch is rejected.
        bad_signiture = sign(self.msg, self.other_priv)
        check = False
        for i in range(3):
            check = verify(self.msg, bad_signiture, self.pubs[i])
            if check == True:
                break
        self.assertFalse(check)

    def test_key_in_bundle(self):
        # Test to make sure a key that is in the batch is allowed.
        good_signiture = sign(self.msg, self.priv[1])
        check = False
        for i in range(3):
            check = verify(self.msg, good_signiture, self.pubs[i])
            if check == True:
                break
        self.assertTrue(check)

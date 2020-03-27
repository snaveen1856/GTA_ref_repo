"""
AESCipher Library to encrypt and decrypt passwords using AES Algorithm
"""
import base64
import hashlib
import os
try:
    from Crypto import Random
except ImportError:
    from crypto import Random
try:
    from Crypto.Cipher import AES
except ImportError:
    from crypto.Cipher import AES
from lib import logger
from os.path import expanduser
from lib.utilities import get_data_from_yaml


class AESCipher(object):
    """
    Encrypt and Decrypt Password using AESCipher.
    """

    def __init__(self):
        """
        Gets symmetric_key from global_conf.yaml file and encodes it with
        hashlib.sha256 module.
        """
        self.blocksize = 128
        #read the values from gloabl_conf.yaml and get the symmetric key.
        try:
            globfile = os.path.join(expanduser('~'), "global_conf.yaml")
            glob_data = get_data_from_yaml(globfile)
            symmetric_key = glob_data['symmetric_key']
        #if the file is not available or do not have permissions to read
        #or any problem in reading the file then raises Exception.
        except IOError as e:
            if e.errno == 13:
                logger.error("user do not have file permissions to "
                            "read the file", e.filename)
            elif e.errno == 2:
                logger.error("no such file or directory", e.filename)
            else:
                logger.error("some problem in opening file."
                            "please check it", e.filename)
        #Encodes the symmetric key with sha256.
        self.key = hashlib.sha256(symmetric_key.encode()).digest()

    def encrypt(self, raw):
        """
        Encrypts the value using passphrase.

        - **parameters**, **types**, **return** and **return types**::

            :param raw: value to be encrypted from the global_conf.yaml file
            :type raw: string
            :return: Returns encrypted value of raw value.
        """
        #padding the data to multiples block-size
        raw = self._pad(raw)
        #iniialization vector to create to be used with symmetric key. 
        init_vector = Random.new().read(AES.block_size)
        #Encrypts the data.
        cipher = AES.new(self.key, AES.MODE_CBC, init_vector)
        return base64.b64encode(init_vector + cipher.encrypt(raw.encode("utf8")))

    def decrypt(self, enc):
        """
        Decrypts the encrypted value using passphrase.

        - **parameters**, **types**, **return** and **return types**::

            :param enc: encrypted value from encrypt method.
            :type enc: string
            :return: Returns decrypted value of the encrypted value
        """
        #decode the encrypted data
        enc = base64.b64decode(enc)
        #iniialization vector to create to be used with symmetric key.
        init_vector = enc[:AES.block_size]
        #Decrypts the data.
        cipher = AES.new(self.key, AES.MODE_CBC, init_vector)
        return self._unpad(cipher.decrypt(enc[AES.block_size:])
                           ).decode('utf-8')

    def _pad(self, raw_pwd):
        """
        value from global_conf.yaml will be padded.

        - **parameters**, **types**, **return** and **return types**::

            :param raw_pwd: value from the global_conf.yaml to be padded
            :type raw_pad: string
            :return: Returns Padded value of given input 
        """
        #padding the data to multiples block-size
        padding = self.blocksize - len(raw_pwd) % self.blocksize
        return raw_pwd + padding * chr(padding)

    @staticmethod
    def _unpad(padded_pwd):
        """
        Unpads the padded value.

        - **parameters**, **types**, **return** and **return types**::

            :param raw_pwd:Padded value.
            :type padded_pwd: string
            :return: Returns unpadded value of the given padded string
        """
        #unpads the data.
        return padded_pwd[:-ord(padded_pwd[len(padded_pwd) - 1:])]

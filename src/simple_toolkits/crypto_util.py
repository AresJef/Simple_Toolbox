# /usr/bin/python
# -*- coding: UTF-8 -*-
import base64 as _base64

from cryptography.fernet import Fernet as _Fernet
from cryptography.hazmat.primitives import hashes as _hashes
from cryptography.hazmat.backends import default_backend as _default_backend
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC as _PBKDF2HMAC
from nacl.public import PrivateKey as _PrivateKey, PublicKey as _PublicKey, Box as _Box

__all__ = ["encrypt", "decrypt"]


def encrypt(msg: str, key: str, salt: str) -> str:
    """Encrypt a string with a key and salt.

    This function should only be used in pair with `decrypt()`.

    :param msg: The string to be encrypted.
    :param key: The key to encrypt the string.
    :param salt: The salt to encrypt the string.
    :raises `TypeError`: if `msg`, `key` or `salt` is not a string.
    :return: The encrypted string.
    """

    if not isinstance(key, str):
        raise TypeError(f"<crypto_util.encrypt> 'key' must be str, not {type(key)}")

    if not isinstance(salt, str):
        raise TypeError(f"<crypto_util.encrypt> 'salt' must be str, not {type(salt)}")

    if not isinstance(msg, str):
        raise TypeError(f"<crypto_util.encrypt> 'msg' must be str, not {type(key)}")

    __fernet = _Fernet(_base64.urlsafe_b64encode(_generate_key(key, salt)))
    __private = _PrivateKey(_generate_key(key, salt))
    __public = _PublicKey(_generate_key(salt, key))
    __box = _Box(__private, __public)
    return __fernet.encrypt(__box.encrypt(msg.encode())).decode()


def decrypt(msg: str, key: str, salt: str) -> str:
    """Decrypt a string with a key and salt.

    This function should only be used in pair with `encrypt()`.

    :param msg: The string to be decrypted.
    :param key: The key to decrypt the string.
    :param salt: The salt to decrypt the string.
    :raises `TypeError`: if `msg`, `key` or `salt` is not a string.
    :return: The decrypted string.
    """

    if not isinstance(key, str):
        raise TypeError(f"<crypto_util.decrypt> 'key' must be str, not {type(key)}")

    if not isinstance(salt, str):
        raise TypeError(f"<crypto_util.decrypt> 'salt' must be str, not {type(salt)}")

    if not isinstance(msg, str):
        raise TypeError(f"<crypto_util.decrypt> 'msg' must be str, not {type(key)}")

    __fernet = _Fernet(_base64.urlsafe_b64encode(_generate_key(key, salt)))
    __private = _PrivateKey(_generate_key(key, salt))
    __public = _PublicKey(_generate_key(salt, key))
    __box = _Box(__private, __public)
    return __box.decrypt(__fernet.decrypt(msg.encode())).decode()


def _generate_key(key: str, salt: str) -> bytes:
    return _PBKDF2HMAC(
        algorithm=_hashes.SHA256(),
        length=32,
        salt=salt.encode(),
        iterations=100,
        backend=_default_backend(),
    ).derive(key.encode())

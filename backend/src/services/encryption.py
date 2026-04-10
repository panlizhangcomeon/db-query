"""
Encryption Utilities

Handles password encryption/decryption for stored credentials.
"""
import base64
import hashlib
import os
from cryptography.fernet import Fernet


class Encryptor:
    """Handles encryption and decryption of sensitive data."""

    _fernet: Fernet | None = None

    @classmethod
    def initialize(cls, secret_key: str | None = None) -> None:
        """
        Initialize the encryptor with a secret key.

        Args:
            secret_key: Secret key for encryption. If None, uses a machine-specific key.
        """
        if secret_key is None:
            # Generate a machine-specific key based on home directory
            home = os.path.expanduser("~")
            key_source = f"{home}-db-query-tool"
            secret_key = hashlib.sha256(key_source.encode()).digest()

        key = base64.urlsafe_b64encode(secret_key[:32].ljust(32, b'0'))
        cls._fernet = Fernet(key)

    @classmethod
    def encrypt(cls, plaintext: str) -> str:
        """
        Encrypt a plaintext string.

        Args:
            plaintext: String to encrypt

        Returns:
            Encrypted string (base64 encoded)

        Raises:
            RuntimeError: If encryptor not initialized
        """
        if cls._fernet is None:
            cls.initialize()

        return cls._fernet.encrypt(plaintext.encode()).decode()

    @classmethod
    def decrypt(cls, ciphertext: str) -> str:
        """
        Decrypt an encrypted string.

        Args:
            ciphertext: Encrypted string (base64 encoded)

        Returns:
            Decrypted plaintext string

        Raises:
            RuntimeError: If encryptor not initialized
        """
        if cls._fernet is None:
            cls.initialize()

        return cls._fernet.decrypt(ciphertext.encode()).decode()

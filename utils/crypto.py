"""
Utilidades de criptografia para o sistema de chat
"""
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class ChatEncryption:
    """Classe para criptografia de mensagens de chat"""

    def __init__(self, password=None):
        """Inicializa o sistema de criptografia com uma chave"""
        if password is None:
            password = os.environ.get('CHAT_ENCRYPTION_KEY', 'vale_feira_default_key_2025').encode()

        # Gera uma chave determinística a partir da senha
        salt = b'vale_feira_salt_2025'
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        self.cipher = Fernet(key)

    def encrypt_message(self, message):
        """Criptografa uma mensagem"""
        if not message:
            return ""

        try:
            message_bytes = message.encode('utf-8')
            encrypted_bytes = self.cipher.encrypt(message_bytes)
            return base64.urlsafe_b64encode(encrypted_bytes).decode('utf-8')
        except Exception as e:
            print(f"Erro ao criptografar mensagem: {e}")
            return message

    def decrypt_message(self, encrypted_message):
        """Descriptografa uma mensagem"""
        if not encrypted_message:
            return ""

        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_message.encode('utf-8'))
            decrypted_bytes = self.cipher.decrypt(encrypted_bytes)
            return decrypted_bytes.decode('utf-8')
        except Exception as e:
            print(f"Erro ao descriptografar mensagem: {e}")
            return encrypted_message

# Instância global
chat_encryption = ChatEncryption()

def encrypt_chat_message(message):
    """Função auxiliar para criptografar mensagens"""
    return chat_encryption.encrypt_message(message)

def decrypt_chat_message(encrypted_message):
    """Função auxiliar para descriptografar mensagens"""
    return chat_encryption.decrypt_message(encrypted_message)
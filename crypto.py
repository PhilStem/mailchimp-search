from cryptography.fernet import Fernet

# Key generated like this: KEY = Fernet.generate_key()
KEY = b'PpLU-KnmDx6RNjARbH7V8Yiw4b4q6M4QKkfhvlYntJw='


def encrypt(key, token):
    f = Fernet(key)
    return f.encrypt(bytes(token.encode())).decode("utf-8")


def decrypt(key, token):
    f = Fernet(key)
    return f.decrypt(bytes(token.encode())).decode("utf-8")

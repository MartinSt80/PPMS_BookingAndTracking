


import pickle, socket, struct

from Crypto.Hash import SHA256

from base64 import b64encode
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

data = {'test': "secret"}

pickled_data = pickle.dumps(data, protocol=2)
key = '0123456789abcdef'

AES_key = SHA256.new()
AES_key.update(key.encode())
AES_key = AES_key.digest()
print('AES SHA256: ' + b64encode(AES_key).decode('utf-8'))
iv = get_random_bytes(16)
cipher = AES.new(AES_key, AES.MODE_CFB, iv)
ct_bytes = cipher.encrypt(pickled_data)

ct = b64encode(ct_bytes).decode('utf-8')
iv_string = b64encode(iv).decode('utf-8')

print('iv: ' + iv_string)
print('ct: ' + ct)
cipher_msg = iv + ct_bytes
packed_dict = struct.pack('>I', len(cipher_msg)) + cipher_msg
proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
proxy_socket.connect(('127.0.0.1', 50000))

proxy_socket.sendall(packed_dict)

import bcrypt
hashed = bcrypt.hashpw('testpass'.encode(), bcrypt.gensalt(12)).decode()
print(hashed)
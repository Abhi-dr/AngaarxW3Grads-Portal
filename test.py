import secrets

key = ''.join(secrets.choice(
    'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)') for i in range(100)
)
print(key)

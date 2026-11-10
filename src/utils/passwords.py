from pwdlib.hashers.argon2 import Argon2Hasher

_hasher = Argon2Hasher()

def hash_password(user_password: str) -> str:
  """
  Hashes the user password using Argon2.
  """
  return _hasher.hash(user_password)


def verify_password(user_password: str, hash: str) -> tuple[bool, str | None]:
  """
  Compare the user password hash. Optionally return the rehashed password when the Argon parameters has been modified.
  """
  valid = _hasher.verify(user_password, hash)
  if not valid:
    return False, None
  
  return valid, _hasher.hash(user_password) if _hasher.check_needs_rehash(hash=hash) else None

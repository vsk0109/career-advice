"""
Run this ONCE to generate hashed passwords for auth_config.yaml.

Usage:
    python3 generate_hashes.py

Edit the `plain_passwords` list below with real passwords for your team,
run the script, then copy the printed hashes into auth_config.yaml
(one hash per user, in the same order as the usernames list).

NEVER commit plaintext passwords to git -- only the hashed output goes
into auth_config.yaml, and even that file should ideally not be committed
to a public repo (add it to .gitignore if your repo is public).

Note: streamlit-authenticator changed its Hasher API in newer versions.
This script tries the new API first (Hasher().hash(password), one at a
time) and falls back to the old API (Hasher(list).generate()) if you're
on an older version -- so it should work either way.
"""

import streamlit_authenticator as stauth

# Add one password per teammate who should be able to log in.
plain_passwords = [
    "vaishnavi123",
    "student123",   # generic demo login for expo visitors, e.g. username "guest"
]

try:
    # New API (streamlit-authenticator >= 0.4.0)
    hasher = stauth.Hasher()
    hashed_passwords = [hasher.hash(pw) for pw in plain_passwords]
except TypeError:
    # Old API (streamlit-authenticator < 0.4.0)
    hashed_passwords = stauth.Hasher(plain_passwords).generate()

for plain, hashed in zip(plain_passwords, hashed_passwords):
    print(f"{plain}  ->  {hashed}")
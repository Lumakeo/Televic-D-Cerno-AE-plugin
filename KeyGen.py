#!/usr/bin/env python3
"""
KeyGen.py — Generatore di chiavi di licenza per Confero Agenda Manager
Uso: python KeyGen.py <hardware_id>
Esempio: python KeyGen.py 3-86AC24DA6D61EEC8D22C9BFA99A9BECD
"""

import sys

SECRET = "CONFERO_PRASE_MIDWICH_2026"
CHARS  = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
MOD    = 1_000_000_000


def gen_key(hardware_id: str) -> str:
    s = hardware_id + SECRET
    h = 0
    for c in s:
        h = (h * 31 + ord(c)) % MOD
    h2 = 0
    for i, c in enumerate(reversed(s)):
        h2 = (h2 * 37 + ord(c) * ((i % 7) + 1)) % MOD

    def enc(n: int, length: int) -> str:
        r = ""
        for _ in range(length):
            r += CHARS[n % 32]
            n //= 32
        return r

    combined = (h + h2) % MOD
    return f"{enc(h,4)}-{enc(h2,4)}-{enc(combined,4)}"


def main():
    if len(sys.argv) < 2:
        print("Uso: python KeyGen.py <hardware_id>")
        print("Il hardware_id si trova nel tab Info del plugin (campo Core Hardware ID)")
        print("oppure tramite GET https://<core-ip>/api/v0/cores → campo hardwareId")
        sys.exit(1)

    hwid = sys.argv[1].strip()
    key  = gen_key(hwid)
    print(f"Hardware ID : {hwid}")
    print(f"Chiave      : {key}")
    print()
    print("Inserire la chiave nella proprietà 'LicenseKey' del plugin in Q-SYS Designer.")


if __name__ == "__main__":
    main()

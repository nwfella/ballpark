#!/usr/bin/env python3
"""Audit the bank in index.html for weak reveal notes.

A good note gives real context. A bare number ("42.") is not a note - and
the ?selftest=1 gate rejects it (n.length > 3).
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.join(os.path.dirname(HERE), "index.html")
ENTRY = re.compile(
    r'\{c:"(.*?)",\s*q:"(.*?)",\s*u:"(.*?)",\s*a:(-?[0-9.]+),\s*'
    r'min:(-?[0-9.]+),\s*max:(-?[0-9.]+),\s*n:"(.*?)"\}'
)

with open(HTML, encoding="utf-8") as fh:
    src = fh.read()
block = src[src.index("/* BANK:START */"):src.index("/* BANK:END */")]

weak = []
for m in ENTRY.finditer(block):
    c, q, u, a, mn, mx, n = m.groups()
    if len(n) <= 3 or re.fullmatch(r"[\d.,%°\s]+", n):
        weak.append((q, a, n))

print("weak notes: %d\n" % len(weak))
for q, a, n in weak:
    print('    (%s, %r),' % (q, n))

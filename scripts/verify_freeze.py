#!/usr/bin/env python3
"""Prove the frozen schedule does its job.

Two claims, both checked here:
  1. A frozen day reproduces EXACTLY what the bank produced at freeze time.
  2. Without the schedule, that same day would have changed the moment the
     bank grew. (This is the regression the schedule exists to prevent.)
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_bank import pick_day, qid, ENTRY, SCHED_START, SCHED_END  # noqa: E402

HTML = os.path.join(os.path.dirname(HERE), "index.html")
src = open(HTML, encoding="utf-8").read()

bank = [m.group(2) for m in ENTRY.finditer(src[src.index("/* BANK:START */"):src.index("/* BANK:END */")])]
sched = re.findall(r'"([0-9a-z]{6})"',
                   src[src.index(SCHED_START) + len(SCHED_START):src.index(SCHED_END)])

n = len(bank)
grown = n + 25  # pretend a later batch adds 25 questions


def ids(bank_list, day):
    return [qid(bank_list[i]) for i in pick_day(len(bank_list), day)]


grown_bank = bank + ["Placeholder question number %d?" % k for k in range(25)]


print("bank = %d questions | schedule = %d days | simulating growth to %d\n"
      % (n, len(sched) // 5, grown))
print("day | frozen day (stored)                  | fallback @%d | fallback @%d | result" % (n, grown))

fails = 0
would_have_changed = 0
DAYS = (0, 1, 15, 60, 120, 180)
for day in DAYS:
    frozen = sched[day * 5:(day + 1) * 5]
    old, new = ids(bank, day), ids(grown_bank, day)
    preserved = frozen == old
    changed = old != new
    would_have_changed += changed
    if not preserved:
        fails += 1
    print("%3d | %s | %s | %s | %s%s"
          % (day, " ".join(frozen), " ".join(old), " ".join(new),
             "OK" if preserved else "FAIL",
             "  <- would have drifted" if changed else "  (stable anyway)"))

print()
print("1. frozen days match the pre-growth bank exactly : %s" % ("YES" if fails == 0 else "NO (%d)" % fails))
print("2. of %d sampled days, %d would have changed without freezing" % (len(DAYS), would_have_changed))
sys.exit(1 if fails else 0)

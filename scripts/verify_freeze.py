#!/usr/bin/env python3
"""Prove the frozen schedule does its job.

The property that matters is *stability across bank growth*, so this compares
the working tree against the previous commit rather than against a synthetic
bank:

  1. every day that existed before the last change is byte-identical now
     (no frozen day moved, even though the bank grew)
  2. the schedule may only APPEND - its day count never shrinks
  3. day 0's five questions did not change
  4. illustration: the unfrozen fallback WOULD have changed for that same day,
     which is exactly the drift the schedule exists to prevent

Run it any time; meaningful whenever there is a previous commit to compare to.
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from build_bank import pick_day, qid, ENTRY, SCHED_START, SCHED_END  # noqa: E402


def parse(src):
    blk = src[src.index("/* BANK:START */"):src.index("/* BANK:END */")]
    bank = [m.group(2) for m in ENTRY.finditer(blk)]
    sched = re.findall(r'"([0-9a-z]{6})"',
                       src[src.index(SCHED_START) + len(SCHED_START):src.index(SCHED_END)])
    return bank, sched


def from_git(rev):
    out = subprocess.run(["git", "show", "%s:index.html" % rev], cwd=REPO,
                         capture_output=True, text=True)
    return out.stdout if out.returncode == 0 else None


cur = open(os.path.join(REPO, "index.html"), encoding="utf-8").read()
cur_bank, cur_sched = parse(cur)

# Walk back to the most recent commit whose bank size DIFFERS - i.e. the state
# just before the last growth. Comparing against HEAD itself is vacuous when
# the tree is clean (HEAD is already the post-growth state).
old_bank = old_sched = None
for k in range(1, 11):
    prev = from_git("HEAD~%d" % k)
    if prev is None:
        break
    b, s = parse(prev)
    if len(b) != len(cur_bank):
        old_bank, old_sched = b, s
        break

if old_bank is None:
    print("no earlier commit with a different bank size - nothing to compare")
    print("bank = %d questions, schedule = %d days" % (len(cur_bank), len(cur_sched) // 5))
    sys.exit(0)

fails = []
days_cmp = min(len(old_sched), len(cur_sched)) // 5
moved = [d for d in range(days_cmp)
         if old_sched[d * 5:d * 5 + 5] != cur_sched[d * 5:d * 5 + 5]]

if moved:
    fails.append("%d frozen day(s) moved, e.g. day index %s" % (len(moved), moved[:5]))
if len(cur_sched) < len(old_sched):
    fails.append("schedule shrank (%d -> %d ids)" % (len(old_sched), len(cur_sched)))
if len(cur_sched) >= 5 and len(old_sched) >= 5 and cur_sched[:5] != old_sched[:5]:
    fails.append("day 0 changed")

print("bank          : %d -> %d questions" % (len(old_bank), len(cur_bank)))
print("schedule      : %d -> %d days" % (len(old_sched) // 5, len(cur_sched) // 5))
print("frozen prefix : %d days compared, %d moved" % (days_cmp, len(moved)))

if old_bank and cur_bank:
    fb_old = [qid(old_bank[i]) for i in pick_day(len(old_bank), 0)]
    fb_new = [qid(cur_bank[i]) for i in pick_day(len(cur_bank), 0)]
    print()
    print("day 0 frozen     : %s" % " ".join(cur_sched[:5]))
    print("day 0 @%-3d bank : %s" % (len(old_bank), " ".join(fb_old)))
    print("day 0 @%-3d bank : %s" % (len(cur_bank), " ".join(fb_new)))
    print("without the schedule, day 0 would have drifted: %s"
          % ("YES" if fb_old != fb_new else "no"))

print()
if fails:
    print("FAIL: " + "; ".join(fails))
    sys.exit(1)
print("PASS: no frozen day moved across the bank growth")

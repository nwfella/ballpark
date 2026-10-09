#!/usr/bin/env python3
"""BALLPARK nightly top-up (Hermes cron, no_agent=true).

Pipeline
    1. refuse to run on a dirty working tree (never commit unrelated work)
    2. read the bank from index.html
    3. take up to BATCH unbanked candidates from scripts/pool.py
    4. VERIFY each one structurally - the same rules ?selftest=1 enforces.
       Failures are QUARANTINED: logged, never published.
    5. freeze the schedule and merge the verified batch (scripts/build_bank.py)
    6. run the in-page ?selftest=1 gate in headless Chrome
    7. commit + push ONLY if the gate passed; revert the file if it did not

Deliberately NOT generative
    Unattended LLM fact generation is the failure mode this project refuses.
    A daily game that publishes a wrong "true answer" destroys trust in one
    day, and no cheap automated check reliably catches a confidently-wrong
    number. Every question here comes from the curated, human-reviewed pool.
    The job's value is drip + freeze + verify, not invention.

Output contract
    stdout IS the delivered message. Nothing to add -> no output (silent).
    A failure exits non-zero, which raises an alert.
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import build_bank  # noqa: E402
from pool import POOL  # noqa: E402

BATCH = 5                     # questions to drip per run
DRY = "--dry-run" in sys.argv  # verify + report only, never writes
CHROME = r"C:/Program Files/Google/Chrome/Application/chrome.exe"
STATE = os.path.join(os.path.expanduser("~"), "AppData", "Local", "hermes",
                     "cache", "ballpark_nightly_state.json")
GITENV = dict(os.environ, GIT_TERMINAL_PROMPT="0")


# ------------------------------------------------------------------ helpers
def git(*args, check=True):
    return subprocess.run(["git"] + list(args), cwd=REPO, env=GITENV,
                          capture_output=True, text=True, check=check)


def read_bank():
    src = open(os.path.join(REPO, "index.html"), encoding="utf-8").read()
    blk = src[src.index("/* BANK:START */"):src.index("/* BANK:END */")]
    return [m.group(2) for m in build_bank.ENTRY.finditer(blk)]


def verify(cand, bank_norms):
    """Structural rules only. Mirrors the in-page gate so nothing ships that
    the gate would reject."""
    c, q, u, a, mn, mx, n = cand
    if not isinstance(a, int) or isinstance(a, bool):
        return "answer is not an integer"
    if not (mn < mx):
        return "range is invalid"
    if not (mn <= a <= mx):
        return "answer outside its range"
    if a == mn or a == mx:
        return "answer sits on a slider edge"
    if len(q) <= 6:
        return "question is too short"
    if len(str(n)) <= 3:
        return "note is too short"
    if build_bank.norm(q) in bank_norms:
        return "already in the bank"
    return None


def gate():
    """Runs the real in-page self-test headless. Returns (ok, detail)."""
    if not os.path.exists(CHROME):
        return False, "chrome not found"
    url = "file:///" + os.path.join(REPO, "index.html").replace("\\", "/") + "?selftest=1"
    with tempfile.TemporaryDirectory() as td:
        try:
            out = subprocess.run(
                [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
                 "--user-data-dir=" + os.path.join(td, "prof"),
                 "--virtual-time-budget=9000", "--dump-dom", url],
                capture_output=True, text=True, timeout=180).stdout
        except subprocess.TimeoutExpired:
            return False, "gate timed out"
    m = re.search(r"SELFTEST (PASS|FAIL) \| checks=(\d+) fails=(\d+)", out)
    if not m:
        return False, "gate produced no verdict (script error?)"
    return m.group(1) == "PASS", "checks=%s fails=%s" % (m.group(2), m.group(3))


def verify_live(expected_bank):
    """Bounded check that the deployed page really carries the new bank."""
    for _ in range(6):
        time.sleep(15)
        try:
            html = subprocess.run(
                ["curl", "-s", "https://nwfella.github.io/ballpark/?v=%d" % int(time.time())],
                capture_output=True, text=True, timeout=60).stdout
        except Exception:
            continue
        if html.count("\n  {c:") >= expected_bank:
            return True
    return False


# --------------------------------------------------------------------- main
def main():
    dirty = git("status", "--porcelain").stdout.strip()
    if dirty and not DRY:
        print("BALLPARK top-up REFUSED: working tree is dirty:\n" + dirty)
        return 1
    if not os.path.exists(CHROME):
        print("BALLPARK top-up: chrome not found at %s" % CHROME)
        return 1

    bank = read_bank()
    bank_norms = {build_bank.norm(q) for q in bank}

    seen = set(bank_norms)
    publishable, quarantined = [], []
    for cand in POOL:
        key = build_bank.norm(cand[1])
        if key in seen:
            continue                      # already banked
        reason = verify(cand, bank_norms)
        if reason:
            quarantined.append("%s (%s)" % (cand[1], reason))
            continue
        seen.add(key)
        publishable.append(cand)

    remaining = len(publishable)
    queue = publishable[:BATCH]

    if DRY:
        print("DRY RUN (nothing written)")
        if dirty:
            print("  note: working tree is dirty; a real run would refuse")
        print("  bank now           : %d questions" % len(bank))
        print("  pool publishable   : %d" % remaining)
        print("  quarantined        : %d" % len(quarantined))
        for c in queue:
            print("  would add          : [%s] %s = %s" % (c[0], c[1], c[3]))
        for z in quarantined:
            print("  QUARANTINED        : " + z)
        return 0

    if not queue:
        # silent unless the pool has just run dry (one-time notice)
        state = {}
        if os.path.exists(STATE):
            try:
                state = json.load(open(STATE, encoding="utf-8"))
            except Exception:
                state = {}
        if remaining == 0 and not state.get("exhausted_warned"):
            state["exhausted_warned"] = True
            os.makedirs(os.path.dirname(STATE), exist_ok=True)
            json.dump(state, open(STATE, "w", encoding="utf-8"))
            print("BALLPARK: pool exhausted - nothing left to drip. "
                  "Add a batch to scripts/pool.py to resume.")
        return 0

    # 1. merge (build_bank freezes the schedule BEFORE the bank changes)
    payload = [{"c": c, "q": q, "u": u, "a": a, "min": mn, "max": mx, "n": n}
               for (c, q, u, a, mn, mx, n) in queue]
    with tempfile.TemporaryDirectory() as td:
        extra = os.path.join(td, "drip.json")
        json.dump(payload, open(extra, "w", encoding="utf-8"))
        quiet = subprocess.run(
            [sys.executable, os.path.join(HERE, "build_bank.py"), "--extra", extra],
            cwd=REPO, capture_output=True, text=True)
        if quiet.returncode != 0:
            git("checkout", "--", "index.html", check=False)
            print("BALLPARK top-up FAILED: build_bank exited %d\n%s"
                  % (quiet.returncode, quiet.stdout[-800:] + quiet.stderr[-800:]))
            return 1

    # verify the artifact actually grew - the file is the source of truth,
    # so re-read it rather than trusting the subprocess exit code
    after = read_bank()
    if len(after) != len(bank) + len(queue):
        git("checkout", "--", "index.html", check=False)
        print("BALLPARK top-up ABORTED: expected %d questions, file has %d - reverted."
              % (len(bank) + len(queue), len(after)))
        return 1
    total = len(after)

    # 2. gate - the real in-page self-test
    ok, detail = gate()
    if not ok:
        git("checkout", "--", "index.html", check=False)
        print("BALLPARK top-up ABORTED: gate failed (%s) - index.html reverted." % detail)
        return 1

    # 3. commit + push
    git("add", "index.html")
    git("commit", "-q", "-m",
        "data: nightly question top-up (+%d, %d total)" % (len(queue), total))
    push = git("push", "-q", "origin", "main", check=False)
    if push.returncode != 0:
        print("BALLPARK top-up: commit made but PUSH FAILED:\n" + push.stderr[-500:])
        return 1

    head = git("rev-parse", "HEAD").stdout.strip()[:8]
    remote = git("rev-parse", "origin/main").stdout.strip()[:8]
    if head != remote:
        print("BALLPARK top-up: pushed but origin is at %s, expected %s" % (remote, head))
        return 1

    live = verify_live(total)
    print("BALLPARK top-up: +%d questions -> %d total (%d-day rotation)"
          % (len(queue), total, total // 5))
    print("  gate : SELFTEST PASS (%s)" % detail)
    print("  push : %s (origin verified)" % head)
    print("  live : %s" % ("verified serving the new bank" if live
                           else "pushed; live check still pending"))
    if quarantined:
        print("  quarantined: " + "; ".join(quarantined))
    print("  pool remaining: %d" % max(0, remaining - len(queue)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

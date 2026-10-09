#!/usr/bin/env python3
"""Merge scripts/questions_new.py into index.html's question bank.

Idempotent and marker-based. It only ever rewrites the text between
/* BANK:START */ and /* BANK:END */, so the rest of the game file is
untouched. It does NOT publish anything on its own - the ?selftest=1 gate
must still pass afterwards (structural checks, integer answers, and a
duplicate guard).

Usage:  python scripts/build_bank.py
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
HTML = os.path.join(ROOT, "index.html")

sys.path.insert(0, HERE)
from questions_new import NEW  # noqa: E402

ENTRY = re.compile(
    r'\{c:"(.*?)",\s*q:"(.*?)",\s*u:"(.*?)",\s*a:(-?[0-9.]+),\s*'
    r'min:(-?[0-9.]+),\s*max:(-?[0-9.]+),\s*n:"(.*?)"\}'
)

START = "/* BANK:START */"
END = "/* BANK:END */"

# --- Corrections applied on EVERY run (so build_bank.py is the single
# --- source of truth for the batch, and re-running is self-healing). ---

# Excluded: the true answer sits on a slider edge, so it is findable by
# simply slamming the slider to one end. Bad puzzle, not a bad fact.
DROP = {
    "How many bones does a shark have?",
    "How many moons does Venus have?",
    # Contested answer (11 crossed on land vs 13 including territorial
    # waters). A daily game must not display a "true" answer that is
    # genuinely argued about.
    "How many countries does the equator pass through?",
}

# Weak notes (bare numbers, e.g. "42.") replaced with real context.
NOTE_FIX = {
    "How many teeth does an adult cat have?": "30 adult teeth, fewer than a dog's 42.",
    "How many teeth does an adult dog have?": "42 adult teeth, more than a human's 32.",
    "How many cards are in a standard deck, without jokers?": "52, in four suits of 13.",
    "How many dominoes are in a double-six set?": "28, from 0-0 up to 6-6.",
    "How many letters are in pneumonoultramicroscopicsilicovolcanoconiosis?": "45 letters; coined to be long.",
    "How many letters are in supercalifragilisticexpialidocious?": "34 letters.",
    "How many letters are in the English alphabet?": "26, from A to Z.",
    "How many letters are in the Greek alphabet?": "24, from alpha to omega.",
    "How many letters are in the word antidisestablishmentarianism?": "28 letters.",
    "How many strings does a concert harp have?": "47, on a standard concert grand.",
    "How many tiles are in a Scrabble set?": "100 tiles in total.",
    "How many millilitres are in a standard wine bottle?": "750 ml, the standard bottle.",
    "How many ounces are in a US soda can?": "12 US fluid ounces.",
    "How many countries does the equator pass through?": "13 countries.",
    "How many member states are in the African Union?": "55 member states.",
    "How many amendments does the US Constitution have?": "27, the last ratified in 1992.",
    "How many people signed the US Declaration of Independence?": "56 delegates, in 1776.",
    "How many years did Queen Elizabeth II reign?": "70 years, from 1952 to 2022.",
    "In what year did World War I begin?": "1914, after the Sarajevo assassination.",
    "In what year did people first land on the Moon?": "1969, on Apollo 11.",
    "In what year did the Berlin Wall fall?": "1989, after 28 years standing.",
    "In what year did the Wright brothers first fly?": "1903, at Kitty Hawk.",
    "In what year was the Chernobyl disaster?": "1986, in Soviet Ukraine.",
    "In what year was the first iPhone released?": "2007, by Apple.",
    "How many bones are in the human skull?": "22, not counting the ear bones.",
    "How many pairs of chromosomes do humans have?": "23 pairs, 46 in total.",
    "How many floors does the Empire State Building have?": "102 storeys.",
    "How many rooms are in the White House?": "132 rooms.",
    "How many steps are there to the top of the Eiffel Tower?": "1,665 steps to the summit.",
    "How many steps lead to the crown of the Statue of Liberty?": "354 steps to the crown.",
    "How many bytes are in a kibibyte?": "1,024 bytes.",
    "How many centimetres are in a metre?": "100 centimetres.",
    "How many degrees are in a full circle?": "360 degrees.",
    "How many degrees are in a right angle?": "90 degrees.",
    "How many elements are in the periodic table?": "118 confirmed elements.",
    "How many feet are in a mile?": "5,280 feet.",
    "How many grams are in a kilogram?": "1,000 grams.",
    "How many kilograms are in a metric ton?": "1,000 kilograms.",
    "How many metres are in a kilometre?": "1,000 metres.",
    "How many millimetres are in a metre?": "1,000 millimetres.",
    "How many pounds are in a US ton?": "2,000 pounds.",
    "What do the interior angles of a triangle add up to, in degrees?": "180 degrees in flat space.",
    "What is the atomic number of gold?": "79, so 79 protons per atom.",
    "What is the boiling point of water at sea level, in Celsius?": "100 C at standard pressure.",
    "What is the freezing point of water, in Fahrenheit?": "32 F, which is 0 C.",
    "How many constellations are officially recognised?": "88, defined by the IAU.",
    "How many balls are used in a snooker frame?": "22: 15 reds, six colours, one cue ball.",
    "How many metres long is a marathon?": "42,195 m, or 26.2 miles.",
    "How many days are in a leap year?": "366, one more than usual.",
    "How many days are in a standard year?": "365 days.",
    "How many hours are in a week?": "168, or 24 x 7.",
    "How many minutes are in a day?": "1,440, or 24 x 60.",
    "How many minutes are in a non-leap year?": "525,600, as the song says.",
    "How many seconds are in a day?": "86,400, or 24 x 3,600.",
    "How many seconds are in a week?": "604,800, or 7 x 86,400.",
    "How many seconds are in an hour?": "3,600, or 60 x 60.",
    "How many weeks are in a year?": "52, plus a day or two.",
    "How many years are in a millennium?": "1,000 years.",
    "How many public levels does the Eiffel Tower have?": "Three levels; the top is reached by lift.",
    "How many species of penguin are there?": "18 recognised by the IOU and IUCN.",
}

# Category tidy-up: the original bank and this batch used different labels for
# the same thing ("Sports"/"Sport", "Astronomy"/"Space"), plus a broad "Nature"
# catch-all. Normalise so the in-game tag is consistent.
CAT_RENAME = {"Sports": "Sport", "Astronomy": "Space"}
CAT_FIX = {
    "How many chambers does the human heart have?": "Human body",
    "How many teeth does a typical adult human have?": "Human body",
    "How many bones are in one human foot?": "Human body",
    "How many hearts does an octopus have?": "Animals",
}


def norm(text):
    return re.sub(r"[^a-z0-9]", "", text.lower())


def num(x):
    f = float(x)
    return str(int(f)) if f == int(f) else repr(f)


def main():
    with open(HTML, encoding="utf-8") as fh:
        src = fh.read()

    inserted = False
    if START not in src:
        k = src.index("var QUESTIONS = [")
        open_end = src.index("[", k) + 1
        close = src.index("\n];", open_end)
        src = (src[:open_end] + "\n  " + START + src[open_end:close]
               + "\n  " + END + src[close:])
        inserted = True

    start = src.index(START) + len(START)
    end = src.index(END)
    block = src[start:end]

    existing = []
    for m in ENTRY.finditer(block):
        c, q, u, a, mn, mx, n = m.groups()
        existing.append({"c": c, "q": q, "u": u, "a": float(a),
                         "min": float(mn), "max": float(mx), "n": n})

    seen = {norm(e["q"]) for e in existing}
    merged = list(existing)
    skipped = []
    for c, q, u, a, mn, mx, n in NEW:
        key = norm(q)
        if key in seen:
            skipped.append(q)
            continue
        seen.add(key)
        merged.append({"c": c, "q": q, "u": u, "a": a,
                       "min": mn, "max": mx, "n": n})

    # apply the corrections table (self-healing on every run)
    merged = [e for e in merged if e["q"] not in DROP]
    fixed = 0
    for e in merged:
        want = NOTE_FIX.get(e["q"])
        if want and e["n"] != want:
            e["n"] = want
            fixed += 1
        if e["c"] in CAT_RENAME:
            e["c"] = CAT_RENAME[e["c"]]
        if e["q"] in CAT_FIX:
            e["c"] = CAT_FIX[e["q"]]

    merged.sort(key=lambda e: (e["c"], e["q"]))

    lines = [
        '  {c:"%s", q:"%s", u:"%s", a:%s, min:%s, max:%s, n:"%s"},'
        % (e["c"], e["q"], e["u"], num(e["a"]), num(e["min"]), num(e["max"]), e["n"])
        for e in merged
    ]
    lines[-1] = lines[-1].rstrip(",")

    out = src[:start] + "\n" + "\n".join(lines) + "\n  " + src[end:]
    with open(HTML, "w", encoding="utf-8") as fh:
        fh.write(out)

    print("markers inserted this run : %s" % inserted)
    print("existing in file          : %d" % len(existing))
    print("candidates in batch       : %d" % len(NEW))
    print("added                     : %d" % (len(merged) - len(existing)))
    print("duplicates skipped        : %d" % len(skipped))
    print("TOTAL bank                : %d  ->  %d-day rotation"
          % (len(merged), len(merged) // 5))
    if skipped:
        print("skipped:", "; ".join(skipped[:8]))


if __name__ == "__main__":
    main()

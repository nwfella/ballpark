#!/usr/bin/env python3
"""BALLPARK candidate pool - the only source the nightly job publishes from.

WHY A POOL AND NOT A GENERATOR
    Unattended LLM fact generation is the failure mode this project refuses:
    a daily game that publishes a wrong "true answer" destroys trust in one
    day, and no automated check reliably catches a confidently-wrong number.
    So the nightly job never invents a fact. It drips entries from this
    curated, human-reviewed pool into the bank, freezes the schedule, runs
    the gate, and commits. Its value is drip + freeze + verify, not invention.

RULES (mirrors what ?selftest=1 enforces)
    * integer answers only (the slider steps by whole numbers)
    * the answer must not sit on the slider min or max
    * a real reveal note, never just the bare number
    * stable facts only - no records, rankings, populations or prices that
      expire and would silently become wrong answers

Tuple layout: (category, question, unit, answer, min, max, note)
"""
POOL = [
    # ---------------- Music, film & TV ----------------
    ("Everyday", "How many strings does a mandolin have?", "strings", 8, 0, 20, "Eight, in four pairs."),
    ("Everyday", "How many frames per second does standard film run at?", "fps", 24, 0, 60, "24, the classic film rate."),
    ("Everyday", "How many episodes are in the Star Wars Skywalker saga?", "episodes", 9, 0, 20, "Nine episodic films."),
    ("Everyday", "How many books are in the main Harry Potter series?", "books", 7, 0, 20, "Seven."),
    ("Everyday", "How many books are in the Chronicles of Narnia series?", "books", 7, 0, 20, "Seven."),
    ("Everyday", "How many volumes is The Lord of the Rings published in?", "volumes", 3, 0, 12, "Three volumes, six books."),
    ("Everyday", "How many dwarfs are there in Snow White?", "dwarfs", 7, 0, 20, "Seven."),

    # ---------------- Language & computing ----------------
    ("Science", "How many letters are in the NATO phonetic alphabet?", "letters", 26, 0, 60, "One per letter of the alphabet."),
    ("Science", "How many bits are in a nibble?", "bits", 4, 0, 12, "Half a byte."),
    ("Science", "What base is the hexadecimal system?", "base", 16, 0, 40, "Sixteen, hence hex."),
    ("Science", "How many bits are in an IPv4 address?", "bits", 32, 0, 100, "32, in four octets."),
    ("Science", "How many bits are in an IPv6 address?", "bits", 128, 0, 300, "128."),
    ("Science", "How many TCP ports are there?", "ports", 65536, 0, 200000, "0 to 65,535."),
    ("Science", "How many characters are in the standard ASCII set?", "characters", 128, 0, 300, "128."),
    ("Science", "How many gigabytes are in a terabyte?", "GB", 1024, 0, 3000, "1,024 on the binary convention."),

    # ---------------- Geography & subdivisions ----------------
    ("Geography", "How many US states have four-letter names?", "states", 3, 0, 20, "Iowa, Ohio and Utah."),
    ("Geography", "How many US states border Canada?", "states", 13, 0, 30, "Thirteen."),
    ("Geography", "How many US states border Mexico?", "states", 4, 0, 15, "California, Arizona, New Mexico and Texas."),
    ("Geography", "How many countries does the Amazon flow through?", "countries", 3, 0, 12, "Peru, Colombia and Brazil."),
    ("Geography", "How many time zones does Canada span?", "time zones", 6, 0, 15, "Six."),
    ("Geography", "How many states does Brazil have?", "states", 26, 0, 60, "26, plus the Federal District."),
    ("Geography", "How many countries make up the United Kingdom?", "countries", 4, 0, 12, "England, Scotland, Wales and Northern Ireland."),
    ("Geography", "How many boroughs does London have?", "boroughs", 32, 0, 80, "32, plus the City of London."),
    ("Geography", "How many emirates make up the UAE?", "emirates", 7, 0, 20, "Seven."),
    ("Geography", "How many cantons does Switzerland have?", "cantons", 26, 0, 60, "26 cantons."),
    ("Geography", "How many states does Germany have?", "states", 16, 0, 40, "Sixteen."),
    ("Geography", "How many states does India have?", "states", 28, 0, 60, "28 states, plus 8 union territories."),
    ("Geography", "How many prefectures does Japan have?", "prefectures", 47, 0, 100, "47 prefectures."),
    ("Geography", "How many provinces does South Africa have?", "provinces", 9, 0, 30, "Nine."),
    ("Geography", "How many counties are on the island of Ireland?", "counties", 32, 0, 80, "32, across both jurisdictions."),
    ("Geography", "How many states does Austria have?", "states", 9, 0, 30, "Nine."),
    ("Geography", "How many regions does France have?", "regions", 18, 0, 40, "13 metropolitan plus 5 overseas."),

    # ---------------- History ----------------
    ("History", "In what year did the Titanic sink?", "year", 1912, 1800, 2000, "1912."),
    ("History", "In what year was the US Declaration of Independence signed?", "year", 1776, 1600, 1900, "1776."),
    ("History", "In what year did the French Revolution begin?", "year", 1789, 1600, 1900, "1789."),
    ("History", "In what year were the first modern Olympic Games held?", "year", 1896, 1800, 2000, "1896, in Athens."),
    ("History", "In what year was the Berlin Wall built?", "year", 1961, 1800, 2000, "1961."),
    ("History", "In what year did the Soviet Union dissolve?", "year", 1991, 1800, 2000, "1991."),
    ("History", "In what year did the US Civil War end?", "year", 1865, 1700, 1950, "1865."),
    ("History", "In what year was the Magna Carta sealed?", "year", 1215, 1000, 1500, "1215."),
    ("History", "How many years did the US Civil War last?", "years", 4, 0, 15, "1861 to 1865."),
    ("History", "In what year was the Battle of Hastings?", "year", 1066, 900, 1400, "1066."),
    ("History", "In what year did Columbus reach the Americas?", "year", 1492, 1300, 1700, "1492."),
    ("History", "In what year did the Eiffel Tower open?", "year", 1889, 1700, 1990, "1889."),
    ("History", "In what year was the Statue of Liberty dedicated?", "year", 1886, 1700, 1990, "1886."),
    ("History", "In what year was the Great Fire of London?", "year", 1666, 1500, 1800, "1666."),
    ("History", "In what year was the Battle of Waterloo?", "year", 1815, 1700, 1900, "1815."),
    ("History", "In what year was the Wall Street Crash?", "year", 1929, 1800, 2000, "1929."),

    # ---------------- Science ----------------
    ("Science", "What is the speed of sound in air, in metres per second?", "m/s", 343, 0, 1000, "About 343 m/s at 20 C."),
    ("Science", "What is the freezing point of water on the kelvin scale?", "kelvin", 273, 0, 600, "273.15 K."),
    ("Science", "What is the boiling point of water on the kelvin scale?", "kelvin", 373, 0, 600, "373.15 K."),
    ("Science", "How many sides does a nonagon have?", "sides", 9, 0, 20, "Nine."),
    ("Science", "How many sides does an octagon have?", "sides", 8, 0, 20, "Eight."),
    ("Science", "How many sides does a heptagon have?", "sides", 7, 0, 20, "Seven."),
    ("Science", "How many faces does a tetrahedron have?", "faces", 4, 0, 12, "Four triangles."),
    ("Science", "How many edges does a tetrahedron have?", "edges", 6, 0, 20, "Six."),
    ("Science", "How many faces does an octahedron have?", "faces", 8, 0, 20, "Eight."),
    ("Science", "How many vertices does an octahedron have?", "vertices", 6, 0, 20, "Six."),
    ("Science", "What is the atomic number of carbon?", "atomic number", 6, 0, 30, "Six."),
    ("Science", "What is the atomic number of iron?", "atomic number", 26, 0, 60, "26, between manganese and cobalt."),
    ("Science", "What is the atomic number of helium?", "atomic number", 2, 0, 20, "Two."),
    ("Science", "What is the atomic number of nitrogen?", "atomic number", 7, 0, 30, "Seven."),
    ("Science", "What is the atomic number of sodium?", "atomic number", 11, 0, 40, "Eleven."),
    ("Science", "What is the atomic number of calcium?", "atomic number", 20, 0, 60, "Twenty."),
    ("Science", "How many elements are in the first period of the periodic table?", "elements", 2, 0, 20, "Hydrogen and helium."),

    # ---------------- Space ----------------
    ("Space", "How many days does Venus take to orbit the Sun?", "days", 225, 0, 600, "About 225 Earth days."),
    ("Space", "How many days does Jupiter take to orbit the Sun?", "days", 4333, 0, 10000, "About 4,333 Earth days."),
    ("Space", "How many moons does Uranus have?", "moons", 28, 0, 60, "28, as of 2023."),
    ("Space", "How many moons does Neptune have?", "moons", 16, 0, 40, "16, as of 2023."),
    ("Space", "How many moons does Pluto have?", "moons", 5, 0, 15, "Five."),

    # ---------------- Sport ----------------
    ("Sport", "How many points is an American football field goal worth?", "points", 3, 0, 10, "Three."),
    ("Sport", "How many points is an American football safety worth?", "points", 2, 0, 10, "Two."),
    ("Sport", "How many players are in a lacrosse team?", "players", 10, 0, 25, "Ten."),
    ("Sport", "How many players are in a handball team?", "players", 7, 0, 20, "Seven."),
    ("Sport", "How many balls are in a cricket over?", "balls", 6, 0, 15, "Six."),
    ("Sport", "How many stumps are at each end of a cricket pitch?", "stumps", 3, 0, 12, "Three."),
    ("Sport", "How many players are in a rugby league team?", "players", 13, 0, 30, "Thirteen."),
    ("Sport", "How many players are in a Gaelic football team?", "players", 15, 0, 30, "Fifteen."),
    ("Sport", "How many points is a rugby union try worth?", "points", 5, 0, 15, "Five."),
    ("Sport", "How many points is a rugby union conversion worth?", "points", 2, 0, 10, "Two."),
    ("Sport", "How many points is a rugby union drop goal worth?", "points", 3, 0, 10, "Three."),
    ("Sport", "How many players per ice hockey team are on the ice?", "players", 6, 0, 20, "Six, including the goalie."),
    ("Sport", "How many kilometres long is a half-marathon?", "km", 21, 0, 60, "About 21.1 km."),

    # ---------------- Food ----------------
    ("Food", "How many teaspoons are in a US cup?", "teaspoons", 48, 0, 120, "48, or 16 tablespoons."),
    ("Food", "How many grams are in an ounce?", "grams", 28, 0, 100, "28.35."),
    ("Food", "How many millilitres are in a US cup?", "ml", 240, 0, 600, "About 240."),
    ("Food", "How many calories are in a medium apple?", "calories", 95, 0, 300, "About 95."),
    ("Food", "How many calories are in a can of Coca-Cola?", "calories", 140, 0, 400, "About 140."),

    # ---------------- Animals ----------------
    ("Animals", "How many legs does a scorpion have?", "legs", 8, 0, 20, "Eight, plus its pincers."),
    ("Animals", "How many chambers does a fish heart have?", "chambers", 2, 0, 8, "Two."),
    ("Animals", "How many chambers does a bird heart have?", "chambers", 4, 0, 12, "Four."),
    ("Animals", "How many wings does a bee have?", "wings", 4, 0, 12, "Four, in two pairs."),
    ("Animals", "How many legs does a butterfly have?", "legs", 6, 0, 20, "Six."),
    ("Animals", "How many arms does a starfish typically have?", "arms", 5, 0, 15, "Five, in most species."),
    ("Human body", "How many cervical vertebrae are in the human neck?", "vertebrae", 7, 0, 20, "Seven."),

    # ---------------- Everyday ----------------
    ("Everyday", "How many numbered squares are on a dartboard?", "squares", 20, 0, 50, "Twenty."),
    ("Everyday", "How many points does it take to win a game of cribbage?", "points", 121, 0, 300, "121."),
    ("Everyday", "How many pieces does each player start with in checkers?", "pieces", 12, 0, 40, "Twelve."),
    ("Everyday", "How many points are on a backgammon board?", "points", 24, 0, 60, "24 triangles."),
    ("Everyday", "How many checkers does each player start with in backgammon?", "checkers", 15, 0, 40, "Fifteen."),
    ("Everyday", "How many tiles are in a mahjong set?", "tiles", 144, 0, 300, "144."),
    ("Everyday", "How many cards are in a standard Uno deck?", "cards", 108, 0, 300, "108."),
    ("Everyday", "How many colours are on a Rubik's cube?", "colours", 6, 0, 15, "Six."),
    ("Everyday", "How many squares are on each face of a Rubik's cube?", "squares", 9, 0, 20, "Nine, in a 3x3 grid."),
    ("Everyday", "How many digits are in a US phone number, without the area code?", "digits", 7, 0, 15, "Seven."),
    ("Everyday", "How many digits are in a US ZIP code?", "digits", 5, 0, 12, "Five."),
]

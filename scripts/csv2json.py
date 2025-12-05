#!/usr/bin/env python3

import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parent.parent

sources: List[Tuple[Path, Path]] = [
    (ROOT / "votd" / "votd.csv", ROOT / "votd" / "votd.json"),
]

BOOK_MAP: Dict[str, str] = {
    # Old Testament
    "Genesis": "GEN",
    "Exodus": "EXO",
    "Leviticus": "LEV",
    "Numbers": "NUM",
    "Deuteronomy": "DEU",
    "Joshua": "JOS",
    "Judges": "JDG",
    "Ruth": "RUT",
    "1 Samuel": "1SA",
    "2 Samuel": "2SA",
    "1 Kings": "1KI",
    "2 Kings": "2KI",
    "1 Chronicles": "1CH",
    "2 Chronicles": "2CH",
    "Ezra": "EZR",
    "Nehemiah": "NEH",
    "Esther": "EST",
    "Job": "JOB",
    "Psalm": "PSA",
    "Psalms": "PSA",
    "Proverbs": "PRO",
    "Ecclesiastes": "ECC",
    "Song of Solomon": "SNG",
    "Song of Songs": "SNG",
    "Isaiah": "ISA",
    "Jeremiah": "JER",
    "Lamentations": "LAM",
    "Ezekiel": "EZK",
    "Daniel": "DAN",
    "Hosea": "HOS",
    "Joel": "JOL",
    "Amos": "AMO",
    "Obadiah": "OBA",
    "Jonah": "JON",
    "Micah": "MIC",
    "Nahum": "NAM",
    "Habakkuk": "HAB",
    "Zephaniah": "ZEP",
    "Haggai": "HAG",
    "Zechariah": "ZEC",
    "Malachi": "MAL",
    # New Testament
    "Matthew": "MAT",
    "Mark": "MRK",
    "Luke": "LUK",
    "John": "JHN",
    "Acts": "ACT",
    "Romans": "ROM",
    "1 Corinthians": "1CO",
    "2 Corinthians": "2CO",
    "Galatians": "GAL",
    "Ephesians": "EPH",
    "Philippians": "PHP",
    "Colossians": "COL",
    "1 Thessalonians": "1TH",
    "2 Thessalonians": "2TH",
    "1 Timothy": "1TI",
    "2 Timothy": "2TI",
    "Titus": "TIT",
    "Philemon": "PHM",
    "Hebrews": "HEB",
    "James": "JAS",
    "1 Peter": "1PE",
    "2 Peter": "2PE",
    "1 John": "1JN",
    "2 John": "2JN",
    "3 John": "3JN",
    "Jude": "JUD",
    "Revelation": "REV",
}


def csv_to_json_rows(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with open(path, newline="", encoding="utf-8") as infile:
        reader = csv.reader(infile)

        for row in reader:
            if not row or all(col.strip() == "" for col in row):
                continue

            # Skip header: id,book,chapter,verse
            if row[0].strip() == "id" and len(row) > 1 and row[1].strip().lower() == "book":
                continue

            if len(row) < 4:
                print(f"Skipping malformed row in {path}: {row}")
                continue

            vid = int(row[0].strip())
            book_name = row[1].strip()
            chapter = int(row[2].strip())
            verse_field = row[3].strip()

            if book_name not in BOOK_MAP:
                raise ValueError(f"Unknown book name in VOTD CSV: '{book_name}'")

            if "-" in verse_field:
                verse_start_str, verse_end_str = verse_field.split("-", 1)
                verse_start = int(verse_start_str)
                verse_end = int(verse_end_str)
            else:
                verse_start = verse_end = int(verse_field)

            rows.append(
                {
                    "id": vid,
                    "book_code": BOOK_MAP[book_name],
                    "chapter": chapter,
                    "verse_start": verse_start,
                    "verse_end": verse_end,
                }
            )

    return rows


for source, target in sources:
    rows = csv_to_json_rows(source)
    with open(target, "w", encoding="utf-8") as outfile:
        json.dump(rows, outfile, ensure_ascii=False, indent=2)

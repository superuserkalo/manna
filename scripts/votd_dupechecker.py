#!/usr/bin/env python3
import csv
from collections import defaultdict

def load_rows(path: str):
    rows = []
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        #header_seen = False

        for row in reader:
            # Skip blank lines
            if not row or all(c.strip() == "" for c in row):
                continue

            # Skip header
            if row[0].strip() == "id" and row[1].strip().lower() == "book":
                continue

            if len(row) < 4:
                print("Skipping malformed row:", row)
                continue

            rows.append({
                "id": row[0].strip(),
                "book": row[1].strip(),
                "chapter": row[2].strip(),
                "verse": row[3].strip()
            })

    return rows


def check_duplicates(rows):
    id_map = {}
    id_duplicates = []

    ref_map = defaultdict(list)

    for entry in rows:
        vid = entry["id"]
        ref = f'{entry["book"]} {entry["chapter"]}:{entry["verse"]}'

        # Check ID duplicates
        if vid in id_map:
            id_duplicates.append((vid, id_map[vid], ref))
        else:
            id_map[vid] = ref

        # Check reference duplicates
        ref_map[ref].append(vid)

    ref_duplicates = {ref: ids for ref, ids in ref_map.items() if len(ids) > 1}

    return id_duplicates, ref_duplicates


def main():
    rows = load_rows("../votd/votd.csv")
    print(f"Loaded {len(rows)} verse entries.")

    id_dupes, ref_dupes = check_duplicates(rows)

    print("\n=== Duplicate ID Check ===")
    if not id_dupes:
        print("SUCCESS: No duplicate IDs found.")
    else:
        print("FAILURE: Duplicate IDs:")
        for vid, ref1, ref2 in id_dupes:
            print(f"ID {vid}: {ref1}  <==>  {ref2}")

    print("\n=== Duplicate Reference Check ===")
    if not ref_dupes:
        print("SUCCESS: No duplicate references found.")
    else:
        print("FAILURE: Duplicate references:")
        for ref, ids in ref_dupes.items():
            print(f"{ref}: used by IDs {ids}")


if __name__ == "__main__":
    main()

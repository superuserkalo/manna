#!/usr/bin/env python3
import json
from typing import Any, Dict
import xml.etree.ElementTree as E

# Mapping from output JSON filename to basic work metadata.
BIBLE_INFO = {
    "bible_kjv.json": {
        "id": "kjv",
        "title": "Holy Bible, King James Version",
        "language": "en",
    },
    "bible_web.json": {
        "id": "web",
        "title": "World English Bible",
        "language": "en",
    },
}

# Book IDs we want to exclude from the generated JSON.
# - FRT / GLO are preface and glossary (mostly empty/useless here).
# - The rest are Apocrypha / deuterocanonical books present in the source USFX.
EXCLUDED_BOOK_IDS = {
    # Front/back matter
    "FRT",  # Preface
    "GLO",  # Glossary
    # KJV Apocrypha
    "TOB",
    "JDT",
    "ESG",
    "WIS",
    "SIR",
    "BAR",
    "S3Y",
    "SUS",
    "BEL",
    "1MA",
    "2MA",
    "1ES",
    "MAN",
    "2ES",
    # WEBU-only Apocrypha additions
    "DAG",  # Daniel (Greek)
    "PS2",  # Psalm 151
    "3MA",
    "4MA",
}

sources = [
    ("../bibles/eng-kjv/bible_kjv_usfx.xml", "bible_kjv.json"),
    ("../bibles/eng-webu/bible_webu_usfx.xml", "bible_web.json"),
]

for source, file in sources:
    # Parse XML tree
    tree = E.parse(source)
    root = tree.getroot()

    # Basic USJ-rich v1.0 shell
    info = BIBLE_INFO.get(file, {})
    work_id = info.get("id", file.rsplit(".", 1)[0])
    language = info.get("language", "en")
    title = info.get("title", work_id)

    output: Dict[str, Any] = {
        "usj_version": "1.0-rich",
        "id": work_id,
        "language": language,
        "scope": "bible",
        "metadata": {
            "title": title,
            "subtitle": None,
            "publisher": None,
            "license": "Public Domain",
            "copyright": None,
            "source": f"Converted from USFX: {source}",
            "created_at": None,
            "revised_at": None,
        },
        "books": {},
    }

    # Only handle real USFX roots
    if root.tag != "usfx":
        continue

    # Iterate over books
    for book in root.findall("book"):
        # Example: GEN
        book_id = book.get("id")
        if not book_id:
            continue
        if book_id in EXCLUDED_BOOK_IDS:
            # Skip Apocrypha, preface, glossary, etc.
            continue

        # Book display name from <h>
        header_node = book.find("h")
        if header_node is not None and header_node.text:
            book_name = header_node.text.strip()
        else:
            book_name = "No Title"

        # Optional long/formal title from first <toc>, if present
        titles_node = book.find("toc")
        titles_text = titles_node.text.strip() if (titles_node is not None and titles_node.text) else None

        # Collect chapter numbers from <c> elements
        chapter_ids = []
        for chapter in book.findall("c"):
            chapter_id = chapter.get("id")
            if not chapter_id:
                continue
            try:
                chapter_ids.append(int(chapter_id))
            except ValueError:
                continue

        # Deduplicate and sort chapter numbers
        chapter_ids = sorted(set(chapter_ids))

        # Per-book structures
        chapter_verse_counts: Dict[int, int] = {}
        chapters_data: Dict[int, Dict[str, Any]] = {}

        # Mutable state used while walking the XML subtree
        state: Dict[str, Any] = {
            "current_chapter": None,
            "current_verse": None,
            "current_buffer": [],
            "current_strongs": [],
            "current_footnotes": [],
            "current_words": [],
            "current_block": None,
        }

        def walk(elem: E.Element, inside_footnote: bool = False) -> None:
            tag = elem.tag

            current_chapter = state["current_chapter"]
            current_verse = state["current_verse"]
            current_buffer = state["current_buffer"]
            current_strongs = state["current_strongs"]
            current_footnotes = state["current_footnotes"]
            current_words = state["current_words"]

            # Save previous block so we can restore it after this element
            prev_block = state["current_block"]

            # Paragraph-like elements: remember their style as the active block
            if tag == "p":
                style = elem.get("style") or elem.get("sfm")
                if style:
                    state["current_block"] = style

            if tag == "v":
                # Start of a verse
                bcv = elem.get("bcv")
                if not bcv:
                    return
                parts = bcv.split(".")
                if len(parts) != 3:
                    return
                _, chap_str, verse_str = parts
                try:
                    chap = int(chap_str)
                    verse_num = int(verse_str)
                except ValueError:
                    return

                state["current_chapter"] = chap
                state["current_verse"] = verse_num
                state["current_buffer"] = []
                state["current_strongs"] = []
                state["current_footnotes"] = []
                state["current_words"] = []

                # Track max verse per chapter
                current_max = chapter_verse_counts.get(chap, 0)
                if verse_num > current_max:
                    chapter_verse_counts[chap] = verse_num

            elif tag == "ve":
                # End of verse
                if current_chapter is not None and current_verse is not None:
                    raw_text = "".join(current_buffer)
                    text = " ".join(raw_text.split())

                    verse_entry: Dict[str, Any] = {"text": text}

                    # Block/paragraph information, if known
                    block = state.get("current_block")
                    if block:
                        verse_entry["block"] = block

                    # Verse-level Strong's list
                    if current_strongs:
                        verse_entry["strongs"] = list(current_strongs)

                    # Footnotes: convert from strings to simple objects
                    if current_footnotes:
                        footnote_objs = []
                        for idx, raw_note in enumerate(current_footnotes, start=1):
                            # Strip leading "chapter:verse " if present (e.g. "1:1 ")
                            prefix = f"{current_chapter}:{current_verse} "
                            text_note = raw_note
                            if raw_note.startswith(prefix):
                                text_note = raw_note[len(prefix):]
                            footnote_objs.append(
                                {
                                    "id": f"{book_id}.{current_chapter}.{current_verse}.{idx}",
                                    "text": text_note,
                                }
                            )
                        verse_entry["footnotes"] = footnote_objs

                    # Word-level data
                    if current_words:
                        verse_entry["words"] = list(current_words)

                    # Store verse
                    chapters_data.setdefault(current_chapter, {"verses": {}})
                    chapters_data[current_chapter]["verses"][str(current_verse)] = verse_entry

                # Reset verse-local state
                state["current_chapter"] = None
                state["current_verse"] = None
                state["current_buffer"] = []
                state["current_strongs"] = []
                state["current_footnotes"] = []
                state["current_words"] = []

            else:
                if current_chapter is not None and not inside_footnote:
                    # Collect Strong's numbers from <w s="..."> elements
                    if tag == "w":
                        s_code = elem.get("s")
                        if s_code:
                            current_strongs.append(s_code)
                        # Capture word text for the words[] array
                        word_text = elem.text or ""
                        if word_text.strip():
                            current_words.append(
                                {
                                    "w": word_text,
                                    "strongs": [s_code] if s_code else [],
                                }
                            )

                    # Add element text (but not footnote content) to verse body
                    if elem.text:
                        current_buffer.append(elem.text)

                # Footnote: record its internal text separately
                if tag == "f" and current_chapter is not None:
                    footnote_text = "".join(elem.itertext())
                    footnote_text = " ".join(footnote_text.split())
                    if footnote_text:
                        current_footnotes.append(footnote_text)

            # Recurse into children, tracking whether inside a footnote
            next_inside_footnote = inside_footnote or (elem.tag == "f")
            for child in elem:
                walk(child, next_inside_footnote)

            # After processing children, capture tail text if in verse and not in footnote
            if current_chapter is not None and not inside_footnote and elem.tail:
                current_buffer.append(elem.tail)

            # Restore previous block context
            state["current_block"] = prev_block

        # Start walking from the book element
        walk(book)

        # If there were no explicit chapter markers, infer chapters from verses
        if not chapter_ids:
            chapter_ids = sorted(chapter_verse_counts.keys())

        # Ensure all known chapters are present in chapters_data
        for chap in chapter_ids:
            chapters_data.setdefault(chap, {"verses": {}})

        # Build book entry for USJ
        book_entry: Dict[str, Any] = {
            "name": book_name,
            "chapters": {str(chap): chapters_data[chap] for chap in sorted(chapters_data)},
        }
        if titles_text:
            book_entry["titles"] = titles_text

        if book_id:
            output["books"][book_id] = book_entry

    # Dump JSON with full Unicode characters (no \uXXXX escapes)
    with open(file, "w", encoding="utf-8") as outfile:
        json.dump(output, outfile, ensure_ascii=False, indent=2)


# for the future going to update this script
if __name__ == "__main__":
    pass

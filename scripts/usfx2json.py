#!/usr/bin/env python3
import json
from typing import Any, Dict
import xml.etree.ElementTree as E

sources = [
 ('../bibles/eng-kjv/eng-kjv_usfx.xml', 'bible_kjv.json'),
 ('../bibles/eng-webu/eng-webu_usfx.xml', 'bible_web.json'),
]

for source, file in sources:
    # File path to build tree
    tree = E.parse(source)
    root = tree.getroot()

    books = root.findall('book')
    output = {"books": {}}

    # Checks if the xml file is usfx
    if root.tag == 'usfx':
        for book in books:
            # Get the ID from the book attribute which returns e.g.: GEN
            book_id = book.get('id')

            # Find the header element, which holds the full name of that book_id e.g.: Genesis
            header_node = book.find('h')

            # Check if the element was found and has text
            # If yes return the element as text and strip whitespace
            # If no handle it gracefully by returning a No Title
            if header_node is not None and header_node.text:
                book_name = header_node.text.strip()
            else:
                book_name = "No Title"

            # Collect chapter numbers from <c> elements so chapter count is independent of verses
            chapter_ids = []
            for chapter in book.findall('c'):
                chapter_id = chapter.get('id')
                if not chapter_id:
                    continue
                try:
                    chapter_ids.append(int(chapter_id))
                except ValueError:
                    continue
            # Deduplicate and sort chapter numbers
            chapter_ids = sorted(set(chapter_ids))

            # Walk the book in document order to collect verse counts, verse text,
            # Strong's numbers, and footnotes.
            chapter_verse_counts: Dict[int, int] = {}
            chapters_data: Dict[int, Dict[str, Any]] = {}

            # Mutable state we pass into the walker so we don't need nonlocal
            state: Dict[str, Any] = {
                "current_chapter": None,
                "current_verse": None,
                "current_buffer": [],
                "current_strongs": [],
                "current_footnotes": [],
            }

            def walk(elem: E.Element, inside_footnote: bool = False) -> None:
                tag = elem.tag

                current_chapter = state["current_chapter"]
                current_verse = state["current_verse"]
                current_buffer = state["current_buffer"]
                current_strongs = state["current_strongs"]
                current_footnotes = state["current_footnotes"]

                if tag == 'v':
                    bcv = elem.get('bcv')
                    if not bcv:
                        return
                    parts = bcv.split('.')
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

                    # Track max verse number per chapter
                    current_max = chapter_verse_counts.get(chap, 0)
                    if verse_num > current_max:
                        chapter_verse_counts[chap] = verse_num

                elif tag == 've':
                    if current_chapter is not None and current_verse is not None:
                        raw_text = ''.join(current_buffer)
                        # Normalize whitespace
                        text = ' '.join(raw_text.split())

                        verse_entry: Dict[str, Any] = {"text": text}
                        if current_strongs:
                            verse_entry["strongs"] = list(current_strongs)
                        if current_footnotes:
                            verse_entry["footnotes"] = list(current_footnotes)

                        chapters_data.setdefault(current_chapter, {"verses": {}})
                        chapters_data[current_chapter]["verses"][str(current_verse)] = verse_entry

                    state["current_chapter"] = None
                    state["current_verse"] = None
                    state["current_buffer"] = []
                    state["current_strongs"] = []
                    state["current_footnotes"] = []

                else:
                    if current_chapter is not None and not inside_footnote:
                        # Collect Strong's numbers from <w s="..."> elements
                        if tag == 'w':
                            s_code = elem.get('s')
                            if s_code:
                                current_strongs.append(s_code)

                        # Only add normal element text to the verse body,
                        # not the contents of any footnote elements.
                        if elem.text:
                            current_buffer.append(elem.text)

                    # When we encounter a footnote, record its internal text,
                    # but treat its content as separate from the verse body.
                    if tag == 'f' and current_chapter is not None:
                        footnote_text = ''.join(elem.itertext())
                        footnote_text = ' '.join(footnote_text.split())
                        if footnote_text:
                            current_footnotes.append(footnote_text)

                # Recurse into children, tracking whether we're inside a footnote subtree
                next_inside_footnote = inside_footnote or (elem.tag == 'f')
                for child in elem:
                    walk(child, next_inside_footnote)

                # After processing children, capture tail text if we're in a verse
                # and not inside a footnote. This preserves text that comes after
                # inline elements like <w> or <f>.
                if current_chapter is not None and not inside_footnote and elem.tail:
                    current_buffer.append(elem.tail)

            # Start walking from the book root element
            walk(book)

            # If we didn't find explicit chapter markers, fall back to chapters inferred from verses
            if not chapter_ids:
                chapter_ids = sorted(chapter_verse_counts.keys())

            # Ensure all known chapters appear in chapters_data, even if they have no verses
            for chap in chapter_ids:
                chapters_data.setdefault(chap, {"verses": {}})

            # Build book entry
            book_entry = {
                "name": book_name,
                "chapters": {str(chap): chapters_data[chap] for chap in sorted(chapters_data)}
            }

            output["books"][book_id] = book_entry

        # Dump JSON to file with full Unicode characters (no \uXXXX escapes)
        with open(file, "w", encoding="utf-8") as outfile:
            json.dump(output, outfile, ensure_ascii=False, indent=2)

# for the future
if __name__ == "__main__":
    ...

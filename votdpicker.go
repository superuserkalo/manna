package main

import (
	"encoding/json"
	"fmt"
	"os"
	"strings"
)

// PicknReturnVotd selects a unique verse-of-the-day reference and returns
// the corresponding passage text from the minimal NUSJ Bible file.
func PicknReturnVotd() string {
	v := ReturnVotd()

	passage, err := lookupPassage("bibles/eng-kjv/bible_kjv_nusj_minimal.json", v)
	if err != nil {
		panic(err)
	}

	return passage
}

// lookupPassage streams through the minimal NUSJ Bible file and only
// decodes verses for the specific book/chapter/verse range we need.
func lookupPassage(path string, v Votd) (string, error) {
	f, err := os.Open(path)
	if err != nil {
		return "", err
	}
	defer f.Close()

	dec := json.NewDecoder(f)

	// Expect the top-level object.
	tok, err := dec.Token()
	if err != nil {
		return "", err
	}
	if delim, ok := tok.(json.Delim); !ok || delim != '{' {
		return "", fmt.Errorf("expected top-level object")
	}

	// Walk keys until we reach "books".
	for dec.More() {
		keyTok, err := dec.Token()
		if err != nil {
			return "", err
		}
		key, ok := keyTok.(string)
		if !ok {
			return "", fmt.Errorf("expected string key at top level")
		}

		if key != "books" {
			// Skip value for keys we don't care about.
			if err := skipValue(dec); err != nil {
				return "", err
			}
			continue
		}

		// Value for "books" should be an object of book codes -> book data.
		tok, err := dec.Token()
		if err != nil {
			return "", err
		}
		if delim, ok := tok.(json.Delim); !ok || delim != '{' {
			return "", fmt.Errorf("expected object for books")
		}

		// Walk through the books until we find the one we need.
		for dec.More() {
			bookKeyTok, err := dec.Token()
			if err != nil {
				return "", err
			}
			bookCode, ok := bookKeyTok.(string)
			if !ok {
				return "", fmt.Errorf("expected string book code")
			}

			if bookCode != v.BookCode {
				// Skip this entire book object.
				if err := skipValue(dec); err != nil {
					return "", err
				}
				continue
			}

			// We are at the desired book. Its value is an object
			// of "chapter:verse" -> text.
			tok, err := dec.Token()
			if err != nil {
				return "", err
			}
			if delim, ok := tok.(json.Delim); !ok || delim != '{' {
				return "", fmt.Errorf("expected object for book %s", v.BookCode)
			}

			var verses []string
			for dec.More() {
				versKeyTok, err := dec.Token()
				if err != nil {
					return "", err
				}
				versKey, ok := versKeyTok.(string)
				if !ok {
					return "", fmt.Errorf("expected string verse key")
				}

				var text string
				if err := dec.Decode(&text); err != nil {
					return "", err
				}

				// We only care about verses in the requested chapter
				// and verse range.
				// Keys are of the form "chapter:verse".
				var chap, verse int
				if _, err := fmt.Sscanf(versKey, "%d:%d", &chap, &verse); err != nil {
					continue
				}
				if chap == v.Chapter && verse >= v.VerseStart && verse <= v.VerseEnd {
					verses = append(verses, text)
				}
			}

			// Consume closing '}' for the book object.
			if tok, err := dec.Token(); err != nil {
				return "", err
			} else if delim, ok := tok.(json.Delim); !ok || delim != '}' {
				return "", fmt.Errorf("expected closing object for book %s", v.BookCode)
			}

			if len(verses) == 0 {
				return "", fmt.Errorf("no verses found for %s %d:%d-%d", v.BookCode, v.Chapter, v.VerseStart, v.VerseEnd)
			}
			return strings.Join(verses, " "), nil
		}

		// If we finish the books object without finding the book.
		return "", fmt.Errorf("book code %s not found", v.BookCode)
	}

	return "", fmt.Errorf("books object not found in Bible JSON")
}

// skipValue consumes the next JSON value (including nested arrays/objects)
// from the decoder without storing it.
func skipValue(dec *json.Decoder) error {
	tok, err := dec.Token()
	if err != nil {
		return err
	}

	switch tok.(type) {
	case json.Delim:
		// Start of object/array; consume until matching end.
		var depth = 1
		for depth > 0 {
			tok, err := dec.Token()
			if err != nil {
				return err
			}
			if delim, ok := tok.(json.Delim); ok {
				switch delim {
				case '{', '[':
					depth++
				case '}', ']':
					depth--
				}
			}
		}
	}
	return nil
}

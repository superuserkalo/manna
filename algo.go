package main

import (
	"encoding/json"
	"math/rand/v2"
	"os"
)

type Votd struct {
	ID         int    `json:"id"`
	BookCode   string `json:"book_code"`
	Chapter    int    `json:"chapter"`
	VerseStart int    `json:"verse_start"`
	VerseEnd   int    `json:"verse_end"`
}

func ReturnVotd() Votd {
	data, err := os.ReadFile("votd/votd.json")
	if err != nil {
		panic(err)
	}

	var verses []Votd
	if err := json.Unmarshal(data, &verses); err != nil {
		panic(err)
	}

	// Load or initialize the list of unused IDs from disk.
	unusedIDs, err := loadUnusedIDs("votd/unused_ids.json", verses)
	if err != nil {
		panic(err)
	}

	// Pick a random index from the unused IDs slice.
	randomIndex := rand.IntN(len(unusedIDs))
	chosenID := unusedIDs[randomIndex]

	// Remove the chosen ID from the unused slice (swap with last, then trim).
	unusedIDs[randomIndex] = unusedIDs[len(unusedIDs)-1]
	unusedIDs = unusedIDs[:len(unusedIDs)-1]

	// Persist updated unused IDs so the state survives across runs.
	if err := saveUnusedIDs("votd/unused_ids.json", unusedIDs); err != nil {
		panic(err)
	}

	// Find the chosen verse by its ID (IDs are unique in votd.json).
	var chosen Votd
	for _, v := range verses {
		if v.ID == chosenID {
			chosen = v
			break
		}
	}

	return chosen
}

// loadUnusedIDs loads the list of unused verse IDs from path. If the file
// does not exist, is empty, or invalid, it initializes the list from verses.
func loadUnusedIDs(path string, verses []Votd) ([]int, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		if os.IsNotExist(err) {
			return allIDsFromVerses(verses), nil
		}
		return nil, err
	}

	var ids []int
	if err := json.Unmarshal(data, &ids); err != nil {
		return allIDsFromVerses(verses), nil
	}

	// If we've exhausted all IDs or the file was empty, start over.
	if len(ids) == 0 {
		return allIDsFromVerses(verses), nil
	}

	// Validate that all stored IDs actually exist in verses.
	valid := make(map[int]struct{}, len(verses))
	for _, v := range verses {
		valid[v.ID] = struct{}{}
	}
	for _, id := range ids {
		if _, ok := valid[id]; !ok {
			return allIDsFromVerses(verses), nil
		}
	}

	return ids, nil
}

func saveUnusedIDs(path string, ids []int) error {
	data, err := json.Marshal(ids)
	if err != nil {
		return err
	}
	return os.WriteFile(path, data, 0o644)
}

func allIDsFromVerses(verses []Votd) []int {
	ids := make([]int, len(verses))
	for i, v := range verses {
		ids[i] = v.ID
	}
	return ids
}

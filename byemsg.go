package main

import "math/rand/v2"

func goodbyemessage() string {
	goodbyes := []string{
		"Grace and peace to you.",
		"The Lord be with you.",
		"Stay blessed.",
		"May His word guide your steps.",
		"Go in peace.",
		"Be strengthened for the journey.",
		"Walk in His light.",
		"May His peace rest upon you.",
		"Stay in His grace.",
		"May today bring you closer to Him.",
		"The Lord is your refuge.",
		"The joy of the Lord is your strength.",
		"His mercies are new every morning.",
		"The Lord watches over you.",
		"Keep the faith.",
		"Go with God.",
		"Blessings on your day.",
		"Stay rooted in the Word.",
		"Till we meet again.",
		"Rest in His goodness.",
		"Abide in His love.",
		"May your heart be at peace.",
		"Rest in His promises.",
		"May His comfort surround you.",
		"Walk gently with Him.",
		"Hold fast to hope.",
		"May His presence calm your spirit.",
		"Be still and know.",
		"May His joy sustain you.",
		"Find rest in His love.",
		"May His kindness follow you.",
		"The Lord is near.",
		"He is faithful.",
		"May His strength uphold you.",
		"The Lord goes before you.",
		"Under His wings you find refuge.",
		"He is your rock and fortress.",
		"The Lord is your light.",
		"His grace is sufficient.",
		"The Lord is your helper.",
		"He guards your coming and going.",
		"Walk in His peace.",
		"The Lord uplift you.",
	}

	index := rand.IntN(len(goodbyes))

	return goodbyes[index]
}

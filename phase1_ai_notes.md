# Phase 1 AI Notes

## Actual request and assistance

The student asked the assistant to follow the supplied Phase 1 instructions, identify blockers, and create a new workspace. The student then supplied the CodePath starter URL. The assistant researched primary sources, forked and cloned the starter, audited the actual CSV, and drafted README documentation. No personal preferences, listening feedback, or student reflection were invented. This file records assistance; it is not a fabricated transcript of separate prompts from the student.

## Suggested prompts for reviewing the design

1. "Compare collaborative and content-based music filtering. Identify user behavior, song attributes, and taste representations separately, citing Spotify and Google primary sources."
2. "Analyze data/songs.csv. Which attributes best capture vibe, what ranges and imbalances exist, and what information is missing?"
3. "Design a normalized weighted score using the starter UserProfile. How can energy closeness reward both slightly lower and slightly higher values equally? Explain scoring versus ranking."
4. "How could genre/mood matching create a filter bubble? Suggest relevance and diversity checks without claiming unmeasured results."

## Design decisions to review

- Starting weights: genre 0.40, mood 0.30, energy 0.20, acousticness 0.10.
- Energy similarity: 1 minus absolute distance on the 0 to 1 scale.
- Rank by score descending, then numeric song ID ascending.
- Retain all Song fields; postpone tempo, valence, and danceability contributions until their target preferences are defined.
- The example pop/happy profile illustrates arithmetic and does not represent the student's musical preferences.

## Verification performed

Read the starter interfaces and tests. Audited the CSV using Python's standard csv module: 10 records, unique IDs, no empty cells, and numeric ranges documented in README. No claims of runtime recommendation quality or successful scoring tests are made: the implementation is still the starter.

## Student review remaining

Check whether the chosen features reflect your experience of musical vibe. Adjust the example profile and weights if needed. Write your own personal reflection when the later implementation/evaluation phases are complete.

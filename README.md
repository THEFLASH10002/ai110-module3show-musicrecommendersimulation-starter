# Music Recommender Simulation

## Project Summary

This working CLI-first simulation recommends music from an expanded 18-song catalog. It loads typed CSV records, compares songs with explicit preferences, and returns a ranked list with score explanations. The functional and dataclass interfaces share the scoring recipe defined below.

## How The System Works

Real recommendation systems turn listening behavior and content information into predictions of what someone might enjoy. Collaborative filtering uses patterns across listeners, while content-based filtering compares attributes of songs with a listener's preferences. Spotify describes combining listening history with track relationships and audio attributes, and updating taste representations from listening, skips, and saves ([Spotify Engineering](https://engineering.atspotify.com/2023/4/humans-machines-a-look-behind-spotifys-algotorial-playlists)). This simulation prioritizes matching genre and mood, closeness to a preferred energy level, and acoustic preference. It assigns each song a transparent weighted score, sorts the catalog, and returns the top k songs with explanations. Its scores represent similarity, not probabilities that a person will like a song.

### Song and UserProfile features

`data/songs.csv` preserves the original ten songs and adds eight fictional songs (IDs 11–18). The additions introduce folk, ska, country, soul, hip hop, classical, reggae, and house, with eight moods absent from the starter catalog: reflective, playful, melancholic, romantic, defiant, solemn, hopeful, and euphoric. Their numeric values are synthetic design examples, not measured audio features. Every energy, valence, danceability, and acousticness value is on a 0.0–1.0 scale; tempo is in BPM.

The data expansion prompt for this step is:

> Generate eight fictional songs as valid CSV using exactly these headers: id,title,artist,genre,mood,energy,tempo_bpm,valence,danceability,acousticness. Use unique IDs 11–18. Introduce genres outside pop, lofi, rock, ambient, jazz, synthwave, and indie pop, and moods outside happy, chill, intense, relaxed, moody, and focused. Keep all normalized numerical features within 0.0–1.0 and tempo positive. Return the header and eight complete rows with no extra columns.

Danceability and acousticness already provide the suggested extra numerical depth, alongside tempo and valence. Keep these existing columns rather than adding duplicate features. The advanced extension below adds five distinct attributes. Only acousticness joins energy in the core recipe; the advanced extension adds optional terms without reusing tempo, valence, or danceability.

The existing `Song` dataclass stores every CSV field:

| Field | Role |
| --- | --- |
| `id`, `title`, `artist` | Identification and display; no score contribution |
| `genre` | Exact match against `favorite_genre` |
| `mood` | Exact match against `favorite_mood` |
| `energy` | Numerical closeness to `target_energy` |
| `acousticness` | Match to `likes_acoustic` |
| `tempo_bpm`, `valence`, `danceability` | Retained for future scoring experiments |

The existing `UserProfile` stores `favorite_genre: str`, `favorite_mood: str`, `target_energy: float` (0 to 1), and `likes_acoustic: bool`. It expresses explicit preferences; it does not infer taste from listening history. Keep these interfaces compatible with the starter tests. The functional runner uses `genre`, `mood`, and `energy` dictionary keys; the shared scorer adapts those to the same recipe, with missing acoustic preference meaning no acoustic contribution.

### Example taste profile and critique

Use this specific hypothetical profile for a listener seeking calm study music:

```python
user_profile = {
    "favorite_genre": "lofi",
    "favorite_mood": "chill",
    "target_energy": 0.40,
    "likes_acoustic": True,
}
```

This is a simulation persona, not a claim about the student's personal taste. It can be passed to `UserProfile(**user_profile)`. The functional scorer accepts either these descriptive keys or the shorter `genre`, `mood`, and `energy` keys used by the CLI; shorter keys take precedence when both are supplied. Missing or `None` acoustic preference omits that component.

Profile critique prompt:

> Critique this profile: favorite_genre=lofi, favorite_mood=chill, target_energy=0.40, likes_acoustic=True. With the attached songs.csv and the recipe below, can it distinguish intense rock from chill lofi? Is it too narrow for discovery? Identify missing preferences without assuming that this represents all of the listener's taste.

The profile clearly distinguishes the two styles: it rewards lofi and chill matches, low energy distance, and acousticness. It is useful for one study session but narrow as a permanent taste model. One genre and one mood cannot capture a listener who also enjoys intense rock during exercise. Later versions could support multiple genres, activity-specific profiles, and an optional discovery slot. Acoustic preference is independent of genre; lofi is not necessarily acoustic.

### Algorithm Recipe

Initial weights are design choices to evaluate, not learned parameters:

| Component | Similarity | Weight |
| --- | --- | --- |
| Genre | 1 for an exact match, otherwise 0 | 0.40 |
| Mood | 1 for an exact match, otherwise 0 | 0.30 |
| Energy | `1 - abs(song.energy - user.target_energy)` | 0.20 |
| Acousticness | `song.acousticness` if acoustic is preferred; otherwise `1 - song.acousticness` | 0.10 |

Normalize categorical text with trimming and case folding before comparing. Treat `pop` and `indie pop` as different categories in the first version and document the limitation.

`score = (0.40 * genre_match + 0.30 * mood_match + 0.20 * energy_similarity + 0.10 * acoustic_similarity) / active_weight_sum`

With all four preferences present, `active_weight_sum = 1.0`. With no acoustic preference, omit that component and divide by 0.90. Validate numerical attributes within 0 to 1; invalid values should produce clear errors rather than misleading scores. All examples here use valid data. Under this recipe, `likes_acoustic=False` means a preference for lower acousticness; absence of a preference is a separate case.

Genre gets slightly more weight than mood as an initial familiarity preference. Mood and energy together can outweigh genre, so a different genre can still rank well. This choice may limit discovery; later compare a mood-first recipe, such as swapping the genre and mood weights.

Energy rewards closeness rather than magnitude: for a target of 0.40, songs at 0.35 and 0.45 both earn 0.95 similarity, while a song at 0.90 earns 0.50. A higher energy song is not automatically better.

**Scoring rule:** evaluate one song against one profile. **Ranking rule:** evaluate all songs, sort by descending unrounded score, break ties by ascending numeric song ID, and return the first k. Return an empty list for k <= 0 and all available songs if k exceeds the catalog size. The scoring rule defines relevance; the ranking rule determines the returned list and resolves ties. Round scores only for display.

For an illustrative profile (`pop`, `happy`, energy 0.80, `likes_acoustic=False`), Sunrise City would score `0.40 + 0.30 + 0.20*0.98 + 0.10*0.82 = 0.978`. This is a worked calculation, not output from an implemented recommender or a claim about the student's taste.

For the study profile above, Library Rain scores `0.40 + 0.30 + 0.20*0.95 + 0.10*0.86 = 0.976`, while Storm Runner scores `0 + 0 + 0.20*0.49 + 0.10*0.10 = 0.108`. These hand calculations show how chill lofi outranks intense rock for this particular session. They do not measure recommendation quality.

The finalized recipe keeps the existing normalized weights: genre 40%, mood 30%, energy 20%, and acousticness 10%. Mood is close enough to genre in weight to influence ranking substantially, while the two numerical features distinguish songs with identical labels. The optional +2 genre / +1 mood / energy-similarity recipe would put more emphasis on genre relative to mood; the selected weights better fit this session's mood preference.

For the requested separate chat, open a session titled **Scoring Logic Design**, attach the expanded `data/songs.csv`, and use this prompt:

> Compare +2 genre / +1 mood / energy similarity with a normalized 40% genre / 30% mood / 20% energy / 10% acousticness recipe for the study profile above. How much should mood count relative to genre? Use Library Rain and Storm Runner as worked examples, discuss discovery bias, and specify normalization, missing preferences, tie-breaking, and top-k behavior.

This plan was prepared in the current chat; a separate chat session has not been created by the assistant.

### Modular flow

```text
Input: user preferences + data/songs.csv
  -> load song records and validate feature ranges
  -> loop over every song: compare labels and numerical features
  -> calculate weighted score and matching reasons for each song
  -> sort by descending score, then ascending numeric ID for ties
  -> output: top k recommendations with scores and explanations
```

One scoring recipe is shared by the functional and object-oriented interfaces. `Recommender.recommend` ranks songs; `explain_recommendation` describes the same contributions used to score them. Explanations identify actual matches and distances rather than claim certainty about enjoyment.

### Implementation and sorting

`load_songs` uses Python's `csv.DictReader` and returns dictionaries with integer IDs and floats for energy, tempo, valence, danceability, and acousticness. It rejects missing or extra columns, incomplete rows, duplicate IDs, invalid normalized values, and nonpositive or nonfinite tempo with clear errors. `score_song` returns `(score, reasons)`, where reasons is a list of strings describing each normalized contribution. `recommend_songs` scores each song and returns `(song, score, explanation)` tuples, joining the reasons for display.

`sorted(items, key=...)` returns a new sorted list and leaves the input order intact. `items.sort(key=...)` changes an existing list in place and returns `None`. This implementation uses `sorted` on scored results with `(-score, numeric_id)` as the key, preserving the catalog and sorting full-precision scores before slicing the top k. Displayed contributions are rounded independently, so their sum may differ slightly from the displayed final score.

### Expected biases in this plan

Genre has the largest individual weight, so the system may overlook songs that fit the mood but use unfamiliar genre labels. Lofi and chill still have three examples each, while the new genres and moods have one each; expanding coverage does not balance the catalog. Exact matching misses related styles, and a fixed profile cannot represent changing contexts. The invented numeric attributes also reflect the author's assumptions about music. Assess relevance and genre/artist variety together before making claims about recommendation quality.

## Sample Recommendation Output

Actual output from `python -m src.main` with the default pop/happy profile. Sunrise City matches both labels; Gym Hero matches genre, while Rooftop Lights matches mood. The remaining results match neither label and rank by energy closeness. No acoustic preference is supplied, so the three active weights are normalized by 0.90.

```text
Loaded songs: 18
Profile: genre=pop, mood=happy, target energy=0.80
Mode: baseline | Diversity: off

Top 5 recommendations (adjusted scores when diversity is on):
+------+----------------------+-----------------+---------+--------------------------------------------------------------------+
| Rank | Song                 | Artist          | Score   | Reasons                                                            |
+------+----------------------+-----------------+---------+--------------------------------------------------------------------+
| 1    | Sunrise City         | Neon Echo       | 0.996   | genre match (+0.444); mood match (+0.333); energy distance 0.020   |
|      |                      |                 |         | (+0.218); acousticness omitted; active weights normalized by 0.90  |
+------+----------------------+-----------------+---------+--------------------------------------------------------------------+
| 2    | Gym Hero             | Max Pulse       | 0.638   | genre match (+0.444); mood mismatch (+0.000); energy distance      |
|      |                      |                 |         | 0.130 (+0.193); acousticness omitted; active weights normalized by |
|      |                      |                 |         | 0.90                                                               |
+------+----------------------+-----------------+---------+--------------------------------------------------------------------+
| 3    | Rooftop Lights       | Indigo Parade   | 0.547   | genre mismatch (+0.000); mood match (+0.333); energy distance      |
|      |                      |                 |         | 0.040 (+0.213); acousticness omitted; active weights normalized by |
|      |                      |                 |         | 0.90                                                               |
+------+----------------------+-----------------+---------+--------------------------------------------------------------------+
| 4    | Night Drive Loop     | Neon Echo       | 0.211   | genre mismatch (+0.000); mood mismatch (+0.000); energy distance   |
|      |                      |                 |         | 0.050 (+0.211); acousticness omitted; active weights normalized by |
|      |                      |                 |         | 0.90                                                               |
+------+----------------------+-----------------+---------+--------------------------------------------------------------------+
| 5    | Brass Horizon        | Copper Steps    | 0.209   | genre mismatch (+0.000); mood mismatch (+0.000); energy distance   |
|      |                      |                 |         | 0.060 (+0.209); acousticness omitted; active weights normalized by |
|      |                      |                 |         | 0.90                                                               |
+------+----------------------+-----------------+---------+--------------------------------------------------------------------+
```

## Phase 1 Data Analysis

The original starter CSV audit below records 10 rows, 10 unique IDs, 10 columns, and no missing cells. It is a historical baseline; the expanded CSV now has 18 rows, 18 unique IDs, and 15 columns, including the five advanced features below.

| Attribute | Observed values |
| --- | --- |
| Genre counts | lofi: 3; pop: 2; rock, ambient, jazz, synthwave, indie pop: 1 each |
| Mood counts | chill: 3; happy: 2; intense: 2; relaxed, moody, focused: 1 each |
| Energy | 0.28 to 0.93 |
| Tempo | 60 to 152 BPM |
| Valence | 0.48 to 0.84 |
| Danceability | 0.41 to 0.88 |
| Acousticness | 0.05 to 0.92 |

Genre and mood are interpretable starting points. Energy captures intensity and gives graded matches; acousticness adds information already requested by the starter profile. Tempo could capture pace, valence emotional positivity, and danceability rhythmic suitability. These numeric labels are proxies: the CSV does not document how they were measured. Do not invent target preferences for fields the user has not supplied.

Mood, energy, and tempo plausibly capture parts of a musical "vibe," but tempo is not intensity and a happy label is not a complete emotional description. Lyrics, timbre, language, context, and personal associations are missing. Mood and valence may overlap, so adding both can double-count similar signals. No personal listening preferences were supplied; the student should review whether this definition of vibe fits their own experience.

## Research: Real Recommendation Systems

- **Collaborative filtering:** learn from behavior shared across users or items. If listeners with similar histories enjoy another song, recommend it to the target listener. It can suggest a new genre, but sparse histories and new songs make it harder. Spotify Research explicitly describes taste similarity across people as the basis of collaborative filtering ([source](https://research.atspotify.com/2024/6/socially-motivated-music-recommendation)).
- **Content-based filtering:** compare attributes or learned content representations with items or preferences a user already likes. Our proposed system uses supplied genre, mood, and numeric attributes, without other users' behavior. Google Research illustrates content similarity as a way to recommend newly uploaded videos with little behavioral history ([source](https://research.google/pubs/content-based-related-video-recommendations/)).
- **Prediction pipeline:** data becomes a user/item representation, candidate items are identified, and a ranking model orders results. Google's 2016 YouTube paper describes separate candidate-generation and ranking models; this is a historical architecture example, not a claim about every current YouTube component ([source](https://research.google/pubs/deep-neural-networks-for-youtube-recommendations/)). Our tiny catalog can score every item directly.

| Data type | Examples | Purpose |
| --- | --- | --- |
| Explicit feedback | Likes, dislikes, saved tracks, playlist additions | Express preference |
| Behavioral signals | Plays, repeat listens, skips, listening duration | Infer interest; a skip can also reflect context |
| Content features | Genre, mood, tempo, energy, audio representations | Describe or compare items |
| Context | Activity, session, time | Account for changing needs |
| Taste representation | Explicit profile here; learned user representations in larger systems | Connect user information to item relevance |

These are examples of data a recommender may use, not a claim that every platform uses every field. This CSV has song attributes only: no listener histories, likes, skips, or playlists for training collaborative filtering.

## Limitations and Bias

These are anticipated risks; the CLI checks do not establish recommendation quality across listeners:

- Matching the same genre and mood repeatedly can create a filter bubble and suppress discovery.
- Lofi and chill each have three examples, while several genres and moods have one. Some profiles therefore have fewer relevant candidates and less variety.
- Exact category matches can miss related genres and favor whichever labels the catalog uses.
- One energy target and one genre flatten a person's changing or mixed tastes.
- Acoustic preference is simplified to a boolean; lyrics, language, culture, and accessibility needs are absent.
- The starter numeric labels' provenance and annotation reliability are unspecified, and the added labels are synthetic. Eighteen songs cannot establish general recommendation quality.

Future improvements: test diverse and unsupported profiles, compare weight settings, measure genre/artist coverage in top k, add an optional discovery slot, and collect explicit feedback. Evaluate relevance and diversity together. An ID tie-break is reproducible but does not improve fairness by itself.

## Status and Next Steps

Phase 1 research, CSV analysis, architecture, and scoring/ranking design are documented. The local repository tracks the student's GitHub fork as `origin` and CodePath as `upstream`. A separate VS Code workspace file is included.

CSV loading, scoring, ranking, explanations, and the module CLI are implemented. Automated tests cover known score calculations, missing acoustic preference, numerical validation, profile aliases, ranking independently of input order, ties, k boundaries, dataclass consistency, and CLI output. Run them with `python -m pytest` after installing pytest if needed (`python -m pip install pytest`). The core CLI uses only the Python standard library.

Run `python -m src.main` from the project root. Its package-relative import supports module execution, and the CSV path is resolved relative to the project files. Run `python -m src.main --evaluate` for High-Energy Pop, Chill Lofi, Deep Intense Rock, and Conflicting Lofi. Repeat with `python -m src.main --evaluate --recipe energy-focus` to halve genre's weight and double energy's weight while keeping the baseline as the default. Both recipes use the same scoring function and normalized weights.

The completed [model card](model_card.md) records all eight profile/recipe outputs, all six pairwise profile comparisons, the weight experiment, observed limitations, and a reflection draft for the student to personalize. The experiment changes rankings but does not establish improved listener satisfaction. Human listener evaluation remains future work.

See [Phase 1 AI notes](phase1_ai_notes.md) for the assistant's role and suggested follow-up prompts. The student's personal reflection and taste assessment require their own review.

## Advanced Features, Modes, and Diversity

The catalog has five new attributes on all 18 songs. These values are invented for the simulation, including popularity and decade; they are not measurements or real release metadata. Original song fields are preserved. Advanced preferences are optional; absent targets add no weight. Run this example to activate all five:

```console
python -m src.main --advanced --mode mood-first --diversity
python -m src.main --evaluate --advanced --mode energy-focus --diversity
```

`--advanced` adds explicit demonstration targets: popularity 60, decade 2010, duration 210 seconds, tags consisting of the profile's mood plus nostalgic, and instrumentalness 0.9 for the acoustic-preferring example profiles or 0.1 for the others. These are editable simulation choices, not inferred user preferences or a claim that acoustic music is always instrumental. Set the individual dictionary keys in Python to express another taste.

| CSV attribute | Preference key | Similarity calculation |
| --- | --- | --- |
| `popularity` (integer 0?100) | `target_popularity` | `1 - abs(song - target) / 100` |
| `release_decade` (1900?2090, multiple of 10) | `preferred_decade` | `max(0, 1 - abs(song - target) / 100)` |
| `detailed_mood_tags` (semicolon-separated text) | `mood_tags` (tuple or semicolon-separated text) | Fraction of requested unique tags present; trim and case-fold labels |
| `duration_seconds` (positive finite number) | `target_duration_seconds` | `max(0, 1 - abs(song - target) / 300)` |
| `instrumentalness` (0?1) | `target_instrumentalness` | `1 - abs(song - target)` |

Every requested advanced feature receives raw weight 0.10. Add those weights to the active core weights, then divide every contribution by that total. Five advanced preferences without acoustic preference give an active total of 1.40; including acoustic preference gives 1.50. All similarities and the final base score stay between zero and one. A decade gap of 100 years or duration gap of 300 seconds earns zero for that feature. Popularity matches a requested level, so it can reward less popular songs rather than always favoring hits.

`ScoringStrategy` is a frozen weight configuration selected from `SCORING_STRATEGIES`; one shared scorer applies it. This lightweight Strategy pattern avoids duplicated formulas and validation. Modes affect the core weights; advanced feature weights remain the same:

| Mode (`--mode`, also accepted as `--recipe`) | Genre | Mood | Energy | Acousticness |
| --- | --- | --- | --- | --- |
| `genre-first` / `baseline` | 0.40 | 0.30 | 0.20 | 0.10 |
| `mood-first` | 0.20 | 0.50 | 0.20 | 0.10 |
| `energy-focus` | 0.20 | 0.30 | 0.40 | 0.10 |

`--diversity` enables greedy selection. After every choice, each remaining candidate loses 0.12 for each already selected song by its artist and 0.06 for each already selected song in its genre. Select the highest adjusted score, break ties by numeric ID, and repeat. Artist and genre comparisons ignore case and spaces. Penalties use counts, so a third song receives a larger penalty than a second. The Python API accepts `artist_penalty` and `genre_penalty` values from 0 to 1; zero disables that part.

This is a soft preference for variety, not a hard artist quota or a demographic fairness guarantee. A sufficiently relevant repeat can still win. Adjusted scores may be negative and depend on previous choices; they are not probabilities or independent per-song similarities. The reasons show the base score, artist penalty, genre penalty, and adjusted score. The dataclass interface accepts mode and diversity options too; request `diversity=True` in its explanation method to include the same selection penalties.

The CLI uses an ASCII table with rank, song, artist, score, and full wrapped reasons. It uses only the standard library and does not truncate explanations. Baseline mode without advanced preferences or diversity preserves earlier rankings. See [AI interactions](ai_interactions.md) for prompts and verification notes, and the [model card](model_card.md) for advanced behavior and limitations.

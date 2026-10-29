# Music Recommender Simulation

VibeFinder 1.0 is a working CLI-first, content-based music recommender. It loads 18 songs with 15 attributes, scores them against explicit preferences, and returns five ranked songs with reasons. It includes three scoring modes, five optional advanced features, and an artist/genre diversity penalty.

## Run the Project

Use Python 3.10 or newer. From the project root:

```console
python -m src.main
python -m src.main --evaluate
python -m src.main --evaluate --mode energy-focus
python -m src.main --advanced --mode mood-first --diversity
```

The CLI uses only Python's standard library. To run the tests, install pytest if necessary:

```console
python -m pip install pytest
python -m pytest -q
```

`--evaluate` runs High-Energy Pop, Chill Lofi, Deep Intense Rock, and Conflicting Lofi. `--advanced` supplies example targets for all five added features. `--diversity` enables repetition penalties. `--mode` selects a strategy; `--recipe` remains an alias. Default settings reproduce the baseline evaluation.

## Rubric Evidence

This table maps the supplied 21-point required rubric and 8 bonus points to reviewable evidence. It is an evidence guide, not an awarded grade.

| Rubric category | Available points | Evidence |
| --- | --- | --- |
| Explain real recommendation systems | 3 | [How The System Works](#how-the-system-works) distinguishes data, preferences, scoring, and selection. |
| Structured song dataset | 3 | [songs.csv](data/songs.csv): 18 complete records, 15 attributes; [load_songs](src/recommender.py) parses and validates them. |
| Scoring reflects preferences | 3 | [Algorithm Recipe](#algorithm-recipe), shared `score_song`, and [scoring tests](tests/test_cli_recommender.py) cover known scores, feature closeness, and invalid input. |
| Sorted recommendations | 3 | `recommend_songs` in [recommender.py](src/recommender.py) ranks all songs and returns five; ties use numeric IDs. |
| Explanations for recommended songs | 3 | [Sample Recommendation Output](#sample-recommendation-output) shows five songs with actual contribution reasons in a fenced text block. |
| Multiple profiles and experiments | 3 | [Model card evaluation](model_card.md#7-evaluation) includes four profiles, eight captured runs, all six profile-pair comparisons, and the energy-weight experiment. |
| Completed model card | 3 | [Model card](model_card.md) covers purpose, data, plain-language rules, observed limitations, and improvement ideas. |
| Five additional attributes via AI | +2 | [Advanced features](#advanced-features-modes-and-diversity), [CSV](data/songs.csv), [feature tests](tests/test_advanced.py), and [workflow notes](ai_interactions.md#agentic-workflow-sf8). |
| Diversity or fairness component | +2 | Optional repetition penalties in `recommend_songs`; [model card evidence](model_card.md#10-advanced-extension) explains variety gains and limits. |
| Multiple modes and design pattern | +2 | `ScoringStrategy`, CLI `--mode`, and [Strategy pattern notes](ai_interactions.md#design-pattern-sf10). |
| Visual summary with reasons | +2 | ASCII CLI tables wrap full explanations; see the sample below and advanced output in the model card. |

## How The System Works

Real-world recommenders can use song features such as genre, mood, and tempo, plus user feedback such as plays, skips, and likes. Content-based filtering compares item features with a listener's preferences. Collaborative filtering finds patterns across listeners' behavior. A recommendation is a prediction of relevance, not proof that someone will enjoy a song.

This project uses content-based rules. It has no listener history, other-user behavior, trained model, or audio recordings. Its three inputs and steps are distinct:

| Part | What it contains or does |
| --- | --- |
| Song data | The CSV describes each song independently of any listener. |
| User preferences | A dictionary supplies the desired genre, mood, energy, and optional feature targets. |
| Scoring | `score_song` compares one song with those preferences and returns a numeric score plus a list of reasons. |
| Ranking and selection | `recommend_songs` scores the whole catalog, orders the results, optionally penalizes repetition, and selects the top k. |

```text
CSV song data + user preferences
  -> load and validate typed records
  -> compare every song with the preferences
  -> calculate scores and reasons
  -> rank by score, optionally accounting for prior selections
  -> return top k songs with explanations
```

### Song Data and User Profile

The CSV preserves the original ten songs and adds eight fictional tracks in folk, ska, country, soul, hip hop, classical, reggae, and house. All 18 rows now have 15 fields. The starter numeric labels have no documented measurement method; added song values and all five advanced attributes are synthetic simulation data.

| Fields | Role |
| --- | --- |
| `id`, `title`, `artist` | Identification and display; artist also supports the diversity penalty. |
| `genre`, `mood` | Exact categorical matches after trimming and case-folding. |
| `energy`, `acousticness` | Core numerical preferences, each on a 0-1 scale. |
| `tempo_bpm`, `valence`, `danceability` | Loaded and validated; retained for future scoring experiments. |
| `popularity`, `release_decade`, `detailed_mood_tags`, `duration_seconds`, `instrumentalness` | Optional advanced scoring attributes, detailed below. |

The loader uses `csv.DictReader`, converts numerical fields, and rejects incorrect headers, incomplete rows, duplicate IDs, and invalid feature ranges. The catalog spans 15 genres and 14 moods; lofi and chill each have three examples, while rock has one. There is no exact `sad` mood label.

A calm-study example profile is:

```python
user_profile = {
    "favorite_genre": "lofi",
    "favorite_mood": "chill",
    "target_energy": 0.40,
    "likes_acoustic": True,
}
```

Both `UserProfile(**user_profile)` and the functional scorer accept this profile. Dictionaries may instead use `genre`, `mood`, and `energy`; those shorter keys take precedence if both spellings are supplied. Missing or `None` acoustic preference omits that component; `False` requests lower acousticness.

This profile distinguishes calm lofi from intense rock, but only describes one listening session. It does not represent all of a person's taste. Genre, mood, and acoustic preference are separate signals; acoustic music is not necessarily instrumental. Multiple genres or activity-specific profiles would capture more variety.

### Algorithm Recipe

The baseline is also called genre-first. Weights are design choices, not learned parameters:

| Component | Similarity | Raw weight |
| --- | --- | --- |
| Genre | 1 for an exact match, otherwise 0 | 0.40 |
| Mood | 1 for an exact match, otherwise 0 | 0.30 |
| Energy | `1 - abs(song.energy - target_energy)` | 0.20 |
| Acousticness | `song.acousticness` if preferred; otherwise `1 - song.acousticness` | 0.10 |

Multiply each active similarity by its weight, add the contributions, and divide by the sum of active weights. With all core preferences present, the denominator is 1.00. Without acoustic preference, it is 0.90. Requested advanced attributes add their own weights to this denominator. Base scores are between 0 and 1 and express similarity, not enjoyment probabilities.

Energy rewards closeness, not magnitude. For a target of 0.40, energies 0.35 and 0.45 both earn similarity 0.95. For the study profile, Library Rain scores `0.40 + 0.30 + 0.20*0.95 + 0.10*0.86 = 0.976`; Storm Runner scores `0 + 0 + 0.20*0.49 + 0.10*0.10 = 0.108`. The weights therefore separate chill lofi from intense rock as intended.

Genre slightly outweighs mood in the baseline. Mood-first increases mood's importance, and energy-focus increases energy's importance; the mode table below gives the exact weights. Related labels such as pop and indie pop remain different categories. This is a known limitation.

### Ranking and Explanations

Without diversity, sort by descending full-precision score, break ties by ascending numeric song ID, and take the first k. Return an empty list for k <= 0; return all available songs if k is larger than the catalog. `sorted()` creates a new list; `.sort()` modifies a list in place and returns `None`. The recommender uses `sorted()` and preserves input data.

`score_song` returns `(score, reasons)`, with reasons as a list. `recommend_songs` returns `(song_dictionary, score, explanation)` tuples, joining the reasons for display. The dataclass interface shares the same logic. Round only for display; individually rounded contributions may not sum exactly to the displayed final score. With diversity on, the returned score includes the selection-dependent penalties explained below.

## Sample Recommendation Output

Actual output from `python -m src.main`. Sunrise City matches pop and happy, Gym Hero matches pop, and Rooftop Lights matches happy. Gym Hero's genre advantage outweighs its worse energy match. The other two songs match neither label and rank by energy closeness. No acoustic target is supplied, so the active core weights total 0.90.

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

## Advanced Features, Modes, and Diversity

The catalog has five new attributes on all 18 songs. These values are invented for the simulation, including popularity and decade; they are not measurements or real release metadata. Original song fields are preserved. Advanced preferences are optional; absent targets add no weight. Run this example to activate all five:

```console
python -m src.main --advanced --mode mood-first --diversity
python -m src.main --evaluate --advanced --mode energy-focus --diversity
```

`--advanced` adds explicit demonstration targets: popularity 60, decade 2010, duration 210 seconds, tags consisting of the profile's mood plus nostalgic, and instrumentalness 0.9 for the acoustic-preferring example profiles or 0.1 for the others. These are editable simulation choices, not inferred user preferences or a claim that acoustic music is always instrumental. Set the individual dictionary keys in Python to express another taste.

| CSV attribute | Preference key | Similarity calculation |
| --- | --- | --- |
| `popularity` (integer 0-100) | `target_popularity` | `1 - abs(song - target) / 100` |
| `release_decade` (1900-2090, multiple of 10) | `preferred_decade` | `max(0, 1 - abs(song - target) / 100)` |
| `detailed_mood_tags` (semicolon-separated text) | `mood_tags` (tuple or semicolon-separated text) | Fraction of requested unique tags present; trim and case-fold labels |
| `duration_seconds` (positive finite number) | `target_duration_seconds` | `max(0, 1 - abs(song - target) / 300)` |
| `instrumentalness` (0-1) | `target_instrumentalness` | `1 - abs(song - target)` |

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

## Evaluation and Limitations

The [model card](model_card.md#7-evaluation) contains the four profiles' actual top-five outputs, explanations, all six profile-pair comparisons, and the experiment that halves genre and doubles energy. The advanced section also demonstrates diversity and explains its limits. Tests cover known scores, unknown labels, boundary values, all scoring modes, optional features, diversity, and captured CLI output.

The small, uneven catalog limits discovery. Exact labels miss synonyms such as sad and melancholic, and a strong genre preference can overpower a conflicting energy target. Synthetic popularity and decade values cannot establish real trends. No listening study has measured relevance or satisfaction. Improvements include broader catalog coverage, related mood labels, listener feedback, and warnings for weak matches.

See [AI interactions](ai_interactions.md) for reproducible prompts, the generated changes, and verification notes. [Phase 1 notes](phase1_ai_notes.md) preserve the earlier planning history. The personal reflection in the model card is a draft for the student to review and personalize.

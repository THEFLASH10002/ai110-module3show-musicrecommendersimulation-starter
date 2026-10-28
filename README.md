# Music Recommender Simulation

## Project Summary

Phase 1 designs an explainable, content-based music recommender using the supplied 10-song catalog. The proposed Python architecture separates CSV loading, song and user data, scoring, ranking, and explanations. The recipe below is a design specification; the starter Python functions still contain TODOs for later implementation phases.

## How The System Works

Real recommendation systems turn listening behavior and content information into predictions of what someone might enjoy. Collaborative filtering uses patterns across listeners, while content-based filtering compares attributes of songs with a listener's preferences. Spotify describes combining listening history with track relationships and audio attributes, and updating taste representations from listening, skips, and saves ([Spotify Engineering](https://engineering.atspotify.com/2023/4/humans-machines-a-look-behind-spotifys-algotorial-playlists)). This simulation will prioritize matching genre and mood, closeness to a preferred energy level, and acoustic preference. It will assign each song a transparent weighted score, sort the catalog, and return the top k songs with explanations. Its scores represent similarity, not probabilities that a person will like a song.

### Song and UserProfile features

The existing `Song` dataclass stores every CSV field:

| Field | Role |
| --- | --- |
| `id`, `title`, `artist` | Identification and display; no score contribution |
| `genre` | Exact match against `favorite_genre` |
| `mood` | Exact match against `favorite_mood` |
| `energy` | Numerical closeness to `target_energy` |
| `acousticness` | Match to `likes_acoustic` |
| `tempo_bpm`, `valence`, `danceability` | Retained for future scoring experiments |

The existing `UserProfile` stores `favorite_genre: str`, `favorite_mood: str`, `target_energy: float` (0 to 1), and `likes_acoustic: bool`. It expresses explicit preferences; it does not infer taste from listening history. Keep these interfaces compatible with the starter tests. The functional runner currently uses `genre`, `mood`, and `energy` dictionary keys; implementation should adapt those to the same recipe, with missing acoustic preference meaning no acoustic contribution.

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

### Proposed modular flow

`data/songs.csv -> load_songs -> Song records + UserProfile -> score_song -> rank -> top k + reasons`

Use one scoring recipe shared by the functional and object-oriented interfaces. `Recommender.recommend` should rank songs; `explain_recommendation` should describe the same contributions used to score them. An explanation should identify actual matches and distances rather than claim certainty about enjoyment.

## Phase 1 Data Analysis

Audited the original CSV without changing it: 10 rows, 10 unique IDs, 11 columns, and no missing cells.

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

These are anticipated risks, not measured outcomes from the unfinished implementation:

- Matching the same genre and mood repeatedly can create a filter bubble and suppress discovery.
- Lofi and chill each have three examples, while several genres and moods have one. Some profiles therefore have fewer relevant candidates and less variety.
- Exact category matches can miss related genres and favor whichever labels the catalog uses.
- One energy target and one genre flatten a person's changing or mixed tastes.
- Acoustic preference is simplified to a boolean; lyrics, language, culture, and accessibility needs are absent.
- The numeric labels' provenance and annotation reliability are unspecified. Ten songs cannot establish general recommendation quality.

Future improvements: test diverse and unsupported profiles, compare weight settings, measure genre/artist coverage in top k, add an optional discovery slot, and collect explicit feedback. Evaluate relevance and diversity together. An ID tie-break is reproducible but does not improve fairness by itself.

## Status and Next Steps

Phase 1 research, CSV analysis, architecture, and scoring/ranking design are documented. The local repository tracks the student's GitHub fork as `origin` and CodePath as `upstream`. A separate VS Code workspace file is included.

The Python implementation, executable sample output, weight experiments, and evaluated Model Card belong to later phases and remain unfinished in the starter. The starter tests are too weak to establish implementation correctness: returning the original list and a placeholder explanation can satisfy them. Do not present such a pass as evidence of a working recommender.

Before implementation, also fix the starter's `src/main.py` import (`from recommender ...`) to support its advertised `python -m src.main` invocation. No dependency installation is needed for this documentation phase.

See [Phase 1 AI notes](phase1_ai_notes.md) for the assistant's role and suggested follow-up prompts. The student's personal reflection and taste assessment require their own review.

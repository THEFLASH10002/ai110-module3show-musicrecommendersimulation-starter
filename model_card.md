# Model Card: VibeFinder 1.0

## 1. Model Name

**VibeFinder 1.0: Explainable Music Recommender**

## 2. Goal / Task and Intended Use

Suggest five songs that resemble a listener's stated genre, mood, energy, and optional acoustic preference. This is a classroom simulation for exploring ranking rules. It assumes the profile describes one listening session. Scores measure similarity under chosen rules, not the chance that someone will enjoy a song.

Non-intended use: commercial personalization, claims about real listener satisfaction, or judging a person's emotions. This system has no listening history and does not learn from plays or skips.

## 3. How the Model Works / Algorithm Summary

The baseline gives genre 40% of the score, mood 30%, energy closeness 20%, and acoustic preference 10%. Genre and mood match only when their labels are the same after ignoring case and surrounding spaces. A song earns more energy points when its energy is closer to the requested level. Acoustic preference rewards either higher or lower acousticness.

If acoustic preference is absent, that part is omitted and the remaining weights are scaled to total 100%. Every song receives a score and a list of reasons. The system sorts full scores from highest to lowest, breaks ties with the smaller numeric song ID, and returns five songs. It can return fewer if the catalog is smaller. The starter placeholders were replaced with CSV loading, validation, shared scoring, ranking, and a working CLI.

The optional **energy-focus** experiment halves genre's weight to 20% and doubles energy's weight to 40%. Mood stays at 30% and acousticness at 10%. Both recipes total 100%, or 90% before scaling when acoustic preference is absent. The baseline remains the default.

## 4. Data Used

The original catalog schema had 10 fields: ID, title, artist, genre, mood, energy, tempo, valence, danceability, and acousticness. The original 10 songs were kept and eight fictional songs were added. The added numeric labels are synthetic examples, not audio measurements. There are no recordings or listener ratings in this project. The advanced extension now stores 18 songs with 15 fields, adding popularity, release decade, detailed mood tags, duration, and instrumentalness. All five added values are synthetic on every row.

The catalog covers 15 genres and 14 moods. Lofi and chill each occur three times; pop and happy each occur twice. Rock has only one example. New genres include folk, ska, country, soul, hip hop, classical, reggae, and house. There is no exact mood label `sad`, though `melancholic` is present. Tempo, valence, and danceability are loaded but do not affect the current score. Lyrics, language, context, and personal associations are missing.

## 5. Strengths

The three ordinary profiles have different first-place songs, so one song does not dominate every list. Their winners fit the catalog descriptions: upbeat pop for High-Energy Pop, quiet lofi for Chill Lofi, and intense rock for Deep Intense Rock. This is a check against the supplied labels, not a listening test or a statement about the student's taste. Clear reasons make it possible to trace a surprising result back to its score.

## 6. Limitations and Bias

The conflicting profile asks for lofi, a sad mood, and energy 0.90, but its baseline winner is Focus Flow at energy 0.40 because genre outweighs the energy gap. No song has the exact label `sad`, so mood contributes nothing for this profile even though a `melancholic` song exists. The catalog offers three lofi tracks but only one rock track, giving different listeners unequal choice within their preferred style. Repeated genre matching can create a filter bubble, and the energy-focus experiment still puts three low-energy lofi songs first for the conflicting profile. Since the system always fills five slots when enough songs exist, even weak matches can appear without a minimum relevance threshold.

## 7. Evaluation

### Evaluation process and tested profiles

The four dictionaries live in `src/main.py` as `EVALUATION_PROFILES`. All 18 songs were scored for each profile with both recipes. The data, profiles, mood weight, and acoustic weight stayed fixed; only genre and energy weights changed. The runs below can be reproduced from the project root:

```console
python -m src.main --evaluate
python -m src.main --evaluate --recipe energy-focus
python -m pytest -q
```

| Profile | Genre | Mood | Target energy | Acoustic preference |
| --- | --- | --- | --- | --- |
| High-Energy Pop | pop | happy | 0.80 | not supplied |
| Chill Lofi | lofi | chill | 0.40 | higher |
| Deep Intense Rock | rock | intense | 0.95 | lower |
| Conflicting Lofi | lofi | sad | 0.90 | higher |

Conflicting Lofi is an adversarial case because its desired energy is far above all three lofi tracks and its mood is absent from the catalog. Additional automated cases cover unknown genre and mood, energy targets at 0 and 1, missing acoustic preference, and invalid numeric inputs. These checks establish scoring behavior, not real-world recommendation accuracy.

### Accuracy check and one explained winner

For Chill Lofi, Library Rain ranks first at 0.976. It earns 0.400 for lofi, 0.300 for chill, 0.190 for being just 0.05 from the energy target, and 0.086 for acousticness. Midnight Coding has a closer energy value, but Library Rain's higher acousticness more than makes up the difference. This fits the stated preference for calm, acoustic study music based on the catalog labels. No human listening feedback was collected.

Gym Hero ranks second for happy-pop listeners even though its mood is intense. In the baseline, its pop match is worth about 0.444 after normalization, while Rooftop Lights earns about 0.333 for matching happy. Gym Hero's genre advantage outweighs its worse energy distance. This explains the result without assuming the listener actually likes intense music.

### Pairwise comparisons of all tested profiles

- **High-Energy Pop vs Chill Lofi:** Sunrise City leads the pop list; Library Rain leads the lofi list. There are no shared songs in their baseline top fives. Genre, mood, energy target, and acoustic preference all help separate these sessions.
- **High-Energy Pop vs Deep Intense Rock:** Storm Runner replaces Sunrise City as the winner when rock and intense are requested. Gym Hero is second in both lists: it matches pop in one session and intense in the other. Sunrise City also stays in the rock top five because it is fairly energetic and has low acousticness.
- **High-Energy Pop vs Conflicting Lofi:** The edge case replaces the pop winner with Focus Flow. Brass Horizon is their only shared top-five song, helped by its high energy in both sessions. The edge case's low-energy winner shows how a genre match can overpower conflicting energy.
- **Chill Lofi vs Deep Intense Rock:** Their baseline top fives share no songs. Low energy and higher acousticness favor Library Rain; high energy, intense mood, and lower acousticness favor Storm Runner. This is the clearest separation of the two listening contexts.
- **Chill Lofi vs Conflicting Lofi:** Both lists start with the same three lofi songs, but Focus Flow moves from third to first. The missing sad label removes Library Rain's chill advantage, while the higher energy target changes the numerical contributions. The remaining two songs switch from quiet ambient/jazz to energetic ska/rock.
- **Deep Intense Rock vs Conflicting Lofi:** Storm Runner leads rock but is only fifth in the edge case, despite being very close to its energy target. The rock profile rewards its genre, intense mood, and low acousticness. The edge case instead rewards lofi and higher acousticness, so only Storm Runner is shared between these top fives.

### Weight-shift experiment and surprises

| Profile | Baseline top five | Energy-focus top five |
| --- | --- | --- |
| High-Energy Pop | Sunrise City; Gym Hero; Rooftop Lights; Night Drive Loop; Brass Horizon | Sunrise City; Rooftop Lights; Gym Hero; Night Drive Loop; Brass Horizon |
| Chill Lofi | Library Rain; Midnight Coding; Focus Flow; Spacewalk Thoughts; Coffee Shop Stories | Library Rain; Midnight Coding; Spacewalk Thoughts; Focus Flow; Coffee Shop Stories |
| Deep Intense Rock | Storm Runner; Gym Hero; Afterglow Circuit; Concrete Anthem; Sunrise City | Storm Runner; Gym Hero; Afterglow Circuit; Concrete Anthem; Brass Horizon |
| Conflicting Lofi | Focus Flow; Library Rain; Midnight Coding; Brass Horizon; Storm Runner | Midnight Coding; Focus Flow; Library Rain; Brass Horizon; Storm Runner |

Rooftop Lights moves above Gym Hero when genre loses weight. Its happy mood and closer energy now outweigh Gym Hero's pop label. For a listener who cares strongly about happy music, this seems more consistent with the stated goal, but it is not measured improvement. Spacewalk Thoughts also overtakes Focus Flow because matching chill becomes more valuable than matching lofi.

The ordinary profiles keep their first-place songs. The edge case changes its winner to Midnight Coding, whose energy is the highest of the three lofi tracks, but that value is still only 0.42. Its first three choices remain lofi. This was the main surprise: doubling energy changes rankings without solving sparse data or missing mood labels. Larger scores under the new recipe do not mean greater accuracy, because the scoring scale's meaning has changed. Keep the baseline as the default until listener feedback supports another choice.

### AI evaluation prompts and review

This evaluation was performed in the current chat. A separate chat session cannot be opened by the assistant and has not been created. To repeat the requested workflow, open **System Evaluation** and attach `src/recommender.py`, `src/main.py`, and `data/songs.csv`.

> Suggest adversarial user profiles for these files. Include conflicting genre/energy preferences, an unavailable mood, unknown categories, and energy boundaries. Predict failure modes without claiming that output scores measure enjoyment.

> Explain why Library Rain ranks above Midnight Coding for the Chill Lofi profile using the current baseline weights. Show the individual contributions and check the total.

> Halve genre's weight from 0.40 to 0.20 and double energy's weight from 0.20 to 0.40. Keep mood at 0.30 and acousticness at 0.10. Verify that the weights sum to 1.0, renormalize when acoustic preference is absent, and compare the same four profiles before and after.

> Review recommender.py and songs.csv for filter bubbles and unequal catalog coverage. Explain how an unavailable mood such as sad and a large energy gap affect the actual recommendations.

### Captured terminal output

The earlier baseline evaluation is reproduced below using the current table display. Advanced preferences and diversity are off, so its scores and rankings are unchanged.

```text
Loaded songs: 18
=== High-Energy Pop | baseline ===
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

```text
Loaded songs: 18
=== Chill Lofi | baseline ===
Profile: genre=lofi, mood=chill, target energy=0.40
Acoustic preference: True
Mode: baseline | Diversity: off

Top 5 recommendations (adjusted scores when diversity is on):
+------+----------------------+-----------------+---------+--------------------------------------------------------------------+
| Rank | Song                 | Artist          | Score   | Reasons                                                            |
+------+----------------------+-----------------+---------+--------------------------------------------------------------------+
| 1    | Library Rain         | Paper Lanterns  | 0.976   | genre match (+0.400); mood match (+0.300); energy distance 0.050   |
|      |                      |                 |         | (+0.190); higher acousticness similarity 0.860 (+0.086)            |
+------+----------------------+-----------------+---------+--------------------------------------------------------------------+
| 2    | Midnight Coding      | LoRoom          | 0.967   | genre match (+0.400); mood match (+0.300); energy distance 0.020   |
|      |                      |                 |         | (+0.196); higher acousticness similarity 0.710 (+0.071)            |
+------+----------------------+-----------------+---------+--------------------------------------------------------------------+
| 3    | Focus Flow           | LoRoom          | 0.678   | genre match (+0.400); mood mismatch (+0.000); energy distance      |
|      |                      |                 |         | 0.000 (+0.200); higher acousticness similarity 0.780 (+0.078)      |
+------+----------------------+-----------------+---------+--------------------------------------------------------------------+
| 4    | Spacewalk Thoughts   | Orbit Bloom     | 0.568   | genre mismatch (+0.000); mood match (+0.300); energy distance      |
|      |                      |                 |         | 0.120 (+0.176); higher acousticness similarity 0.920 (+0.092)      |
+------+----------------------+-----------------+---------+--------------------------------------------------------------------+
| 5    | Coffee Shop Stories  | Slow Stereo     | 0.283   | genre mismatch (+0.000); mood mismatch (+0.000); energy distance   |
|      |                      |                 |         | 0.030 (+0.194); higher acousticness similarity 0.890 (+0.089)      |
+------+----------------------+-----------------+---------+--------------------------------------------------------------------+
```

```text
Loaded songs: 18
=== Deep Intense Rock | baseline ===
Profile: genre=rock, mood=intense, target energy=0.95
Acoustic preference: False
Mode: baseline | Diversity: off

Top 5 recommendations (adjusted scores when diversity is on):
+------+----------------------+-----------------+---------+--------------------------------------------------------------------+
| Rank | Song                 | Artist          | Score   | Reasons                                                            |
+------+----------------------+-----------------+---------+--------------------------------------------------------------------+
| 1    | Storm Runner         | Voltline        | 0.982   | genre match (+0.400); mood match (+0.300); energy distance 0.040   |
|      |                      |                 |         | (+0.192); lower acousticness similarity 0.900 (+0.090)             |
+------+----------------------+-----------------+---------+--------------------------------------------------------------------+
| 2    | Gym Hero             | Max Pulse       | 0.591   | genre mismatch (+0.000); mood match (+0.300); energy distance      |
|      |                      |                 |         | 0.020 (+0.196); lower acousticness similarity 0.950 (+0.095)       |
+------+----------------------+-----------------+---------+--------------------------------------------------------------------+
| 3    | Afterglow Circuit    | Prism Current   | 0.284   | genre mismatch (+0.000); mood mismatch (+0.000); energy distance   |
|      |                      |                 |         | 0.060 (+0.188); lower acousticness similarity 0.960 (+0.096)       |
+------+----------------------+-----------------+---------+--------------------------------------------------------------------+
| 4    | Concrete Anthem      | Verse Atlas     | 0.277   | genre mismatch (+0.000); mood mismatch (+0.000); energy distance   |
|      |                      |                 |         | 0.070 (+0.186); lower acousticness similarity 0.910 (+0.091)       |
+------+----------------------+-----------------+---------+--------------------------------------------------------------------+
| 5    | Sunrise City         | Neon Echo       | 0.256   | genre mismatch (+0.000); mood mismatch (+0.000); energy distance   |
|      |                      |                 |         | 0.130 (+0.174); lower acousticness similarity 0.820 (+0.082)       |
+------+----------------------+-----------------+---------+--------------------------------------------------------------------+
```

```text
Loaded songs: 18
=== Conflicting Lofi | baseline ===
Profile: genre=lofi, mood=sad, target energy=0.90
Acoustic preference: True
Mode: baseline | Diversity: off

Top 5 recommendations (adjusted scores when diversity is on):
+------+----------------------+-----------------+---------+--------------------------------------------------------------------+
| Rank | Song                 | Artist          | Score   | Reasons                                                            |
+------+----------------------+-----------------+---------+--------------------------------------------------------------------+
| 1    | Focus Flow           | LoRoom          | 0.578   | genre match (+0.400); mood mismatch (+0.000); energy distance      |
|      |                      |                 |         | 0.500 (+0.100); higher acousticness similarity 0.780 (+0.078)      |
+------+----------------------+-----------------+---------+--------------------------------------------------------------------+
| 2    | Library Rain         | Paper Lanterns  | 0.576   | genre match (+0.400); mood mismatch (+0.000); energy distance      |
|      |                      |                 |         | 0.550 (+0.090); higher acousticness similarity 0.860 (+0.086)      |
+------+----------------------+-----------------+---------+--------------------------------------------------------------------+
| 3    | Midnight Coding      | LoRoom          | 0.575   | genre match (+0.400); mood mismatch (+0.000); energy distance      |
|      |                      |                 |         | 0.480 (+0.104); higher acousticness similarity 0.710 (+0.071)      |
+------+----------------------+-----------------+---------+--------------------------------------------------------------------+
| 4    | Brass Horizon        | Copper Steps    | 0.220   | genre mismatch (+0.000); mood mismatch (+0.000); energy distance   |
|      |                      |                 |         | 0.040 (+0.192); higher acousticness similarity 0.280 (+0.028)      |
+------+----------------------+-----------------+---------+--------------------------------------------------------------------+
| 5    | Storm Runner         | Voltline        | 0.208   | genre mismatch (+0.000); mood mismatch (+0.000); energy distance   |
|      |                      |                 |         | 0.010 (+0.198); higher acousticness similarity 0.100 (+0.010)      |
+------+----------------------+-----------------+---------+--------------------------------------------------------------------+
```

```text
Loaded songs: 18
=== High-Energy Pop | energy-focus ===
Profile: genre=pop, mood=happy, target energy=0.80
Mode: energy-focus | Diversity: off

Top 5 recommendations (adjusted scores when diversity is on):
+------+----------------------+-----------------+---------+--------------------------------------------------------------------+
| Rank | Song                 | Artist          | Score   | Reasons                                                            |
+------+----------------------+-----------------+---------+--------------------------------------------------------------------+
| 1    | Sunrise City         | Neon Echo       | 0.991   | genre match (+0.222); mood match (+0.333); energy distance 0.020   |
|      |                      |                 |         | (+0.436); acousticness omitted; active weights normalized by 0.90  |
+------+----------------------+-----------------+---------+--------------------------------------------------------------------+
| 2    | Rooftop Lights       | Indigo Parade   | 0.760   | genre mismatch (+0.000); mood match (+0.333); energy distance      |
|      |                      |                 |         | 0.040 (+0.427); acousticness omitted; active weights normalized by |
|      |                      |                 |         | 0.90                                                               |
+------+----------------------+-----------------+---------+--------------------------------------------------------------------+
| 3    | Gym Hero             | Max Pulse       | 0.609   | genre match (+0.222); mood mismatch (+0.000); energy distance      |
|      |                      |                 |         | 0.130 (+0.387); acousticness omitted; active weights normalized by |
|      |                      |                 |         | 0.90                                                               |
+------+----------------------+-----------------+---------+--------------------------------------------------------------------+
| 4    | Night Drive Loop     | Neon Echo       | 0.422   | genre mismatch (+0.000); mood mismatch (+0.000); energy distance   |
|      |                      |                 |         | 0.050 (+0.422); acousticness omitted; active weights normalized by |
|      |                      |                 |         | 0.90                                                               |
+------+----------------------+-----------------+---------+--------------------------------------------------------------------+
| 5    | Brass Horizon        | Copper Steps    | 0.418   | genre mismatch (+0.000); mood mismatch (+0.000); energy distance   |
|      |                      |                 |         | 0.060 (+0.418); acousticness omitted; active weights normalized by |
|      |                      |                 |         | 0.90                                                               |
+------+----------------------+-----------------+---------+--------------------------------------------------------------------+
```

```text
Loaded songs: 18
=== Chill Lofi | energy-focus ===
Profile: genre=lofi, mood=chill, target energy=0.40
Acoustic preference: True
Mode: energy-focus | Diversity: off

Top 5 recommendations (adjusted scores when diversity is on):
+------+----------------------+-----------------+---------+--------------------------------------------------------------------+
| Rank | Song                 | Artist          | Score   | Reasons                                                            |
+------+----------------------+-----------------+---------+--------------------------------------------------------------------+
| 1    | Library Rain         | Paper Lanterns  | 0.966   | genre match (+0.200); mood match (+0.300); energy distance 0.050   |
|      |                      |                 |         | (+0.380); higher acousticness similarity 0.860 (+0.086)            |
+------+----------------------+-----------------+---------+--------------------------------------------------------------------+
| 2    | Midnight Coding      | LoRoom          | 0.963   | genre match (+0.200); mood match (+0.300); energy distance 0.020   |
|      |                      |                 |         | (+0.392); higher acousticness similarity 0.710 (+0.071)            |
+------+----------------------+-----------------+---------+--------------------------------------------------------------------+
| 3    | Spacewalk Thoughts   | Orbit Bloom     | 0.744   | genre mismatch (+0.000); mood match (+0.300); energy distance      |
|      |                      |                 |         | 0.120 (+0.352); higher acousticness similarity 0.920 (+0.092)      |
+------+----------------------+-----------------+---------+--------------------------------------------------------------------+
| 4    | Focus Flow           | LoRoom          | 0.678   | genre match (+0.200); mood mismatch (+0.000); energy distance      |
|      |                      |                 |         | 0.000 (+0.400); higher acousticness similarity 0.780 (+0.078)      |
+------+----------------------+-----------------+---------+--------------------------------------------------------------------+
| 5    | Coffee Shop Stories  | Slow Stereo     | 0.477   | genre mismatch (+0.000); mood mismatch (+0.000); energy distance   |
|      |                      |                 |         | 0.030 (+0.388); higher acousticness similarity 0.890 (+0.089)      |
+------+----------------------+-----------------+---------+--------------------------------------------------------------------+
```

```text
Loaded songs: 18
=== Deep Intense Rock | energy-focus ===
Profile: genre=rock, mood=intense, target energy=0.95
Acoustic preference: False
Mode: energy-focus | Diversity: off

Top 5 recommendations (adjusted scores when diversity is on):
+------+----------------------+-----------------+---------+--------------------------------------------------------------------+
| Rank | Song                 | Artist          | Score   | Reasons                                                            |
+------+----------------------+-----------------+---------+--------------------------------------------------------------------+
| 1    | Storm Runner         | Voltline        | 0.974   | genre match (+0.200); mood match (+0.300); energy distance 0.040   |
|      |                      |                 |         | (+0.384); lower acousticness similarity 0.900 (+0.090)             |
+------+----------------------+-----------------+---------+--------------------------------------------------------------------+
| 2    | Gym Hero             | Max Pulse       | 0.787   | genre mismatch (+0.000); mood match (+0.300); energy distance      |
|      |                      |                 |         | 0.020 (+0.392); lower acousticness similarity 0.950 (+0.095)       |
+------+----------------------+-----------------+---------+--------------------------------------------------------------------+
| 3    | Afterglow Circuit    | Prism Current   | 0.472   | genre mismatch (+0.000); mood mismatch (+0.000); energy distance   |
|      |                      |                 |         | 0.060 (+0.376); lower acousticness similarity 0.960 (+0.096)       |
+------+----------------------+-----------------+---------+--------------------------------------------------------------------+
| 4    | Concrete Anthem      | Verse Atlas     | 0.463   | genre mismatch (+0.000); mood mismatch (+0.000); energy distance   |
|      |                      |                 |         | 0.070 (+0.372); lower acousticness similarity 0.910 (+0.091)       |
+------+----------------------+-----------------+---------+--------------------------------------------------------------------+
| 5    | Brass Horizon        | Copper Steps    | 0.436   | genre mismatch (+0.000); mood mismatch (+0.000); energy distance   |
|      |                      |                 |         | 0.090 (+0.364); lower acousticness similarity 0.720 (+0.072)       |
+------+----------------------+-----------------+---------+--------------------------------------------------------------------+
```

```text
Loaded songs: 18
=== Conflicting Lofi | energy-focus ===
Profile: genre=lofi, mood=sad, target energy=0.90
Acoustic preference: True
Mode: energy-focus | Diversity: off

Top 5 recommendations (adjusted scores when diversity is on):
+------+----------------------+-----------------+---------+--------------------------------------------------------------------+
| Rank | Song                 | Artist          | Score   | Reasons                                                            |
+------+----------------------+-----------------+---------+--------------------------------------------------------------------+
| 1    | Midnight Coding      | LoRoom          | 0.479   | genre match (+0.200); mood mismatch (+0.000); energy distance      |
|      |                      |                 |         | 0.480 (+0.208); higher acousticness similarity 0.710 (+0.071)      |
+------+----------------------+-----------------+---------+--------------------------------------------------------------------+
| 2    | Focus Flow           | LoRoom          | 0.478   | genre match (+0.200); mood mismatch (+0.000); energy distance      |
|      |                      |                 |         | 0.500 (+0.200); higher acousticness similarity 0.780 (+0.078)      |
+------+----------------------+-----------------+---------+--------------------------------------------------------------------+
| 3    | Library Rain         | Paper Lanterns  | 0.466   | genre match (+0.200); mood mismatch (+0.000); energy distance      |
|      |                      |                 |         | 0.550 (+0.180); higher acousticness similarity 0.860 (+0.086)      |
+------+----------------------+-----------------+---------+--------------------------------------------------------------------+
| 4    | Brass Horizon        | Copper Steps    | 0.412   | genre mismatch (+0.000); mood mismatch (+0.000); energy distance   |
|      |                      |                 |         | 0.040 (+0.384); higher acousticness similarity 0.280 (+0.028)      |
+------+----------------------+-----------------+---------+--------------------------------------------------------------------+
| 5    | Storm Runner         | Voltline        | 0.406   | genre mismatch (+0.000); mood mismatch (+0.000); energy distance   |
|      |                      |                 |         | 0.010 (+0.396); higher acousticness similarity 0.100 (+0.010)      |
+------+----------------------+-----------------+---------+--------------------------------------------------------------------+
```

## 8. Ideas for Improvement

- Add more songs for underrepresented genres and collect listener feedback before tuning weights.
- Support related mood labels and activity-specific or mixed preferences.
- Warn about unsupported categories and weak matches, and test an optional discovery slot.

## 9. Personal Reflection

*Draft for the student to review and personalize. This describes the demonstrated engineering process; it does not claim personal listening experience.*

The biggest learning moment was seeing that valid scoring math can still produce a poor fit when the requested music is missing. The conflicting profile showed this clearly: doubling energy changed the winner but still returned low-energy lofi. AI helped implement the loader, propose edge cases, and explain the rankings. Its suggestions needed checking against the actual catalog, hand calculations, and terminal output; a larger score alone did not prove a better recommendation. Simple rules can feel like recommendations because matching a few recognizable traits gives different listening sessions different results. Next, I would add more varied songs, ask listeners to rate the results, and use that feedback to compare weight choices.

## 10. Advanced Extension

Five new features can contribute when their targets are supplied: popularity, decade, detailed mood tags, duration, and instrumentalness. Each gets raw weight 0.10, and all active weights are normalized together. Popularity rewards closeness to a requested level, not fame alone. Three selectable strategies share one scorer: genre-first, mood-first, and energy-focus; baseline is an alias for genre-first. The original evaluation above uses only the core preferences.

Diversity is optional. Each prior appearance of an artist subtracts 0.12 and each prior appearance of a genre subtracts 0.06 from a candidate. The system recomputes these penalties after each selection. Relevance can still outweigh a penalty, so this is not a quota. It offers variety across artist and genre labels, not proof of fairness to people or musical cultures. Displayed adjusted scores can be negative; explanations retain the base score and each penalty.

Additional limitations: synthetic popularity and decade values cannot support conclusions about real trends. Exact detailed tags can miss synonyms; detailed tags and the main mood can count similar information twice. Treating all five extra preferences as equally important is a design choice without listener validation. The example instrumentalness targets are explicit simulation choices and do not imply a relationship between instrumental and acoustic music. The data schema admits decades from 1900 to 2090 for experimentation; those bounds are not a claim that a track has already been released.

### Advanced example output

Captured from `python -m src.main --advanced --mode mood-first --diversity`. Sunrise City still leads, but Rooftop Lights comes second because mood-first rewards happy more than the pop label. Gym Hero pays a repeated-genre penalty after Sunrise City. Night Drive Loop does not appear in this list, while Brass Horizon and Storm Runner provide other genres and artists. This example checks that the controls and reasons work; it does not measure listener satisfaction.

```text
Loaded songs: 18
Profile: genre=pop, mood=happy, target energy=0.80
Advanced preferences: {'target_popularity': 60, 'preferred_decade': 2010, 'mood_tags': ('happy', 'nostalgic'), 'target_duration_seconds': 210, 'target_instrumentalness': 0.1}
Mode: mood-first | Diversity: on

Top 5 recommendations (adjusted scores when diversity is on):
+------+----------------------+-----------------+---------+--------------------------------------------------------------------+
| Rank | Song                 | Artist          | Score   | Reasons                                                            |
+------+----------------------+-----------------+---------+--------------------------------------------------------------------+
| 1    | Sunrise City         | Neon Echo       | 0.895   | genre match (+0.143); mood match (+0.357); energy distance 0.020   |
|      |                      |                 |         | (+0.140); acousticness omitted; active weights normalized by 1.40; |
|      |                      |                 |         | popularity similarity 0.720 (+0.051); release decade similarity    |
|      |                      |                 |         | 0.900 (+0.064); detailed mood tags similarity 0.000 (+0.000);      |
|      |                      |                 |         | duration similarity 0.993 (+0.071); instrumentalness similarity    |
|      |                      |                 |         | 0.950 (+0.068); base score 0.895; repeated artist penalty          |
|      |                      |                 |         | (-0.000); repeated genre penalty (-0.000); adjusted score 0.895    |
+------+----------------------+-----------------+---------+--------------------------------------------------------------------+
| 2    | Rooftop Lights       | Indigo Parade   | 0.769   | genre mismatch (+0.000); mood match (+0.357); energy distance      |
|      |                      |                 |         | 0.040 (+0.137); acousticness omitted; active weights normalized by |
|      |                      |                 |         | 1.40; popularity similarity 0.890 (+0.064); release decade         |
|      |                      |                 |         | similarity 1.000 (+0.071); detailed mood tags similarity 0.000     |
|      |                      |                 |         | (+0.000); duration similarity 0.980 (+0.070); instrumentalness     |
|      |                      |                 |         | similarity 0.980 (+0.070); base score 0.769; repeated artist       |
|      |                      |                 |         | penalty (-0.000); repeated genre penalty (-0.000); adjusted score  |
|      |                      |                 |         | 0.769                                                              |
+------+----------------------+-----------------+---------+--------------------------------------------------------------------+
| 3    | Gym Hero             | Max Pulse       | 0.452   | genre match (+0.143); mood mismatch (+0.000); energy distance      |
|      |                      |                 |         | 0.130 (+0.124); acousticness omitted; active weights normalized by |
|      |                      |                 |         | 1.40; popularity similarity 0.680 (+0.049); release decade         |
|      |                      |                 |         | similarity 0.900 (+0.064); detailed mood tags similarity 0.000     |
|      |                      |                 |         | (+0.000); duration similarity 0.917 (+0.065); instrumentalness     |
|      |                      |                 |         | similarity 0.930 (+0.066); base score 0.512; repeated artist       |
|      |                      |                 |         | penalty (-0.000); repeated genre penalty (-0.060); adjusted score  |
|      |                      |                 |         | 0.452                                                              |
+------+----------------------+-----------------+---------+--------------------------------------------------------------------+
| 4    | Brass Horizon        | Copper Steps    | 0.402   | genre mismatch (+0.000); mood mismatch (+0.000); energy distance   |
|      |                      |                 |         | 0.060 (+0.134); acousticness omitted; active weights normalized by |
|      |                      |                 |         | 1.40; popularity similarity 0.980 (+0.070); release decade         |
|      |                      |                 |         | similarity 0.800 (+0.057); detailed mood tags similarity 0.000     |
|      |                      |                 |         | (+0.000); duration similarity 0.970 (+0.069); instrumentalness     |
|      |                      |                 |         | similarity 1.000 (+0.071); base score 0.402; repeated artist       |
|      |                      |                 |         | penalty (-0.000); repeated genre penalty (-0.000); adjusted score  |
|      |                      |                 |         | 0.402                                                              |
+------+----------------------+-----------------+---------+--------------------------------------------------------------------+
| 5    | Storm Runner         | Voltline        | 0.385   | genre mismatch (+0.000); mood mismatch (+0.000); energy distance   |
|      |                      |                 |         | 0.110 (+0.127); acousticness omitted; active weights normalized by |
|      |                      |                 |         | 1.40; popularity similarity 0.840 (+0.060); release decade         |
|      |                      |                 |         | similarity 0.900 (+0.064); detailed mood tags similarity 0.000     |
|      |                      |                 |         | (+0.000); duration similarity 0.893 (+0.064); instrumentalness     |
|      |                      |                 |         | similarity 0.980 (+0.070); base score 0.385; repeated artist       |
|      |                      |                 |         | penalty (-0.000); repeated genre penalty (-0.000); adjusted score  |
|      |                      |                 |         | 0.385                                                              |
+------+----------------------+-----------------+---------+--------------------------------------------------------------------+
```

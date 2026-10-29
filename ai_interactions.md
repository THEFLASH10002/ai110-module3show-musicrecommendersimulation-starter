# AI Interactions Log

## Agentic Workflow (SF8)

**Task given to the agent**

Implement the four advanced challenges: add at least five new song attributes and score them, provide selectable ranking modes, penalize repeated artists and genres, and display scores with reasons in a terminal table. Document the prompts, decisions, and checks here. Work was performed by one coding assistant in this chat; no separate chat or parallel agent session was created.

**Prompts used and reproducible examples**

The user's challenge descriptions were the implementation instructions. The following example prompts make the same requests concrete for repeating or extending the work:

> Add popularity (0–100), release decade, detailed mood tags, duration in seconds, and instrumentalness (0–1) to every song in songs.csv. Preserve all original fields and values. Generate synthetic metadata and label it as such. Update CSV conversion, the Song dataclass, and profile targets. Score each new attribute only when its target is supplied; normalize all active weights together and return reasons. Keep existing profiles compatible.

> Review recommender.py and brainstorm a simple Strategy pattern for genre-first, mood-first, and energy-focused ranking. Compare a weight registry with separate strategy subclasses. Choose the smallest approach that keeps one formula implementation, exposes a CLI mode selector, and preserves the baseline recipe name.

> Add a greedy diversity rule: subtract 0.12 for every already selected track by the candidate's artist and 0.06 for every already selected track in its genre. Recalculate penalties after each selection. Use case-insensitive names, break ties by numeric ID, keep input data unchanged, and explain the base score, both penalties, and adjusted score. Make diversity optional so baseline comparisons remain reproducible.

> Suggest a readable terminal table using tabulate or standard-library ASCII formatting. Include rank, title, artist, final score, and the complete reasons for every score. Wrap long reasons instead of truncating them. Keep the CLI runnable without installing extra packages.

**What the AI generated or changed**

- Added five synthetic columns to all 18 songs, with two detailed mood tags per song. The loader converts IDs, popularity, and decade to integers; numerical features to floats; and semicolon-separated tags to normalized tuples.
- Added optional targets for all five attributes to the dictionary and dataclass profile interfaces. Each requested advanced attribute has raw weight 0.10. The scorer divides every component by the total active weight and includes each contribution in the reasons.
- Added a frozen ScoringStrategy configuration and registry for genre-first, mood-first, and energy-focus. Baseline remains a compatible alias for genre-first. CLI options are `--mode` (alias `--recipe`), `--advanced`, and `--diversity`.
- Added greedy artist and genre penalties to the shared ranking function, with configurable amounts in the Python API. The dataclass interface supports the same modes and diversity ranking, including contextual penalty explanations.
- Replaced free-form recommendation lines with an ASCII table containing full wrapped reasons. No new package dependency was needed.
- Added focused tests for each new feature's score, data validation, normalization, mode differences, repeated-name normalization, cumulative penalties, unchanged input data, object-interface consistency, and complete table output.
- Updated the README and model card with formulas, usage, limitations, and output captured from the current CLI. Earlier baseline rankings and scores remain reproducible with advanced preferences and diversity off.

**Verification notes**

These checks were performed by the coding assistant; they are not a claim that the student manually tested or listened to the songs.

- Compared every original CSV field against the prior committed CSV. All 18 rows retain every original value, and exactly five columns were added. Checked numeric ranges, positive durations, decade multiples, and at least two tags per row.
- Independently checked Sunrise City's advanced mood-first score: `(0.2 + 0.5 + 0.2*0.98 + 0.1*0.72 + 0.1*0.90 + 0.1*0 + 0.1*(1 - 2/300) + 0.1*0.95) / 1.4 = 0.894524`. The CLI rounds this to 0.895. The denominator is 0.90 active core weight plus five 0.10 advanced weights.
- Checked a controlled ranking where candidates initially had the same artist or genre. The second repeat receives one count's penalty, and later repeats receive accumulated penalties. Zero penalties reproduce the normal ranking order. The greedy selector recomputes after each choice rather than penalizing only the input order.
- Observed the actual default pop results with diversity off: Sunrise City, Gym Hero, Rooftop Lights, Night Drive Loop, Brass Horizon. With diversity on: Sunrise City, Gym Hero, Rooftop Lights, Brass Horizon, Concrete Anthem. The second Neon Echo song loses its slot to a different artist.
- Observed the chill results with diversity off: Library Rain, Midnight Coding, Focus Flow, Spacewalk Thoughts, Coffee Shop Stories. With diversity on: Library Rain, Midnight Coding, Spacewalk Thoughts, Focus Flow, Coffee Shop Stories. The third lofi track moves below an ambient track; this demonstrates a soft penalty rather than a hard quota.
- Ran `python -m pytest -q`: **65 tests passed**. Checked table column widths and reassembled wrapped reasons to verify that no explanation text was lost. Automated checks compare README/model-card baseline examples with actual CLI output.
- During implementation, the old CLI snapshot checks failed because the display changed to a table. Updated the display assertion and regenerated captured output; score and ranking checks continued to pass. This is why output fixtures needed review rather than simply deleting failing checks.
- Ran `git diff --check` successfully. Used the installed Python 3.14 executable directly because the shell's generic python alias points to WindowsApps.

**Student manual review still useful**

Edit the example advanced targets to reflect your own preferences, then compare genre-first and mood-first with `python -m src.main --advanced --mode mood-first --diversity`. Judge relevance yourself; a passing test verifies the rules, not that a listener will enjoy the results. Confirm that the synthetic metadata and reflection draft are described accurately before presenting this as personal work.

## Design Pattern (SF10)

**Chosen pattern: a lightweight, data-driven Strategy pattern.**

The alternatives considered were a registry of weight configurations and separate classes implementing the same scoring interface. Separate classes would repeat or delegate identical arithmetic because these strategies currently differ only in their weights. The chosen design uses immutable ScoringStrategy objects in SCORING_STRATEGIES. The CLI selects a registry key, and score_song applies that configuration through one shared scoring path. More complex algorithms could later implement separate strategy classes when their behavior differs beyond weights.

Genre-first uses genre/mood/energy/acousticness weights of 0.40/0.30/0.20/0.10. Mood-first uses 0.20/0.50/0.20/0.10. Energy-focus uses 0.20/0.30/0.40/0.10. Advanced features each retain raw weight 0.10; all active weights are normalized. Both functional and object interfaces select the same strategy registry. Diversity is a separate ranking step because it depends on songs already selected, while a base similarity score compares one song with one profile.

AI contributed the implementation, the tradeoff analysis, example prompts, tests, and documentation. Verification used known calculations and observed output, rather than assuming that a named design pattern or a larger score proves better recommendations.

## Diversity and Fairness Review

Artist and genre variety are limited forms of coverage. A soft score penalty does not guarantee equal exposure, a fixed artist quota, or fairness across people or cultures. Relevance can outweigh the penalty, and adjusted scores can become negative when many repeats are selected. The score column shows this adjusted selection score when diversity is enabled; reasons retain the original base score. Synthetic popularity must not be treated as evidence of real listening trends, and a popularity target is matched by closeness rather than always rewarding the most popular song.

## Rubric Cleanup Review

The supplied rubric has seven required categories worth 21 points and four bonus categories worth 8 points. Reviewed the existing implementation against each category, then added an evidence table in the README linking to the relevant code, captured outputs, model card, and workflow notes. Replaced outdated planning instructions with descriptions of the finished system and corrected the displayed advanced-feature ranges. The model card now explicitly describes the observed gain from four to five artists in the diverse pop list, while keeping the limits of this fairness claim clear.

Added interaction checks for all three ranking modes, advanced preferences on/off, and diversity on/off across all four evaluation profiles. These verify finite descending scores, five distinct recommendations, complete advanced contributions and penalties, and unchanged input records. The final check is `python -m pytest -q`: **77 tests passed**. `git diff --check` also passed. The rubric table documents evidence rather than claiming an instructor's grade; the personal reflection remains labeled as a student-review draft.

"""Verify advanced feature math, selectable modes, and diversity selection."""

import csv
from dataclasses import asdict
from pathlib import Path
import subprocess
import sys

import pytest

from src.main import EVALUATION_PROFILES, with_advanced_preferences
from src.recommender import (
    SCORING_STRATEGIES, Recommender, Song, UserProfile,
    load_songs, recommend_songs, score_song,
)

ROOT = Path(__file__).resolve().parents[1]
POP = EVALUATION_PROFILES["High-Energy Pop"]


def test_advanced_csv_types_and_original_values():
    songs = load_songs(ROOT / "data/songs.csv")
    assert len(songs) == 18
    assert len(songs[0]) == 15
    for song in songs:
        assert isinstance(song["popularity"], int) and 0 <= song["popularity"] <= 100
        assert isinstance(song["release_decade"], int) and song["release_decade"] % 10 == 0
        assert len(song["detailed_mood_tags"]) >= 2
        assert song["duration_seconds"] > 0
        assert 0 <= song["instrumentalness"] <= 1
    assert songs[0]["energy"] == 0.82


@pytest.mark.parametrize("change", [
    {"popularity": "101"}, {"popularity": "2.5"}, {"release_decade": "2023"},
    {"detailed_mood_tags": "; ;"}, {"duration_seconds": "0"},
    {"duration_seconds": "nan"}, {"instrumentalness": "-0.1"},
])
def test_invalid_advanced_csv_values(tmp_path, change):
    song = load_songs(ROOT / "data/songs.csv")[0]
    song["detailed_mood_tags"] = ";".join(song["detailed_mood_tags"])
    song.update(change)
    path = tmp_path / "invalid.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(song))
        writer.writeheader()
        writer.writerow(song)
    with pytest.raises(ValueError, match="CSV line 2"):
        load_songs(path)


@pytest.mark.parametrize("preference, field, target, match, mismatch, expected", [
    ("target_popularity", "popularity", 80, 80, 0, 0.2),
    ("preferred_decade", "release_decade", 2010, 2010, 1960, 0.5),
    ("mood_tags", "detailed_mood_tags", (" Nostalgic ", "dreamy"), ("nostalgic", "dreamy"), ("dreamy",), 0.5),
    ("target_duration_seconds", "duration_seconds", 210, 210, 360, 0.5),
    ("target_instrumentalness", "instrumentalness", 0.9, 0.9, 0.1, 0.2),
])
def test_each_new_feature_changes_scoring(preference, field, target, match, mismatch, expected):
    song = load_songs(ROOT / "data/songs.csv")[0]
    prefs = {**POP, preference: target}
    good_score, good_reasons = score_song(prefs, {**song, field: match})
    poor_score, _ = score_song(prefs, {**song, field: mismatch})
    # Without acoustic preference, 0.9 core + 0.1 advanced = 1.0 active weight.
    assert good_score == pytest.approx(0.896 + 0.1)
    assert poor_score == pytest.approx(0.896 + 0.1 * expected)
    assert good_score > poor_score
    assert len(good_reasons) == 5


def test_all_features_normalize_and_missing_preferences_are_omitted():
    song = load_songs(ROOT / "data/songs.csv")[0]
    prefs = {**POP, "energy": song["energy"], "likes_acoustic": False,
             "target_popularity": song["popularity"], "preferred_decade": song["release_decade"],
             "mood_tags": song["detailed_mood_tags"], "target_duration_seconds": song["duration_seconds"],
             "target_instrumentalness": song["instrumentalness"]}
    perfect = {**song, "acousticness": 0}
    for mode in SCORING_STRATEGIES:
        assert score_song(prefs, perfect, recipe=mode)[0] == pytest.approx(1)
    absent = {**POP, "target_popularity": None, "mood_tags": ()}
    assert score_song(absent, song) == score_song(POP, song)


@pytest.mark.parametrize("prefs", [
    {"target_popularity": -1}, {"preferred_decade": 2012},
    {"target_duration_seconds": 0}, {"target_instrumentalness": 2}, {"mood_tags": (" ",)},
])
def test_invalid_advanced_preferences(prefs):
    song = load_songs(ROOT / "data/songs.csv")[0]
    with pytest.raises(ValueError):
        score_song({**POP, **prefs}, song)


def test_genre_and_mood_strategies_make_different_choices():
    song = load_songs(ROOT / "data/songs.csv")[0]
    genre_match = {**song, "id": 1, "mood": "intense"}
    mood_match = {**song, "id": 2, "genre": "rock"}
    assert recommend_songs(POP, [mood_match, genre_match], 1, recipe="genre-first")[0][0] is genre_match
    assert recommend_songs(POP, [genre_match, mood_match], 1, recipe="mood-first")[0][0] is mood_match
    for strategy in SCORING_STRATEGIES.values():
        assert sum(asdict(strategy).values()) == pytest.approx(1)


def test_diversity_recomputes_penalties_after_each_selection():
    song = load_songs(ROOT / "data/songs.csv")[0]
    songs = [
        {**song, "id": 1, "artist": "Artist A"},
        {**song, "id": 2, "artist": " artist a "},
        {**song, "id": 3, "artist": "Artist B"},
        {**song, "id": 4, "artist": "Artist C", "genre": "rock"},
    ]
    original = [s.copy() for s in songs]
    normal = recommend_songs(POP, songs, 4)
    diverse = recommend_songs(POP, songs, 4, diversity=True, artist_penalty=0.3, genre_penalty=0.3)
    assert [s["id"] for s, _, _ in normal] == [1, 2, 3, 4]
    assert [s["id"] for s, _, _ in diverse] == [1, 3, 4, 2]
    base = normal[0][1]
    assert diverse[1][1] == pytest.approx(base - 0.3)
    assert diverse[3][1] == pytest.approx(base - 0.3 - 0.6)
    assert "repeated artist penalty (-0.300)" in diverse[3][2]
    assert "repeated genre penalty (-0.600)" in diverse[3][2]
    assert songs == original
    assert recommend_songs(POP, songs, 4, diversity=True, artist_penalty=0, genre_penalty=0) == [
        (s, score, reason + f"; base score {score:.3f}; repeated artist penalty (-0.000); repeated genre penalty (-0.000); adjusted score {score:.3f}")
        for s, score, reason in normal]


@pytest.mark.parametrize("penalties", [{"artist_penalty": -0.1}, {"genre_penalty": float("nan")}])
def test_invalid_diversity_penalties(penalties):
    with pytest.raises(ValueError):
        recommend_songs(POP, [], diversity=True, **penalties)


def test_oop_advanced_mode_and_diversity_consistency():
    songs = [Song(**s) for s in load_songs(ROOT / "data/songs.csv")]
    prefs = with_advanced_preferences(POP)
    user = UserProfile("pop", "happy", 0.8, False,
                       **{k: v for k, v in prefs.items() if k not in ("genre", "mood", "energy")})
    rec = Recommender(songs)
    expected = recommend_songs(asdict(user), [asdict(s) for s in songs], recipe="mood-first", diversity=True)
    results = rec.recommend(user, recipe="mood-first", diversity=True)
    assert [s.id for s in results] == [s["id"] for s, _, _ in expected]
    for result, (_, _, reasons) in zip(results, expected):
        assert rec.explain_recommendation(user, result, recipe="mood-first", diversity=True) == reasons


def test_advanced_cli_table_preserves_all_reasons():
    result = subprocess.run(
        [sys.executable, "-m", "src.main", "--advanced", "--mode", "mood-first", "--diversity"],
        cwd=ROOT, capture_output=True, text=True, check=True,
    )
    assert "Mode: mood-first | Diversity: on" in result.stdout
    assert "| Rank | Song" in result.stdout and "Reasons" in result.stdout
    lines = [line for line in result.stdout.splitlines() if line.startswith("|")]
    assert len({len(line) for line in lines}) == 1
    # Reassemble wrapped reason cells and check none were truncated.
    actual = " ".join(line.split("|")[5].strip() for line in lines[1:])
    prefs = with_advanced_preferences(POP)
    songs = load_songs(ROOT / "data/songs.csv")
    for _, _, reasons in recommend_songs(prefs, songs, recipe="mood-first", diversity=True):
        assert " ".join(reasons.split()) in " ".join(actual.split())

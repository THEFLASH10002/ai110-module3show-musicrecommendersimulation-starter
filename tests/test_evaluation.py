"""Check experiment math, observed rankings, and reproducible evaluation evidence."""

from pathlib import Path
import subprocess
import sys

import pytest

from src.main import EVALUATION_PROFILES
from src.recommender import load_songs, recommend_songs, score_song


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("recipe", ["baseline", "energy-focus"])
@pytest.mark.parametrize("acoustic", [None, True, False])
def test_recipes_normalize_perfect_matches(recipe, acoustic):
    prefs = {"genre": "pop", "mood": "happy", "energy": 0.8, "likes_acoustic": acoustic}
    song = {"genre": "pop", "mood": "happy", "energy": 0.8,
            "acousticness": 0.0 if acoustic is False else 1.0}
    assert score_song(prefs, song, recipe=recipe)[0] == pytest.approx(1.0)


def test_weight_shift_uses_expected_contributions():
    song = load_songs(ROOT / "data/songs.csv")[0]
    prefs = {**EVALUATION_PROFILES["High-Energy Pop"], "likes_acoustic": False}
    score, reasons = score_song(prefs, song, recipe="energy-focus")
    assert score == pytest.approx(0.2 + 0.3 + 0.4 * 0.98 + 0.1 * 0.82)
    assert "genre match (+0.200)" in reasons
    assert "energy distance 0.020 (+0.392)" in reasons


@pytest.mark.parametrize("recipe, winners", [
    ("baseline", ["Sunrise City", "Library Rain", "Storm Runner", "Focus Flow"]),
    ("energy-focus", ["Sunrise City", "Library Rain", "Storm Runner", "Midnight Coding"]),
])
def test_observed_winners_and_rank_changes(recipe, winners):
    songs = load_songs(ROOT / "data/songs.csv")
    actual = []
    for profile in EVALUATION_PROFILES.values():
        results = recommend_songs(profile, songs, recipe=recipe)
        assert len(results) == 5
        assert all(0 <= score <= 1 for _, score, _ in results)
        actual.append(results[0][0]["title"])
    assert actual == winners
    pop = recommend_songs(EVALUATION_PROFILES["High-Energy Pop"], songs, recipe=recipe)
    assert pop[1][0]["title"] == ("Gym Hero" if recipe == "baseline" else "Rooftop Lights")


@pytest.mark.parametrize("recipe", ["baseline", "energy-focus"])
@pytest.mark.parametrize("energy", [0.0, 1.0])
def test_unknown_labels_and_energy_boundaries(recipe, energy):
    songs = load_songs(ROOT / "data/songs.csv")
    prefs = {"genre": "unlisted", "mood": "unlisted", "energy": energy}
    results = recommend_songs(prefs, songs, recipe=recipe)
    assert len(results) == 5
    # Without label or acoustic matches, only energy distance orders the songs.
    expected = sorted(songs, key=lambda song: (abs(song["energy"] - energy), song["id"]))[:5]
    assert [s["id"] for s, _, _ in results] == [s["id"] for s in expected]
    for _, score, reasons in results:
        assert 0 <= score <= 1
        assert "mood mismatch" in reasons


def test_unknown_recipe_is_rejected():
    song = load_songs(ROOT / "data/songs.csv")[0]
    with pytest.raises(ValueError, match="Unknown scoring recipe"):
        score_song(EVALUATION_PROFILES["High-Energy Pop"], song, recipe="typo")


@pytest.mark.parametrize("recipe", ["baseline", "energy-focus"])
def test_model_card_output_matches_evaluation_cli(recipe):
    result = subprocess.run(
        [sys.executable, "-m", "src.main", "--evaluate", "--recipe", recipe],
        cwd=ROOT, capture_output=True, text=True, check=True,
    )
    card = (ROOT / "model_card.md").read_text(encoding="utf-8")
    header, *profiles = result.stdout.split("=== ")
    assert len(profiles) == 4
    for profile in profiles:
        block = "```text\n" + header.strip() + "\n=== " + profile.rstrip() + "\n```"
        assert block in card

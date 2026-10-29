import csv
from dataclasses import asdict
from pathlib import Path
import subprocess
import sys

import pytest

from src.recommender import load_songs, recommend_songs, score_song, Song, UserProfile, Recommender

CATALOG = Path(__file__).resolve().parents[1] / 'data' / 'songs.csv'
POP = {'genre': 'pop', 'mood': 'happy', 'energy': 0.8}


def test_load_catalog_numeric_types():
    songs = load_songs(CATALOG)
    assert len(songs) == 18
    assert isinstance(songs[0]['id'], int)
    for field in ('energy', 'tempo_bpm', 'valence', 'danceability', 'acousticness'):
        assert isinstance(songs[0][field], float)
    assert songs[0]['title'] == 'Sunrise City'


@pytest.mark.parametrize('change', [
    {'energy': 'nan'}, {'energy': '1.1'}, {'energy': ''},
    {'tempo_bpm': '-1'}, {'tempo_bpm': 'inf'}, {'valence': 'text'},
])
def test_loader_rejects_invalid_values(tmp_path, change):
    row = {**load_songs(CATALOG)[0], **change}
    path = tmp_path / 'invalid.csv'
    with path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row))
        writer.writeheader()
        writer.writerow(row)
    with pytest.raises(ValueError, match='CSV line 2'):
        load_songs(path)


def test_loader_rejects_missing_header_and_duplicate_ids(tmp_path):
    path = tmp_path / 'songs.csv'
    path.write_text('title,energy\nExample,0.4\n', encoding='utf-8')
    with pytest.raises(ValueError, match='headers'):
        load_songs(path)
    row = load_songs(CATALOG)[0]
    with path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row))
        writer.writeheader()
        writer.writerows([row, row])
    with pytest.raises(ValueError, match='duplicate song ID'):
        load_songs(path)


def test_weighted_scores_and_reasons():
    song = load_songs(CATALOG)[0]
    score, reasons = score_song({**POP, 'likes_acoustic': False}, song)
    assert score == pytest.approx(0.978)
    assert 'genre match (+0.400)' in reasons
    assert 'mood match (+0.300)' in reasons
    assert 'energy distance 0.020 (+0.196)' in reasons
    assert 'lower acousticness similarity 0.820 (+0.082)' in reasons
    score, reasons = score_song(POP, song)
    assert score == pytest.approx(0.896 / 0.9)
    assert 'acousticness omitted' in reasons[-1]


def test_profile_aliases_normalization_and_study_example():
    songs = load_songs(CATALOG)
    prefs = {'favorite_genre': ' LOFI ', 'favorite_mood': 'ChIlL',
             'target_energy': 0.4, 'likes_acoustic': True}
    assert score_song(prefs, songs[3])[0] == pytest.approx(0.976)
    assert score_song(prefs, songs[2])[0] == pytest.approx(0.108)


def test_energy_rewards_distance_not_magnitude():
    song = load_songs(CATALOG)[0]
    prefs = {**POP, 'energy': 0.4}
    low = score_song(prefs, {**song, 'energy': 0.35})[0]
    high = score_song(prefs, {**song, 'energy': 0.45})[0]
    assert low == pytest.approx(high)
    assert high > score_song(prefs, {**song, 'energy': 0.9})[0]


@pytest.mark.parametrize('value', [-0.1, 1.1, float('nan'), float('inf'), 'bad'])
def test_scorer_rejects_invalid_energy(value):
    song = load_songs(CATALOG)[0]
    with pytest.raises(ValueError, match='energy'):
        score_song({**POP, 'energy': value}, song)
    with pytest.raises(ValueError, match='energy'):
        score_song(POP, {**song, 'energy': value})


def test_acoustic_preference_validation():
    song = load_songs(CATALOG)[0]
    with pytest.raises(ValueError, match='likes_acoustic'):
        score_song({**POP, 'likes_acoustic': 'false'}, song)
    with pytest.raises(ValueError, match='acousticness'):
        score_song({**POP, 'likes_acoustic': True}, {**song, 'acousticness': 2})


def test_rank_entire_catalog_without_mutation():
    songs = load_songs(CATALOG)
    original = [song.copy() for song in songs]
    # Reverse input so the expected order cannot pass by returning a catalog slice.
    results = recommend_songs(POP, list(reversed(songs)), k=5)
    assert [song['title'] for song, _, _ in results] == [
        'Sunrise City', 'Gym Hero', 'Rooftop Lights', 'Night Drive Loop', 'Brass Horizon']
    assert all(results[i][1] >= results[i + 1][1] for i in range(len(results) - 1))
    assert all(explanation for _, _, explanation in results)
    assert songs == original


def test_ties_numeric_ids_and_k_boundaries():
    song = load_songs(CATALOG)[0]
    songs = [{**song, 'id': '10'}, {**song, 'id': '2'}]
    assert [s['id'] for s, _, _ in recommend_songs(POP, songs, 99)] == ['2', '10']
    assert recommend_songs(POP, songs, 0) == []
    assert recommend_songs(POP, songs, -1) == []
    assert recommend_songs(POP, [], 5) == []


def test_ranking_uses_unrounded_scores():
    song = load_songs(CATALOG)[0]
    songs = [{**song, 'id': 1, 'energy': 0.8002}, {**song, 'id': 2, 'energy': 0.8001}]
    results = recommend_songs(POP, songs, 2)
    assert results[0][0]['id'] == 2


def test_oop_matches_functional_scores_and_preserves_original_objects():
    songs = [Song(**s) for s in reversed(load_songs(CATALOG))]
    user = UserProfile('lofi', 'chill', 0.4, True)
    rec = Recommender(songs)
    expected = recommend_songs(asdict(user), [asdict(s) for s in songs], 5)
    results = rec.recommend(user)
    assert [s.id for s in results] == [s['id'] for s, _, _ in expected]
    assert all(any(result is s for s in songs) for result in results)
    assert rec.explain_recommendation(user, results[0]) == expected[0][2]


def test_cli_and_readme_sample_match():
    root = CATALOG.parents[1]
    result = subprocess.run([sys.executable, '-m', 'src.main'], cwd=root,
                            capture_output=True, text=True, check=True)
    assert result.stdout.startswith('Loaded songs: 18\n')
    assert '| 1    | Sunrise City' in result.stdout
    readme = (root / 'README.md').read_text(encoding='utf-8')
    sample = readme.split('## Sample Recommendation Output', 1)[1].split('```text\n', 1)[1].split('```', 1)[0]
    assert sample.strip() == result.stdout.strip()

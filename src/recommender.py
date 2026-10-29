"""Load, score, and rank songs with transparent content-based explanations."""

import csv
import math
from dataclasses import asdict, dataclass
from typing import Dict, List, Tuple


@dataclass
class Song:
    """Store the catalog attributes for one song."""

    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float


@dataclass
class UserProfile:
    """Store explicit genre, mood, energy, and acoustic preferences."""

    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool


def _unit_value(value, name: str) -> float:
    """Convert a numerical feature and require a finite value from zero to one."""
    try:
        number = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{name} must be a number between 0 and 1") from error
    if not math.isfinite(number) or not 0 <= number <= 1:
        raise ValueError(f"{name} must be a finite number between 0 and 1")
    return number


def load_songs(csv_path: str) -> List[Dict]:
    """Read validated CSV rows as dictionaries with integer IDs and float features."""
    songs = []
    seen_ids = set()
    fields = set(Song.__dataclass_fields__)
    with open(csv_path, newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or set(reader.fieldnames) != fields or len(reader.fieldnames) != len(fields):
            raise ValueError("CSV headers must match the Song fields")
        for row in reader:
            try:
                if set(row) != fields or any(value is None or not value.strip() for value in row.values()):
                    raise ValueError("every row must contain exactly one nonempty value per column")
                song = {key: value.strip() for key, value in row.items()}
                song["id"] = int(song["id"])
                if song["id"] in seen_ids:
                    raise ValueError(f"duplicate song ID {song['id']}")
                for field in ("energy", "valence", "danceability", "acousticness"):
                    song[field] = _unit_value(song[field], field)
                song["tempo_bpm"] = float(song["tempo_bpm"])
                if not math.isfinite(song["tempo_bpm"]) or song["tempo_bpm"] <= 0:
                    raise ValueError("tempo_bpm must be finite and positive")
            except (TypeError, ValueError) as error:
                raise ValueError(f"Invalid song at CSV line {reader.line_num}: {error}") from error
            seen_ids.add(song["id"])
            songs.append(song)
    return songs


def score_song(user_prefs: Dict, song: Dict, *, recipe: str = "baseline") -> Tuple[float, List[str]]:
    """Return the normalized weighted similarity and its component explanations."""
    genre = user_prefs["genre"] if "genre" in user_prefs else user_prefs["favorite_genre"]
    mood = user_prefs["mood"] if "mood" in user_prefs else user_prefs["favorite_mood"]
    target = user_prefs["energy"] if "energy" in user_prefs else user_prefs["target_energy"]
    target = _unit_value(target, "target_energy")
    energy = _unit_value(song["energy"], "energy")
    likes_acoustic = user_prefs.get("likes_acoustic")
    if likes_acoustic is not None and not isinstance(likes_acoustic, bool):
        raise ValueError("likes_acoustic must be True, False, or None")
    if recipe == "baseline":
        genre_weight, mood_weight, energy_weight, acoustic_weight = 0.4, 0.3, 0.2, 0.1
    elif recipe == "energy-focus":
        genre_weight, mood_weight, energy_weight, acoustic_weight = 0.2, 0.3, 0.4, 0.1
    else:
        raise ValueError(f"Unknown scoring recipe: {recipe}")
    active_weight = genre_weight + mood_weight + energy_weight
    if likes_acoustic is not None:
        active_weight += acoustic_weight
    genre_match = song["genre"].strip().casefold() == genre.strip().casefold()
    mood_match = song["mood"].strip().casefold() == mood.strip().casefold()
    genre_points = genre_weight * genre_match / active_weight
    mood_points = mood_weight * mood_match / active_weight
    distance = abs(energy - target)
    energy_points = energy_weight * (1 - distance) / active_weight
    reasons = [
        f"genre {'match' if genre_match else 'mismatch'} (+{genre_points:.3f})",
        f"mood {'match' if mood_match else 'mismatch'} (+{mood_points:.3f})",
        f"energy distance {distance:.3f} (+{energy_points:.3f})",
    ]
    score = genre_points + mood_points + energy_points
    if likes_acoustic is not None:
        acousticness = _unit_value(song["acousticness"], "acousticness")
        similarity = acousticness if likes_acoustic else 1 - acousticness
        acoustic_points = acoustic_weight * similarity / active_weight
        score += acoustic_points
        preference = "higher" if likes_acoustic else "lower"
        reasons.append(f"{preference} acousticness similarity {similarity:.3f} (+{acoustic_points:.3f})")
    else:
        reasons.append("acousticness omitted; active weights normalized by 0.90")
    return score, reasons


def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5, *, recipe: str = "baseline") -> List[Tuple[Dict, float, str]]:
    """Score every song and return the top k by score, breaking ties by numeric ID."""
    if k <= 0:
        return []
    scored = []
    for song in songs:
        score, reasons = score_song(user_prefs, song, recipe=recipe)
        scored.append((song, score, "; ".join(reasons)))
    return sorted(scored, key=lambda result: (-result[1], int(result[0]["id"])))[:k]


class Recommender:
    """Adapt Song and UserProfile objects to the shared scoring implementation."""

    def __init__(self, songs: List[Song]):
        """Retain the supplied catalog without reordering it."""
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """Return the top k original Song objects using the shared ranking rules."""
        records = [asdict(song) for song in self.songs]
        originals = {id(record): song for record, song in zip(records, self.songs)}
        return [originals[id(record)] for record, _, _ in recommend_songs(asdict(user), records, k)]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Explain the same weighted contributions used to rank this song."""
        _, reasons = score_song(asdict(user), asdict(song))
        return "; ".join(reasons)

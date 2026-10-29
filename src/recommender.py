"""Load, score, and rank songs with transparent content-based explanations."""

import csv
import math
from dataclasses import asdict, dataclass
from typing import Dict, List, Optional, Tuple


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
    popularity: int = 50
    release_decade: int = 2020
    detailed_mood_tags: Tuple[str, ...] = ()
    duration_seconds: float = 180.0
    instrumentalness: float = 0.0


@dataclass
class UserProfile:
    """Store explicit genre, mood, energy, and acoustic preferences."""

    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool
    target_popularity: Optional[float] = None
    preferred_decade: Optional[int] = None
    mood_tags: Tuple[str, ...] = ()
    target_duration_seconds: Optional[float] = None
    target_instrumentalness: Optional[float] = None


@dataclass(frozen=True)
class ScoringStrategy:
    """Define interchangeable core weights for a ranking mode."""

    genre: float
    mood: float
    energy: float
    acousticness: float


SCORING_STRATEGIES = {
    "baseline": ScoringStrategy(0.4, 0.3, 0.2, 0.1),
    "genre-first": ScoringStrategy(0.4, 0.3, 0.2, 0.1),
    "mood-first": ScoringStrategy(0.2, 0.5, 0.2, 0.1),
    "energy-focus": ScoringStrategy(0.2, 0.3, 0.4, 0.1),
}


def _positive_value(value, name: str) -> float:
    """Require a positive finite duration or other numerical value."""
    try:
        number = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{name} must be a positive finite number") from error
    if not math.isfinite(number) or number <= 0:
        raise ValueError(f"{name} must be a positive finite number")
    return number


def _decade(value) -> int:
    """Require a release decade from 1900 through 2090."""
    try:
        number = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError("release_decade must be a decade from 1900 to 2090") from error
    if not math.isfinite(number) or not 1900 <= number <= 2090 or number % 10:
        raise ValueError("release_decade must be a decade from 1900 to 2090")
    return int(number)


def _tags(value) -> set:
    """Normalize semicolon-delimited CSV tags or an iterable of profile tags."""
    if isinstance(value, str):
        value = value.split(";")
    return {tag.strip().casefold() for tag in value if tag.strip()}


def _advanced_similarities(user_prefs: Dict, song: Dict) -> List[Tuple[str, float]]:
    """Compute only advanced similarities explicitly requested by the listener."""
    similarities = []
    if user_prefs.get("target_popularity") is not None:
        target = _unit_value(float(user_prefs["target_popularity"]) / 100, "target_popularity / 100")
        actual = _unit_value(float(song["popularity"]) / 100, "popularity / 100")
        similarities.append(("popularity", 1 - abs(actual - target)))
    if user_prefs.get("preferred_decade") is not None:
        distance = abs(_decade(song["release_decade"]) - _decade(user_prefs["preferred_decade"]))
        similarities.append(("release decade", max(0.0, 1 - distance / 100)))
    if user_prefs.get("mood_tags"):
        desired, actual = _tags(user_prefs["mood_tags"]), _tags(song["detailed_mood_tags"])
        if not desired:
            raise ValueError("mood_tags must contain at least one nonempty tag")
        similarities.append(("detailed mood tags", len(desired & actual) / len(desired)))
    if user_prefs.get("target_duration_seconds") is not None:
        target = _positive_value(user_prefs["target_duration_seconds"], "target_duration_seconds")
        actual = _positive_value(song["duration_seconds"], "duration_seconds")
        similarities.append(("duration", max(0.0, 1 - abs(actual - target) / 300)))
    if user_prefs.get("target_instrumentalness") is not None:
        target = _unit_value(user_prefs["target_instrumentalness"], "target_instrumentalness")
        actual = _unit_value(song["instrumentalness"], "instrumentalness")
        similarities.append(("instrumentalness", 1 - abs(actual - target)))
    return similarities


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
                song["tempo_bpm"] = _positive_value(song["tempo_bpm"], "tempo_bpm")
                song["popularity"] = int(song["popularity"])
                _unit_value(song["popularity"] / 100, "popularity / 100")
                song["release_decade"] = _decade(song["release_decade"])
                song["duration_seconds"] = _positive_value(song["duration_seconds"], "duration_seconds")
                song["instrumentalness"] = _unit_value(song["instrumentalness"], "instrumentalness")
                song["detailed_mood_tags"] = tuple(sorted(_tags(song["detailed_mood_tags"])))
                if not song["detailed_mood_tags"]:
                    raise ValueError("detailed_mood_tags must contain a tag")
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
    try:
        strategy = SCORING_STRATEGIES[recipe]
    except KeyError as error:
        raise ValueError(f"Unknown scoring recipe: {recipe}") from error
    genre_weight, mood_weight = strategy.genre, strategy.mood
    energy_weight, acoustic_weight = strategy.energy, strategy.acousticness
    advanced = _advanced_similarities(user_prefs, song)
    active_weight = genre_weight + mood_weight + energy_weight
    if likes_acoustic is not None:
        active_weight += acoustic_weight
    active_weight += 0.1 * len(advanced)
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
        reasons.append(f"acousticness omitted; active weights normalized by {active_weight:.2f}")
    for name, similarity in advanced:
        points = 0.1 * similarity / active_weight
        score += points
        reasons.append(f"{name} similarity {similarity:.3f} (+{points:.3f})")
    return score, reasons


def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5, *, recipe: str = "baseline", diversity: bool = False, artist_penalty: float = 0.12, genre_penalty: float = 0.06) -> List[Tuple[Dict, float, str]]:
    """Rank by similarity or greedily adjust for repeated artists and genres."""
    artist_penalty = _unit_value(artist_penalty, "artist_penalty")
    genre_penalty = _unit_value(genre_penalty, "genre_penalty")
    if k <= 0:
        return []
    scored = []
    for song in songs:
        score, reasons = score_song(user_prefs, song, recipe=recipe)
        scored.append((song, score, "; ".join(reasons)))
    if not diversity:
        return sorted(scored, key=lambda result: (-result[1], int(result[0]["id"])))[:k]
    selected, artist_counts, genre_counts = [], {}, {}
    while scored and len(selected) < k:
        candidates = []
        for index, (song, base_score, explanation) in enumerate(scored):
            artist = song["artist"].strip().casefold()
            genre = song["genre"].strip().casefold()
            artist_cost = artist_penalty * artist_counts.get(artist, 0)
            genre_cost = genre_penalty * genre_counts.get(genre, 0)
            adjusted = base_score - artist_cost - genre_cost
            candidates.append((adjusted, int(song["id"]), index, artist_cost, genre_cost))
        adjusted, _, index, artist_cost, genre_cost = min(candidates, key=lambda item: (-item[0], item[1]))
        song, base_score, explanation = scored.pop(index)
        explanation += (f"; base score {base_score:.3f}; repeated artist penalty (-{artist_cost:.3f})"
                        f"; repeated genre penalty (-{genre_cost:.3f}); adjusted score {adjusted:.3f}")
        selected.append((song, adjusted, explanation))
        artist = song["artist"].strip().casefold()
        genre = song["genre"].strip().casefold()
        artist_counts[artist] = artist_counts.get(artist, 0) + 1
        genre_counts[genre] = genre_counts.get(genre, 0) + 1
    return selected


class Recommender:
    """Adapt Song and UserProfile objects to the shared scoring implementation."""

    def __init__(self, songs: List[Song]):
        """Retain the supplied catalog without reordering it."""
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5, *, recipe: str = "baseline", diversity: bool = False) -> List[Song]:
        """Return the top k original Song objects using the shared ranking rules."""
        records = [asdict(song) for song in self.songs]
        originals = {id(record): song for record, song in zip(records, self.songs)}
        return [originals[id(record)] for record, _, _ in recommend_songs(asdict(user), records, k, recipe=recipe, diversity=diversity)]

    def explain_recommendation(self, user: UserProfile, song: Song, *, recipe: str = "baseline", diversity: bool = False) -> str:
        """Explain the same weighted contributions used to rank this song."""
        if diversity:
            records = [asdict(item) for item in self.songs]
            target = next((record for record, original in zip(records, self.songs) if original is song), None)
            if target is None:
                raise ValueError("Diversity explanations require a song from this catalog")
            ranking = recommend_songs(asdict(user), records, len(records), recipe=recipe, diversity=True)
            return next(explanation for record, _, explanation in ranking if record is target)
        _, reasons = score_song(asdict(user), asdict(song), recipe=recipe)
        return "; ".join(reasons)

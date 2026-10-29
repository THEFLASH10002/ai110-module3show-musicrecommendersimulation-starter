"""Run the CLI-first music recommender with the default pop/happy profile."""

import argparse
from pathlib import Path
import textwrap

from .recommender import SCORING_STRATEGIES, load_songs, recommend_songs


EVALUATION_PROFILES = {
    "High-Energy Pop": {"genre": "pop", "mood": "happy", "energy": 0.8},
    "Chill Lofi": {"genre": "lofi", "mood": "chill", "energy": 0.4, "likes_acoustic": True},
    "Deep Intense Rock": {"genre": "rock", "mood": "intense", "energy": 0.95, "likes_acoustic": False},
    "Conflicting Lofi": {"genre": "lofi", "mood": "sad", "energy": 0.9, "likes_acoustic": True},
}


def print_recommendations(user_prefs: dict, songs: list, recipe: str, *, diversity: bool = False) -> None:
    """Print the top five songs and reasons for one profile and scoring recipe."""
    recommendations = recommend_songs(user_prefs, songs, k=5, recipe=recipe, diversity=diversity)
    print(f"Profile: genre={user_prefs['genre']}, mood={user_prefs['mood']}, target energy={user_prefs['energy']:.2f}")
    if "likes_acoustic" in user_prefs:
        print(f"Acoustic preference: {user_prefs['likes_acoustic']}")
    advanced = {key: value for key, value in user_prefs.items() if key in (
        "target_popularity", "preferred_decade", "mood_tags", "target_duration_seconds", "target_instrumentalness")}
    if advanced:
        print(f"Advanced preferences: {advanced}")
    print(f"Mode: {recipe} | Diversity: {'on' if diversity else 'off'}")
    widths = (4, 20, 15, 7, 66)
    headers = ("Rank", "Song", "Artist", "Score", "Reasons")
    border = "+" + "+".join("-" * (width + 2) for width in widths) + "+"
    print("\nTop 5 recommendations (adjusted scores when diversity is on):")
    print(border)
    print("| " + " | ".join(f"{header:<{width}}" for header, width in zip(headers, widths)) + " |")
    print(border)
    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        cells = (str(rank), song['title'], song['artist'], f"{score:.3f}", explanation)
        wrapped = [textwrap.wrap(cell, width=width) or [""] for cell, width in zip(cells, widths)]
        for line in range(max(map(len, wrapped))):
            print("| " + " | ".join(
                f"{(parts[line] if line < len(parts) else ''):<{width}}"
                for parts, width in zip(wrapped, widths)) + " |")
        print(border)
    print()


def main() -> None:
    """Load the catalog and print ranked songs with their scoring reasons."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evaluate", action="store_true", help="run all four evaluation profiles")
    parser.add_argument("--mode", "--recipe", dest="recipe", choices=tuple(SCORING_STRATEGIES), default="baseline")
    parser.add_argument("--diversity", action="store_true", help="penalize repeated artists and genres")
    parser.add_argument("--advanced", action="store_true", help="activate preferences for all five new attributes")
    args = parser.parse_args()
    catalog = Path(__file__).resolve().parents[1] / "data" / "songs.csv"
    songs = load_songs(catalog)
    user_prefs = {"genre": "pop", "mood": "happy", "energy": 0.8}
    print(f"Loaded songs: {len(songs)}")
    if args.evaluate:
        for name, profile in EVALUATION_PROFILES.items():
            print(f"=== {name} | {args.recipe} ===")
            print_recommendations(with_advanced_preferences(profile) if args.advanced else profile,
                                  songs, args.recipe, diversity=args.diversity)
    else:
        print_recommendations(with_advanced_preferences(user_prefs) if args.advanced else user_prefs,
                              songs, args.recipe, diversity=args.diversity)


def with_advanced_preferences(profile: dict) -> dict:
    """Add explicit example targets for all five advanced attributes."""
    return {**profile, "target_popularity": 60, "preferred_decade": 2010,
            "mood_tags": (profile["mood"], "nostalgic"), "target_duration_seconds": 210,
            "target_instrumentalness": 0.9 if profile.get("likes_acoustic") else 0.1}


if __name__ == "__main__":
    main()

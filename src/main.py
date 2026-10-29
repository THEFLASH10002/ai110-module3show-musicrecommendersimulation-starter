"""Run the CLI-first music recommender with the default pop/happy profile."""

import argparse
from pathlib import Path

from .recommender import load_songs, recommend_songs


EVALUATION_PROFILES = {
    "High-Energy Pop": {"genre": "pop", "mood": "happy", "energy": 0.8},
    "Chill Lofi": {"genre": "lofi", "mood": "chill", "energy": 0.4, "likes_acoustic": True},
    "Deep Intense Rock": {"genre": "rock", "mood": "intense", "energy": 0.95, "likes_acoustic": False},
    "Conflicting Lofi": {"genre": "lofi", "mood": "sad", "energy": 0.9, "likes_acoustic": True},
}


def print_recommendations(user_prefs: dict, songs: list, recipe: str) -> None:
    """Print the top five songs and reasons for one profile and scoring recipe."""
    recommendations = recommend_songs(user_prefs, songs, k=5, recipe=recipe)
    print(f"Profile: genre={user_prefs['genre']}, mood={user_prefs['mood']}, target energy={user_prefs['energy']:.2f}")
    if "likes_acoustic" in user_prefs:
        print(f"Acoustic preference: {user_prefs['likes_acoustic']}")
    print("\nTop 5 recommendations:\n")
    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        print(f"{rank}. {song['title']} - {song['artist']} | Score: {score:.3f}")
        print(f"   Reasons: {explanation}")
        print()


def main() -> None:
    """Load the catalog and print ranked songs with their scoring reasons."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evaluate", action="store_true", help="run all four evaluation profiles")
    parser.add_argument("--recipe", choices=("baseline", "energy-focus"), default="baseline")
    args = parser.parse_args()
    catalog = Path(__file__).resolve().parents[1] / "data" / "songs.csv"
    songs = load_songs(catalog)
    user_prefs = {"genre": "pop", "mood": "happy", "energy": 0.8}
    print(f"Loaded songs: {len(songs)}")
    if args.evaluate:
        for name, profile in EVALUATION_PROFILES.items():
            print(f"=== {name} | {args.recipe} ===")
            print_recommendations(profile, songs, args.recipe)
    else:
        print_recommendations(user_prefs, songs, args.recipe)


if __name__ == "__main__":
    main()

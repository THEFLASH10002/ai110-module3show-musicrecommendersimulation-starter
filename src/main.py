"""Run the CLI-first music recommender with the default pop/happy profile."""

from pathlib import Path

from .recommender import load_songs, recommend_songs


def main() -> None:
    """Load the catalog and print ranked songs with their scoring reasons."""
    catalog = Path(__file__).resolve().parents[1] / "data" / "songs.csv"
    songs = load_songs(catalog)
    user_prefs = {"genre": "pop", "mood": "happy", "energy": 0.8}
    recommendations = recommend_songs(user_prefs, songs, k=5)

    print(f"Loaded songs: {len(songs)}")
    print("Profile: genre=pop, mood=happy, target energy=0.80")
    print("\nTop 5 recommendations:\n")
    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        print(f"{rank}. {song['title']} - {song['artist']} | Score: {score:.3f}")
        print(f"   Reasons: {explanation}")
        print()


if __name__ == "__main__":
    main()

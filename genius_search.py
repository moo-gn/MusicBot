import re

def smart_clean_lyrics(lyrics: str):
        # Step 1: Slice from after the last 'Read More'
    if "Read More" in lyrics:
        lyrics = lyrics.split("Read More")[-1]

    # Step 2: Slice from after the last 'Contributors'
    if "Contributors" in lyrics:
        lyrics = lyrics.split("Lyrics")[-1]

    return lyrics.strip()

def chunk_lyrics(lyrics: str, max_chunk_size: int = 4000):
    lines = lyrics.splitlines()
    chunks = []
    current_chunk = ""

    for line in lines:
        # +1 for newline
        if len(current_chunk) + len(line) + 1 > max_chunk_size:
            chunks.append(current_chunk.strip())
            current_chunk = ""

        current_chunk += line + "\n"

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks
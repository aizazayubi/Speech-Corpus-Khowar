# main.py
import os
import argparse
from pathlib import Path
import pandas as pd
from pydub import AudioSegment, silence
from tqdm import tqdm

from utils import download_audio, convert_to_wav

# ---------- helper functions ----------
def split_by_silence_and_chunk(wav_path: str,
                               out_dir: str,
                               min_silence_len: int = 450,
                               silence_thresh_delta: int = 14,
                               keep_silence: int = 120,
                               min_chunk_s: float = 3.0,
                               max_chunk_s: float = 8.0):
    """
    1) Split by silence using pydub.split_on_silence
    2) Post-process segments:
       - merge adjacent segments if too short (< min_chunk_s)
       - split segments longer than max_chunk_s into multiple pieces
    Export each chunk as WAV.
    """
    audio = AudioSegment.from_wav(wav_path)
    # determine silence threshold relative to audio dBFS
    silence_thresh = audio.dBFS - silence_thresh_delta

    raw_chunks = silence.split_on_silence(
        audio,
        min_silence_len=min_silence_len,
        silence_thresh=silence_thresh,
        keep_silence=keep_silence
    )

    # normalize: ensure all chunks are AudioSegment and non-empty
    chunks = [c for c in raw_chunks if len(c) > 0]

    final_chunks = []
    # Merge small chunks with next until >= min_chunk_s
    i = 0
    while i < len(chunks):
        current = chunks[i]
        dur_s = len(current) / 1000.0
        if dur_s >= min_chunk_s:
            final_chunks.append(current)
            i += 1
            continue
        # merge with next(s)
        j = i + 1
        merged = current
        while j < len(chunks) and (len(merged)/1000.0) < min_chunk_s:
            merged += chunks[j]
            j += 1
        final_chunks.append(merged)
        i = j

    # Now split any chunk longer than max_chunk_s into pieces
    processed = []
    max_ms = int(max_chunk_s * 1000)
    for c in final_chunks:
        if len(c) <= max_ms:
            processed.append(c)
        else:
            start = 0
            while start < len(c):
                piece = c[start:start + max_ms]
                processed.append(piece)
                start += max_ms

    # Export processed chunks
    os.makedirs(out_dir, exist_ok=True)
    basename = Path(wav_path).stem
    exported = []
    for idx, chunk in enumerate(processed, start=1):
        out_path = os.path.join(out_dir, f"{basename}_chunk{idx:03d}.wav")
        chunk.export(out_path, format="wav")
        exported.append(out_path)
    return exported

# ---------- CLI ----------
def process_csv(csv_path: str, tmp_dir: str, out_root: str,
                min_silence_len: int, silence_thresh_delta: int,
                keep_silence: int, min_chunk_s: float, max_chunk_s: float):
    df = pd.read_csv(csv_path)
    if 'url' not in df.columns:
        raise ValueError("CSV must have 'url' column")
    for url in tqdm(df['url'].dropna().unique(), desc="Links"):
        try:
            print(f"\nProcessing: {url}")
            download_folder = os.path.join(tmp_dir, "downloads")
            downloaded = download_audio(url, download_folder)
            # convert to wav
            wav_out = os.path.splitext(downloaded)[0] + ".wav"
            if not os.path.exists(wav_out):
                wav_out = convert_to_wav(downloaded, wav_out)
            # create output folder per video
            safe_name = Path(wav_out).stem
            out_dir = os.path.join(out_root, safe_name)
            exported = split_by_silence_and_chunk(
                wav_out, out_dir,
                min_silence_len=min_silence_len,
                silence_thresh_delta=silence_thresh_delta,
                keep_silence=keep_silence,
                min_chunk_s=min_chunk_s,
                max_chunk_s=max_chunk_s
            )
            print(f"Exported {len(exported)} chunks to {out_dir}")
        except Exception as e:
            print(f"Error for {url}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download audio from YouTube links and split into 3-8s WAV chunks")
    parser.add_argument("csv", help="input CSV (with header 'url')")
    parser.add_argument("--tmp", default="./tmp", help="temporary folder")
    parser.add_argument("--out", default="./output_chunks", help="output folder")
    parser.add_argument("--min_silence_len", type=int, default=450, help="ms")
    parser.add_argument("--silence_thresh_delta", type=int, default=14, help="dB below audio.dBFS")
    parser.add_argument("--keep_silence", type=int, default=120, help="ms to keep at edges of chunks")
    parser.add_argument("--min_chunk_s", type=float, default=3.0)
    parser.add_argument("--max_chunk_s", type=float, default=8.0)
    args = parser.parse_args()

    process_csv(
        args.csv, args.tmp, args.out,
        args.min_silence_len, args.silence_thresh_delta,
        args.keep_silence, args.min_chunk_s, args.max_chunk_s
    )

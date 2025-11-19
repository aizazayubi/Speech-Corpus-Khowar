# utils.py
import os
import subprocess
from pathlib import Path
from yt_dlp import YoutubeDL
from pydub import AudioSegment, silence

def download_audio(url: str, out_dir: str) -> str:
    """
    Download best audio from YouTube and return path to .m4a file.
    Filenames are based on video ID to avoid Windows invalid characters.
    """
    os.makedirs(out_dir, exist_ok=True)

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(out_dir, '%(id)s.%(ext)s'),  # safe filename
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'm4a',
        }],
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
    }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        video_id = info.get('id')
        if not video_id:
            raise ValueError("Could not get video ID")
        file_path = os.path.join(out_dir, f"{video_id}.m4a")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Downloaded file not found: {file_path}")
        return file_path

def convert_to_wav(input_path: str, output_path: str) -> str:
    """
    Convert any audio file to WAV using ffmpeg.
    Output is mono, 16kHz.
    """
    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-ar", "16000",
        "-ac", "1",
        output_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return output_path

def split_by_silence_and_chunk(wav_path: str,
                               out_dir: str,
                               min_silence_len: int = 450,
                               silence_thresh_delta: int = 14,
                               keep_silence: int = 120,
                               min_chunk_s: float = 3.0,
                               max_chunk_s: float = 8.0) -> list[str]:
    """
    Split WAV into chunks based on silence:
    - min_silence_len: minimum silence to split (ms)
    - silence_thresh_delta: dBFS below audio average to consider silence
    - keep_silence: ms of silence to keep around each chunk
    - min_chunk_s / max_chunk_s: final chunk length constraints
    Returns list of exported chunk file paths.
    """
    audio = AudioSegment.from_wav(wav_path)
    silence_thresh = audio.dBFS - silence_thresh_delta

    raw_chunks = silence.split_on_silence(
        audio,
        min_silence_len=min_silence_len,
        silence_thresh=silence_thresh,
        keep_silence=keep_silence
    )

    # Remove empty chunks
    chunks = [c for c in raw_chunks if len(c) > 0]

    # Merge small chunks with next until >= min_chunk_s
    final_chunks = []
    i = 0
    while i < len(chunks):
        current = chunks[i]
        dur_s = len(current) / 1000.0
        if dur_s >= min_chunk_s:
            final_chunks.append(current)
            i += 1
            continue
        j = i + 1
        merged = current
        while j < len(chunks) and (len(merged)/1000.0) < min_chunk_s:
            merged += chunks[j]
            j += 1
        final_chunks.append(merged)
        i = j

    # Split chunks longer than max_chunk_s
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

    os.makedirs(out_dir, exist_ok=True)
    basename = Path(wav_path).stem
    exported = []
    for idx, chunk in enumerate(processed, start=1):
        out_path = os.path.join(out_dir, f"{basename}_chunk{idx:03d}.wav")
        chunk.export(out_path, format="wav")
        exported.append(out_path)
    return exported

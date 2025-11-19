
# **Speech-Corpus-Khowar**

Tools for downloading speech from YouTube, converting it to WAV, and slicing it into 3–8 second chunks suitable for **Wav2Vec2** and other self-supervised speech models.
Designed for **low-resource languages** where building datasets is difficult.

---

## **✨ Features**

* Download audio from YouTube using safe filenames
* Convert audio to **mono 16kHz WAV** (Wav2Vec2 preferred format)
* Split audio into chunks based on silence
* Normalize chunk duration to **3–8 seconds** for robust model training
* Export ready-to-use WAV files for ASR, SSL training, or dataset creation

---

## **📦 Requirements**

Install all dependencies:

```bash
pip install -r requirements.txt
```

Dependencies:

* `yt-dlp`
* `pydub`
* `pandas`
* `tqdm`
* `ffmpeg` (must be installed on your system)

---

## **📂 Project Structure**

```
Speech-Corpus-Khowar/
├── utils.py
├── main.py
├── urls.csv
├── requirements.txt
└── README.md
```

---

## **🚀 Usage**

### **1. Download audio**

```python
from utils import download_audio
m4a_path = download_audio(url, "tmp")
```

### **2. Convert to WAV**

```python
from utils import convert_to_wav
wav_path = convert_to_wav(m4a_path, m4a_path.replace(".m4a", ".wav"))
```

### **3. Chunk the audio (3–8 seconds)**

```python
from utils import split_by_silence_and_chunk
chunks = split_by_silence_and_chunk(wav_path, "wav_chunks")
```

---

## **🎯 Goal**

This tool is built to help researchers, linguists, and developers automatically generate **Wav2Vec2-friendly datasets for low-resource languages**, such as Khowar, Dakhni, Wakhi, Burushaski, Pashto, or any language with limited audio resources.

Wav2Vec2 and other SSL models perform best when given:

* **Clean**
* **Short-duration**
* **Mono, 16kHz**
* **Natural speech chunks**

This script automates that entire pipeline.

---

## **📜 Example CSV**

Provide YouTube links in a file like:

```csv
url
https://www.youtube.com/watch?v=XXXXXXXX
```

---

## **🛠 Notes**

* Audio chunks are saved in WAV 16kHz mono format.
* Chunks are automatically adjusted to respect 3–8 second limits.
* This tool avoids invalid Windows filenames by using YouTube video IDs.

---

## **🤝 Contributions**

Pull requests and improvements are welcome—especially extensions for:

* Automatic transcription
* Metadata generation
* Language tagging tools
* Whisper / Wav2Vec2 dataset integration

# Interview Cheat Sheet

Real-time AI interview assistant that captures system audio, detects questions, and provides intelligent answers using GPU-accelerated speech recognition and LLM processing.

## Features

- **System Audio Capture**: Captures all PC audio output (YouTube, Zoom, etc.) via Stereo Mix
- **GPU Acceleration**: CUDA-accelerated Faster Whisper for real-time transcription
- **Smart Question Detection**: Automatically identifies complete interview questions
- **AI-Powered Answers**: Generates responses using Ollama or OpenRouter
- **Duplicate Filtering**: Prevents re-processing similar questions
- **Real-time Processing**: Sub-second latency with background processing

## System Requirements

| Component | Requirement |
|-----------|-------------|
| OS | Windows (Stereo Mix), Linux (PulseAudio), macOS |
| Python | 3.8 or higher |
| GPU | NVIDIA GPU with CUDA 11.8+ (optional) |
| RAM | 4GB minimum, 8GB recommended |

---

## Installation

### 1. Enable Stereo Mix (Windows)

1. Right-click sound icon in system tray
2. Select "Sounds" → "Recording" tab
3. Right-click → "Show Disabled Devices"
4. Right-click "Stereo Mix" → "Enable"
5. Set as default recording device (optional)

### 2. Install Dependencies

**Using uv (Recommended)**

```bash
# Install uv
pip install uv

# Clone repository
git clone https://github.com/yourusername/interview-cheatsheet.git
cd interview-cheatsheet

# Install base dependencies
uv sync

# For GPU support
uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
uv pip install nvidia-cudnn-cu11
```

**Using pip**

```bash
# Install base dependencies
pip install -e .

# For GPU support  
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install nvidia-cudnn-cu11
```

### 3. Setup Ollama

```bash
# Install Ollama from https://ollama.ai

# Pull a model
ollama pull llama3.2

# Start server
ollama serve
```

### 4. Configure
cp .env.example

```

### 5. Run

```bash
python main.py
```

---

## Usage

The application will:
1. Auto-detect Stereo Mix audio device
2. Capture all system audio in real-time
3. Transcribe speech using Faster Whisper
4. Detect interview questions automatically
5. Generate AI-powered answers via Ollama

**Test it:**
- Play interview videos on YouTube
- Join online meetings (Zoom/Teams)
- Questions are detected and answered automatically

---

## Example Output

```
Interview Cheat Sheet
============================================================
Initializing STT...

Available audio input devices:
  [9] Stereo Mix (Realtek HD Audio Stereo input)

Found system audio device: Stereo Mix
Ready!

System audio capture started!
Listening to all PC audio (Stereo Mix)...
Will detect interview questions and suggest answers
Press Ctrl+C to stop
------------------------------------------------------------

[Transcribed]: Thank you for joining us today.

============================================================
QUESTION:
   Tell me about yourself and your background
------------------------------------------------------------
Asking Ollama...

ANSWER:
I'm a software engineer with 5 years of experience in full-stack 
development, specializing in Python and React. I've led teams at 
two startups, building scalable web applications. Most recently, 
I architected a microservices platform that reduced deployment 
time by 60%.
============================================================
```

---

## Configuration

All settings in `.env`:

```bash
# LLM Provider (ollama or openrouter)
LLM_PROVIDER=ollama

# Ollama Settings
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2  # llama2, mistral, codellama, etc.

# OpenRouter Settings (if using cloud)
OPENROUTER_API_KEY=your_key_here
OPENROUTER_MODEL=meta-llama/llama-3.1-8b-instruct:free

# STT Settings
STT_DEVICE=cuda  # cuda or cpu
STT_MODEL=base.en  # tiny.en, base.en, small.en, medium.en, large
```

### Model Recommendations

| Speed | STT Model | LLM Model |
|-------|-----------|-----------|
| Fast | tiny.en | llama3.2 |
| Balanced | base.en | llama3.2 |
| Accurate | medium.en | llama3.1:70b |

---

## Troubleshooting

**Stereo Mix not found**
- Enable in Sound settings (see Installation step 1)
- Install Realtek HD Audio drivers
- Alternative: Use VB-Audio Virtual Cable

**CUDA errors**
```bash
pip install nvidia-cudnn-cu11
# or switch to CPU: STT_DEVICE=cpu in .env
```

**Invalid device error**
- Ensure Stereo Mix is enabled and not muted
- Set as default recording device
- Update audio drivers

**No questions detected**
- Questions must be 5+ words
- Must start with question words (what, how, why, etc.)
- Check audio is transcribing correctly

**Ollama connection failed**
```bash
ollama serve
ollama pull llama3.2
# Check OLLAMA_BASE_URL in .env
```

**Slow transcription**
- Use GPU mode (STT_DEVICE=cuda)
- Switch to smaller model (STT_MODEL=tiny.en)
- Close other GPU applications

---

## Project Structure

```
interview-cheatsheet/
├── src/
│   ├── stt.py              # Speech-to-text with system audio capture
│   └── llm_processor.py    # LLM integration (Ollama/OpenRouter)
├── main.py                  # Main application entry point
├── pyproject.toml           # Dependencies and configuration
├── README.md                # Documentation
└── .env                     # User configuration
```

## Acknowledgments

The speech-to-text engine (`src/stt.py`) is forked from [Real-time-STT](https://github.com/rudymohammadbali/Real-time-STT) by rudymohammadbali, licensed under GPL-3.0.

## License

MIT License

## Contributing

Pull requests are welcome. For major changes, please open an issue first.

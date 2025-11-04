# Interview Cheat Sheet

Real-time AI interview assistant that captures system audio, detects questions, and provides intelligent answers using GPU-accelerated speech recognition and LLM.

## Features

- Faster Whisper transcription
- Question detection
- AI-powered answers
- Real-time processing

## Requirements

- Python 3.8+
- NVIDIA GPU with CUDA 11.8+ (optional)
- Ollama or OpenRouter API key

## Installation

```bash
# Clone
git clone https://github.com/Gary-Chau/Interview-CheatSheet.git
cd Interview-CheatSheet

# Install dependencies
uv sync

# GPU support
uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
uv pip install nvidia-cudnn-cu11
```

## Setup

```bash
# Install and start Ollama
ollama pull llama3.2
ollama serve

# Configure
cp .env.example .env
# Edit .env with your settings

# Setup database
# 1. Edit database/self_intro.txt - Write YOUR self-introduction
# 2. Create database/company_<name>.txt - Research about target companies
#
# Example: database/company_nvidia.txt, database/company_google.txt
# Include: company overview, culture, recent news, tech stack, interview tips
```

## Run

```bash
python main.py
```

A GUI window will open. Enter:
- Company name
- Position
- Date (auto-fills today)

Click "Start" - the app loads your self-intro + company research to generate personalized answers.

## Model Recommendations

| Speed | STT Model | LLM Model |
|-------|-----------|-----------|
| Fast | tiny.en | llama3.2 |
| Balanced | base.en | llama3.2 |
| Accurate | medium.en | llama3.1:70b |

## Acknowledgments

Speech-to-text engine forked from [Real-time-STT](https://github.com/rudymohammadbali/Real-time-STT) (GPL-3.0)

## License

MIT

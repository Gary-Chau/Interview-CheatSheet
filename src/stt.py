"""
Speech-to-Text Module with System Audio Capture

Forked from: https://github.com/rudymohammadbali/Real-time-STT
Original Author: rudymohammadbali
License: GPL-3.0

"""

import threading
import queue
import io
import logging
import wave
import struct
import os
import sys

# Fix OpenMP duplicate library issue
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# Add cuDNN and cuBLAS to PATH before importing CUDA libraries
try:
    import nvidia.cudnn
    cudnn_path = os.path.dirname(nvidia.cudnn.__file__)
    
    paths_to_add = []
    if os.path.exists(cudnn_path):
        paths_to_add.append(cudnn_path)
        os.add_dll_directory(cudnn_path)
    
    try:
        import nvidia.cublas.lib
        cublas_path = os.path.dirname(nvidia.cublas.lib.__file__)
        if os.path.exists(cublas_path):
            paths_to_add.append(cublas_path)
            os.add_dll_directory(cublas_path)
    except:
        pass
    
    if paths_to_add:
        os.environ['PATH'] = os.pathsep.join(paths_to_add) + os.pathsep + os.environ.get('PATH', '')
except Exception as e:
    pass  # Silently ignore, will try CPU fallback

import pyaudio
import speech_recognition as sr

import time
from faster_whisper import WhisperModel


class STT:
    """Real-time Speech to Text class using Faster WhisperModel and speech_recognition."""

    def __init__(self, model_size: str = "medium.en", device: str = "cuda", compute_type: str = "float16",
                 language: str = "en", logging_level: str = None):
        """Initialize the STT object."""
        self.recorder = sr.Recognizer()
        self.data_queue = queue.Queue()
        self.transcription = ['']
        self.last_transcription = ""
        self.is_listening = True

        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.language = language
        self.default_mic = self.setup_mic()
        
        # PyAudio parameters
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 2
        self.RATE = 16000
        self.audio_buffer = []
        self.buffer_duration = 5  # seconds of audio to buffer before transcribing (increased for complete questions)

        self.model = WhisperModel(self.model_size, device=self.device, compute_type=self.compute_type)

        self.lock = threading.Lock()

        if logging_level:
            self.configure_logging(level=logging_level)

        self.thread = threading.Thread(target=self.transcribe)
        self.thread.setDaemon(True)
        self.thread.start()

        logging.info("Ready!\n")
        print("Ready!\n")

    def transcribe(self):
        """Transcribe the audio data from the queue."""
        while self.is_listening:
            audio_data = self.data_queue.get()

            if audio_data == 'STOP':
                break

            segments, info = self.model.transcribe(audio_data, beam_size=5, language=self.language, vad_filter=True)
            for segment in segments:
                text = segment.text.strip()
                logging.info("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, text))
                with self.lock:
                    self.transcription.append(text)
                    self.last_transcription = text

            self.data_queue.task_done()
            time.sleep(0.25)

    def audio_callback(self, in_data, frame_count, time_info, status):
        """PyAudio callback function for capturing audio."""
        if status:
            logging.warning(f"Audio callback status: {status}")
        
        self.audio_buffer.append(in_data)
        
        # Check if we have enough audio buffered
        buffer_size = len(self.audio_buffer) * self.CHUNK / self.RATE
        if buffer_size >= self.buffer_duration:
            try:
                # Convert buffer to WAV format
                audio_data = b''.join(self.audio_buffer)
                wav_buffer = io.BytesIO()
                
                with wave.open(wav_buffer, 'wb') as wf:
                    wf.setnchannels(self.CHANNELS)
                    wf.setsampwidth(self.sample_width)
                    wf.setframerate(self.RATE)
                    wf.writeframes(audio_data)
                
                wav_buffer.seek(0)
                self.data_queue.put(wav_buffer)
                self.audio_buffer = []
            except Exception as e:
                logging.error(f"Error in audio callback: {e}")
                self.audio_buffer = []
        
        return (in_data, pyaudio.paContinue)

    def listen(self):
        """Start listening to the audio source using PyAudio directly."""
        try:
            self.p = pyaudio.PyAudio()
            
            # Get device info
            device_info = self.p.get_device_info_by_index(self.default_mic)
            
            # Use device's default sample rate
            self.RATE = int(device_info['defaultSampleRate'])
            
            # Adjust channels if device doesn't support stereo
            if device_info['maxInputChannels'] < 2:
                self.CHANNELS = 1
                logging.info("Device only supports mono audio")
            else:
                self.CHANNELS = min(2, int(device_info['maxInputChannels']))
            
            # Get sample width
            self.sample_width = self.p.get_sample_size(self.FORMAT)
            
            logging.info(f"Audio settings: {self.RATE}Hz, {self.CHANNELS} channel(s)")
            logging.info("Starting background audio capture from system audio...")
            print(f"Listening to system audio on: {device_info['name']}")
            print(f"Sample rate: {self.RATE}Hz, Channels: {self.CHANNELS}")
            print("(say 'stop' to end)\n")
            
            # Try to open the stream with the device's native settings
            self.stream = self.p.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                input_device_index=self.default_mic,
                frames_per_buffer=self.CHUNK,
                stream_callback=self.audio_callback
            )
            
            self.stream.start_stream()
            
        except Exception as e:
            logging.error(f"Error starting audio capture: {e}")
            if hasattr(self, 'p'):
                self.p.terminate()
            raise e

    def stop(self):
        """Stop the transcription process."""
        logging.info("Stopping...")
        logging.info(f"Transcription:\n {self.transcription}")
        self.is_listening = False
        
        # Stop PyAudio stream
        if hasattr(self, 'stream') and self.stream:
            self.stream.stop_stream()
            self.stream.close()
        
        if hasattr(self, 'p'):
            self.p.terminate()
        
        self.data_queue.put("STOP")

    def get_last_transcription(self):
        """Get the last transcription and clear it."""
        with self.lock:
            text = self.last_transcription
            self.last_transcription = ""
        return text

    @staticmethod
    def setup_mic():
        """Set up the audio capture device (looks for system audio loopback/Stereo Mix)."""
        p = pyaudio.PyAudio()
        device_index = None
        
        # Keywords to identify system audio loopback devices
        loopback_keywords = ['stereo mix', 'wave out mix', 'loopback', 'what u hear', 'what you hear', 
                            'rec. playback', 'recording playback']
        
        logging.info("Searching for system audio capture device...")
        print("\nAvailable audio input devices:")
        
        # List all input devices and try to find a loopback device
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                device_name = info['name'].lower()
                print(f"  [{i}] {info['name']}")
                logging.info(f"Device index: {i}, Device name: {info['name']}")
                
                # Check if this is a loopback/stereo mix device
                for keyword in loopback_keywords:
                    if keyword in device_name:
                        device_index = i
                        print(f"\n✓ Found system audio device: {info['name']}")
                        logging.info(f"Selected system audio device: {info['name']} (index: {i})")
                        break
                
                if device_index is not None:
                    break
        
        # If no loopback device found, use the first available input device
        if device_index is None:
            for i in range(p.get_device_count()):
                info = p.get_device_info_by_index(i)
                if info['maxInputChannels'] > 0:
                    device_index = i
                    print(f"\n⚠ No system audio loopback device found. Using: {info['name']}")
                    print("\nTo capture system audio on Windows:")
                    print("1. Right-click the sound icon in system tray")
                    print("2. Select 'Sounds' or 'Sound settings'")
                    print("3. Go to 'Recording' tab")
                    print("4. Right-click in empty space and enable 'Show Disabled Devices'")
                    print("5. Find 'Stereo Mix' and enable it")
                    print("6. Set it as default recording device\n")
                    logging.warning(f"Using fallback device: {info['name']} (index: {i})")
                    break
        
        if device_index is None:
            raise Exception("No audio input devices found.")
        
        p.terminate()
        return device_index

    @staticmethod
    def configure_logging(level: str = "INFO"):
        """
        Configure the logging level for the whole application.
        :param level: The desired logging level. Should be one of the following:
        'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'.
        """
        levels = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        logging.basicConfig(level=levels.get(level.upper(), logging.INFO))
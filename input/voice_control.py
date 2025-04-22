import threading
import struct
import pyaudio
import pvporcupine
import speech_recognition as sr
import time


class VoiceCommandListener(threading.Thread):
    def __init__(self, callback, access_key, hotword="jarvis", target_device="Microphone (Realtek(R) Audio)"):
        super().__init__()
        self.callback = callback
        self._stop_event = threading.Event()
        self.hotword = hotword
        self.access_key = access_key
        self.target_device = target_device
        self.daemon = True  # Ensures the thread will exit when the main program terminates
        self._initialized = False

    def get_device_index(self, target_name):
        """Find and return the device index for a given microphone name."""
        pa = None
        try:
            pa = pyaudio.PyAudio()
            for i in range(pa.get_device_count()):
                dev = pa.get_device_info_by_index(i)
                name = dev['name'].lower()
                if target_name.lower() in name:
                    print(f"Using device {i}: {dev['name']}")
                    return i
            raise RuntimeError(f"No device found matching name: {target_name}")
        finally:
            if pa is not None:
                pa.terminate()

    def initialize_audio(self):
        """Initialize all audio components."""
        try:
            device_index = self.get_device_index(self.target_device)
            
            # Initialize Porcupine
            porcupine = pvporcupine.create(
                access_key=self.access_key,
                keywords=[self.hotword]
            )
            
            # Initialize PyAudio
            pa = pyaudio.PyAudio()
            audio_stream = pa.open(
                rate=porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=porcupine.frame_length,
            )
            
            # Initialize SpeechRecognition
            recognizer = sr.Recognizer()
            mic = sr.Microphone(device_index=device_index)
            
            return porcupine, pa, audio_stream, recognizer, mic
        except Exception as e:
            print(f"Failed to initialize audio: {e}")
            raise

    def run(self):
        print("Initializing voice listener...")
        
        try:
            porcupine, pa, audio_stream, recognizer, mic = self.initialize_audio()
            self._initialized = True
            print(f"Voice listener started. Say '{self.hotword}' to begin...")

            while not self._stop_event.is_set():
                try:
                    # Read audio data
                    pcm = audio_stream.read(porcupine.frame_length, exception_on_overflow=False)
                    pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)

                    # Hotword detection
                    if porcupine.process(pcm) >= 0:
                        print(f"Hotword '{self.hotword}' detected! Listening for command...")
                        
                        # Command recognition
                        with mic as source:
                            recognizer.adjust_for_ambient_noise(source, duration=0.5)
                            try:
                                audio = recognizer.listen(source, timeout=3, phrase_time_limit=5)
                                command = recognizer.recognize_google(audio).lower()
                                print(f"Command heard: {command}")
                                self.callback(command)
                            except sr.WaitTimeoutError:
                                print("Listening timed out")
                            except sr.UnknownValueError:
                                print("Could not understand audio")
                            except sr.RequestError as e:
                                print(f"Speech recognition error: {e}")

                except IOError as e:
                    print(f"Audio stream error: {e}")
                    if self._stop_event.is_set():
                        break
                    time.sleep(0.1)  # Brief pause before retrying

        except Exception as e:
            print(f"Voice listener error: {e}")
        finally:
            print("Cleaning up voice listener resources...")
            if hasattr(self, 'audio_stream'):
                audio_stream.stop_stream()
                audio_stream.close()
            if hasattr(self, 'pa'):
                pa.terminate()
            if hasattr(self, 'porcupine'):
                porcupine.delete()
            print("Voice listener stopped")

    def stop(self):
        """Stop the voice listener thread."""
        if not self._stop_event.is_set():
            print("Stopping voice listener...")
            self._stop_event.set()
            # Give it a moment to respond to the stop signal
            time.sleep(0.1)
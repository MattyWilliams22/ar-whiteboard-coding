import pyaudio
import struct
import threading
import speech_recognition as sr
import pvporcupine
from fsm.states import Event
from settings import settings
import time


class VoiceCommandThread(threading.Thread):
    def __init__(
        self, fsm, access_key, settings, hotword_sensitivity=0.5, command_timeout=3
    ):
        super().__init__()
        self.fsm = fsm
        self.access_key = access_key
        self.settings = settings
        self.hotword_sensitivity = hotword_sensitivity  # MOVE THIS UP
        self.command_timeout = command_timeout

        self._needs_restart = threading.Event()
        self._running = threading.Event()
        self._stop_flag = threading.Event()

        # Initialize speech recognizer
        self.recognizer = sr.Recognizer()
        self.recognizer.dynamic_energy_threshold = False
        self.recognizer.energy_threshold = 400

        # Command mapping
        self.command_map = {
            "run": Event.START_RUN,
            "compile": Event.START_RUN,
            "execute": Event.START_RUN,
            "restart": Event.START_RUN,
            "clear": Event.CLEAR,
            "back": Event.CLEAR,
            "stop": Event.CLEAR,
            "idle": Event.CLEAR,
            "exit": Event.EXIT,
            "quit": Event.EXIT,
            "close": Event.EXIT,
        }

        # Initialize Porcupine (after all params are set)
        self.porcupine = None
        self.audio_stream = None
        self.pa = None
        self._initialize_porcupine()

    def _initialize_porcupine(self):
        """Initialize or reinitialize audio components with current settings"""
        # Clean up existing resources
        if self.audio_stream is not None:
            self.audio_stream.close()
        if self.pa is not None:
            self.pa.terminate()
        if self.porcupine is not None:
            self.porcupine.delete()

        try:
            self.pa = pyaudio.PyAudio()
            self.porcupine = pvporcupine.create(
                access_key=self.access_key,
                keywords=["jarvis"],
                sensitivities=[self.hotword_sensitivity],
            )

            self.audio_stream = self.pa.open(
                input_device_index=self.settings["MICROPHONE"],
                rate=self.porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=self.porcupine.frame_length,
            )
            print(
                f"Initialized microphone: {self.pa.get_device_info_by_index(self.settings['MICROPHONE'])['name']}"
            )
        except Exception as e:
            print(f"Failed to initialize audio: {e}")
            raise

    def _process_command(self, command):
        command = command.lower().strip()
        for key, event in self.command_map.items():
            if key in command:
                return event
        return None

    def update_settings(self):
        """Trigger a restart with new settings"""
        self._needs_restart.set()

    def set_active(self):
        self._running.set()
        print("Voice command thread activated.")

    def set_inactive(self):
        self._running.clear()
        print("Voice command thread deactivated.")

    def run(self):
        while not self._stop_flag.is_set():
            if self._running.is_set():
                if self._needs_restart.is_set():
                    self._initialize_porcupine()
                    self._needs_restart.clear()

                try:
                    # Listen for hotword
                    pcm = self.audio_stream.read(self.porcupine.frame_length)
                    pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm)
                    result = self.porcupine.process(pcm)

                    if result >= 0:  # Hotword detected
                        print("Hotword detected! Listening for command...")

                        with sr.Microphone(
                            device_index=self.settings["MICROPHONE"]
                        ) as source:
                            self.recognizer.adjust_for_ambient_noise(
                                source, duration=0.5
                            )
                            audio = self.recognizer.listen(
                                source, timeout=self.command_timeout
                            )

                        try:
                            command = self.recognizer.recognize_google(audio)
                            print(f"Recognized command: {command}")
                            event = self._process_command(command)
                            if event:
                                self.fsm.transition(event)
                        except sr.UnknownValueError:
                            print("Could not understand audio")
                        except sr.RequestError as e:
                            print(f"Recognition error: {e}")
                        except sr.WaitTimeoutError:
                            print("Listening timed out")

                except Exception as e:
                    print(f"Voice command error: {e}")
                    time.sleep(0.1)  # Prevent tight loop on errors

            else:
                time.sleep(1)

    def stop(self):
        self._stop_flag.set()
        if self.audio_stream is not None:
            self.audio_stream.close()
        if self.pa is not None:
            self.pa.terminate()
        if self.porcupine is not None:
            self.porcupine.delete()

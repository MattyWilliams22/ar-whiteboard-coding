# test_voice_simple.py

import threading
import struct
import pyaudio
import pvporcupine
import speech_recognition as sr
import time


class VoiceCommandListener(threading.Thread):
    def __init__(self, callback, access_key, hotword="jarvis", device_name="Microphone (Realtek(R) Audio)"):
        super().__init__()
        self.callback = callback
        self.access_key = access_key
        self.hotword = hotword
        self.device_name = device_name
        self._stop_event = threading.Event()

    def get_device_index(self):
        pa = pyaudio.PyAudio()
        for i in range(pa.get_device_count()):
            dev = pa.get_device_info_by_index(i)
            if self.device_name.lower() in dev['name'].lower():
                print(f"✅ Using device {i}: {dev['name']}")
                return i
        raise RuntimeError(f"No device found matching name: {self.device_name}")

    def run(self):
        device_index = self.get_device_index()

        porcupine = pvporcupine.create(
            access_key=self.access_key,
            keywords=[self.hotword]
        )
        pa = pyaudio.PyAudio()

        stream = pa.open(
            rate=porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=porcupine.frame_length,
            input_device_index=device_index
        )

        recognizer = sr.Recognizer()
        mic = sr.Microphone(device_index=device_index)

        print(f"🎙️ Say '{self.hotword}' to activate...")

        try:
            while not self._stop_event.is_set():
                pcm = stream.read(porcupine.frame_length, exception_on_overflow=False)
                pcm_unpacked = struct.unpack_from("h" * porcupine.frame_length, pcm)

                if porcupine.process(pcm_unpacked) >= 0:
                    print(f"🟢 Hotword '{self.hotword}' detected!")

                    with mic as source:
                        # Quicker ambient noise adjustment
                        recognizer.adjust_for_ambient_noise(source, duration=0.2)
                        print("🎧 Listening for command...")
                        try:
                            audio = recognizer.listen(source, timeout=4, phrase_time_limit=5)
                            command = recognizer.recognize_google(audio).lower()
                            print(f"🗣️ Command: {command}")
                            self.callback(command)
                        except sr.UnknownValueError:
                            print("🤷 Could not understand the command.")
                        except sr.WaitTimeoutError:
                            print("⏱️ Listening timed out.")
                        except sr.RequestError as e:
                            print(f"❌ Recognition error: {e}")

        finally:
            stream.stop_stream()
            stream.close()
            pa.terminate()
            porcupine.delete()

    def stop(self):
        self._stop_event.set()


# --- MAIN TEST ---

def command_callback(cmd):
    print(f"✅ Command callback: {cmd}")
    if "exit" in cmd:
        print("👋 Exiting...")
        listener.stop()

if __name__ == "__main__":
    ACCESS_KEY = "duY+um2g68Nn2ctqSjm2QlIkmyaMRV2mRkgG4XmpjYHruBDK4AsWWw=="
    listener = VoiceCommandListener(callback=command_callback, access_key=ACCESS_KEY)
    listener.start()

    try:
        while listener.is_alive():
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("🛑 Interrupted by user.")
        listener.stop()
        listener.join()

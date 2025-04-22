import speech_recognition as sr
import threading

# Function to handle voice commands
def listen_for_voice_commands():
    recognizer = sr.Recognizer()
    mic = sr.Microphone(device_index=22)

    print("Voice command listener started. Say 'run', 'clear', 'exit'...")

    with mic as source:
        recognizer.adjust_for_ambient_noise(source)

    while True:
        with mic as source:
            print("Listening...")
            try:
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
                command = recognizer.recognize_google(audio).lower()
                print(f"Recognized command: {command}")

                if command == "exit":
                    print("Exiting voice listener.")
                    break

            except sr.WaitTimeoutError:
                print("Listening timed out, no speech detected.")
            except sr.UnknownValueError:
                print("Could not understand audio.")
            except sr.RequestError as e:
                print(f"Could not request results; {e}")

# Run voice command listener in a separate thread
if __name__ == "__main__":
    voice_thread = threading.Thread(target=listen_for_voice_commands)
    voice_thread.start()
    voice_thread.join()
    print("Program ended.")

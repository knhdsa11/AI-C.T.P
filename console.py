import speech_recognition as sr
import os
import json

# ฟังก์ชันแปลงเสียงพูดเป็นข้อความ
def listen_to_command():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        print("Listening...")
        try:
            audio = recognizer.listen(source, timeout=5)  # Timeout after 5 seconds of silence
        except sr.WaitTimeoutError:
            print("No command heard. Please try again.")
            return ""

    try:
        command = recognizer.recognize_google(audio, language="th-TH")
        print(f"You said: {command}")
        return command
    except sr.UnknownValueError:
        print("Sorry, I could not understand your command.")
        return ""
    except sr.RequestError:
        print("Sorry, the service is not available.")
        return ""

# ฟังก์ชันรันคำสั่งระบบจาก config
def execute_command(command, config):
    if command in config:
        if config[command] == "exit":
            print("Exiting...")
            exit(0)
        else:
            os.system(config[command])  # รันคำสั่งจาก config
    else:
        print("Command not recognized.")

# โหลด config จากไฟล์
def load_config(config_file="commands_config.json"):
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Config file '{config_file}' not found.")
        return {}

# Main Program
if __name__ == "__main__":
    # โหลด config
    config = load_config()

    while True:
        user_command = listen_to_command()
        if user_command:
            execute_command(user_command, config)

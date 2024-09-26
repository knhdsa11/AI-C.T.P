import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
import speech_recognition as sr
import os
import json
from threading import Thread, Event

class VoiceAssistantApp(App):
    def build(self):
        self.config = self.load_config()
        self.listening_event = Event()
        self.listening_event.clear()

        # Layout หลัก
        layout = BoxLayout(orientation='vertical')

        # Label สำหรับแสดงข้อความ
        self.label = Label(text="Press the button to start listening", font_size='20sp')
        layout.add_widget(self.label)

        # ปุ่มสำหรับเริ่มฟังคำสั่ง
        listen_button = Button(text="Start Listening", font_size='20sp', size_hint=(1, 0.2))
        listen_button.bind(on_press=self.start_listening)
        layout.add_widget(listen_button)

        # ปุ่มสำหรับหยุดฟัง
        stop_button = Button(text="Stop Listening", font_size='20sp', size_hint=(1, 0.2))
        stop_button.bind(on_press=self.stop_listening)
        layout.add_widget(stop_button)

        return layout

    # ฟังก์ชันโหลด config จากไฟล์
    def load_config(self, config_file="commands_config.json"):
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            self.label.text = f"Config file '{config_file}' not found."
            return {}

    # ฟังก์ชันแปลงเสียงพูดเป็นข้อความ
    def listen_to_command(self):
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source)
            self.label.text = "Listening..."
            self.listening_event.set()  # เริ่มฟังคำสั่ง

            while self.listening_event.is_set():
                try:
                    audio = recognizer.listen(source, timeout=5)
                    command = recognizer.recognize_google(audio, language="th-TH")
                    self.label.text = f"You said: {command}"
                    self.execute_command(command)
                except sr.WaitTimeoutError:
                    continue
                except sr.UnknownValueError:
                    self.label.text = "Sorry, I could not understand your command."
                except sr.RequestError:
                    self.label.text = "Sorry, the service is not available."

    # ฟังก์ชันรันคำสั่งระบบจาก config
    def execute_command(self, command):
        if command in self.config:
            if self.config[command] == "exit":
                self.label.text = "Exiting..."
                exit(0)
            else:
                os.system(self.config[command])  # รันคำสั่งจาก config
        else:
            self.label.text = "Command not recognized."

    # ฟังก์ชันเริ่มการฟังคำสั่ง (run on a separate thread)
    def start_listening(self, instance):
        self.listening_event.set()  # เริ่มการฟัง
        Thread(target=self.listen_to_command).start()

    # ฟังก์ชันหยุดการฟังคำสั่ง
    def stop_listening(self, instance):
        self.listening_event.clear()  # หยุดการฟัง
        self.label.text = "Stopped listening."

if __name__ == '__main__':
    VoiceAssistantApp().run()

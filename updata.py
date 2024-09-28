import os
import json , configparser
import requests
import speech_recognition as sr
import subprocess
from gtts import gTTS
from threading import Thread, Event
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.core.text import LabelBase

config = configparser.ConfigParser()
config.read("config.ini")

# โหลดฟอนต์ภาษาไทย
LabelBase.register(name="THSarabun", fn_regular="THSarabunNew.ttf")  # ตรวจสอบให้แน่ใจว่าไฟล์ฟอนต์อยู่ในโฟลเดอร์เดียวกับโค้ด

class VoiceAssistantApp(App):
    def build(self):
        # Event สำหรับควบคุม thread การฟังเสียง
        self.listening_event = Event()
        self.listening_event.clear()

        # Layout หลัก
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Label สำหรับแสดงข้อความ
        self.label = Label(text="กดปุ่มเพื่อเริ่มการฟัง", font_size='24sp', font_name="THSarabun", halign="center", valign="middle")
        layout.add_widget(self.label)

        # ปุ่มสำหรับเริ่มฟังคำสั่ง
        listen_button = Button(text="เริ่มการฟัง", font_size='24sp', font_name="THSarabun", size_hint=(1, 0.2))
        listen_button.bind(on_press=self.start_listening_thread)
        layout.add_widget(listen_button)

        # ปุ่มสำหรับหยุดฟัง
        stop_button = Button(text="หยุดการฟัง", font_size='24sp', font_name="THSarabun", size_hint=(1, 0.2))
        stop_button.bind(on_press=self.stop_listening)
        layout.add_widget(stop_button)

        # โหลด config จากไฟล์หรือ GitHub หลังจากสร้าง UI เสร็จ
        config_source = config.get("setting","config_raw")
        if config_source == "":
            config_source = "commands_config.json"
        self.config = self.load_custom_config(config_source)

        return layout

    # ฟังก์ชันโหลด config จากไฟล์หรือ GitHub
    def load_custom_config(self, config_file):
        if os.path.exists(config_file):  # ถ้าไฟล์ config อยู่ในเครื่อง
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except FileNotFoundError:
                self.label.text = f"ไม่พบไฟล์ '{config_file}'"
                return {}
        else:  # ถ้าไม่มี ให้โหลดจาก GitHub
            github_url = "https://raw.githubusercontent.com/username/repo/branch/commands_config.json"
            try:
                response = requests.get(github_url)
                if response.status_code == 200:
                    return response.json()
                else:
                    self.label.text = "ไม่สามารถโหลด config จาก GitHub ได้"
                    return {}
            except Exception as e:
                self.label.text = f"เกิดข้อผิดพลาด: {str(e)}"
                return {}

    # ฟังก์ชันแปลงเสียงพูดเป็นข้อความ
    def listen_to_command(self):
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source)
            self.label.text = "กำลังฟัง..."
            self.listening_event.set()  # เริ่มฟังคำสั่ง

            while self.listening_event.is_set():
                try:
                    audio = recognizer.listen(source, timeout=5)
                    command = recognizer.recognize_google(audio, language="th-TH")
                    self.label.text = f"คุณพูดว่า: {command}"
                    self.execute_command(command)
                except sr.WaitTimeoutError:
                    continue
                except sr.UnknownValueError:
                    self.label.text = "ขออภัย, ไม่เข้าใจคำสั่งของคุณ"
                except sr.RequestError:
                    self.label.text = "บริการไม่สามารถใช้งานได้"

    # ฟังก์ชันรันคำสั่งจาก config
    def execute_command(self, command):
        if command in self.config:
            if self.config[command] == "exit":
                self.label.text = "กำลังออก..."
                self.play_response("กำลังออก")
                exit(0)
            else:
                os.system(self.config[command])  # รันคำสั่งจาก config
                self.play_response(f"กำลังทำงานคำสั่ง: {command}")  # เล่นเสียงตอบกลับ
        else:
            self.label.text = "ไม่รู้จักคำสั่ง"
            self.play_response("ไม่รู้จักคำสั่ง")
            self.stop_listening(None)  # หยุดการฟังเมื่อไม่รู้จักคำสั่ง

    # ฟังก์ชันเล่นเสียงตอบกลับผ่าน ffplay
    def play_response(self, message):
        # สร้างชื่อไฟล์เสียงในโฟลเดอร์ที่กำหนด
        audio_file_path = os.path.join(os.getcwd(), "response.mp3")  # เก็บในโฟลเดอร์ปัจจุบัน

        tts = gTTS(text=message, lang='th')
        tts.save(audio_file_path)  # บันทึกไฟล์เสียง

        # ใช้ ffplay เล่นไฟล์เสียงในแบ็คกราวด์
        subprocess.Popen(['ffplay', '-nodisp', '-autoexit', audio_file_path],
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)

    # ฟังก์ชันเริ่มการฟังคำสั่งใน thread ใหม่
    def start_listening_thread(self, instance):
        if not self.listening_event.is_set():  # ถ้ายังไม่มีการฟัง ให้เริ่ม
            self.listening_event.set()
            Thread(target=self.listen_to_command, daemon=True).start()

    # ฟังก์ชันหยุดการฟังคำสั่ง
    def stop_listening(self, instance):
        self.listening_event.clear()  # หยุดการฟัง
        self.label.text = "หยุดการฟังแล้ว"

if __name__ == '__main__':
    VoiceAssistantApp().run()

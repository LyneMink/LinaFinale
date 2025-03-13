import os
import subprocess
import requests

def text_to_speech_offline(text, lang='en'):
    try:
        subprocess.run(["espeak", "-v", lang, text])
    except FileNotFoundError:
        try:
            subprocess.run(["pico2wave", "-w", "temp.wav", f"{text}"])
            subprocess.run(["aplay", "temp.wav"])
            os.remove("temp.wav")
        except FileNotFoundError:
            print("Aucun moteur de synthèse vocale hors ligne trouvé (espeak ou pico2wave).")

def text_to_speech_online(text, lang):
    try:
        from gtts import gTTS
        import pygame

        tts = gTTS(text, lang=lang)
        tts.save("temp.mp3")

        pygame.mixer.init()
        pygame.mixer.music.load("temp.mp3")
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            continue

        os.remove("temp.mp3")
    except ImportError:
        print("gTTS ou pygame n'est pas installé. Installation en cours...")
        os.system("pip install gtts pygame")
        text_to_speech_online(text, lang) 
    except requests.exceptions.RequestException:
        print("Pas de connexion Internet. Utilisation de la synthèse vocale hors ligne.")
        text_to_speech_offline(text, lang)


def run_synthese_vocale(synthesis_object_queue, synthesis_description_queue):
    while True:
        try:
            data = synthesis_object_queue.get(timeout=10)
            object_name, distance = data
            text = f"Objet détecté: {object_name} à {distance} cm"
            text_to_speech_online(text, 'fr')
        except Exception as e:
            print(f"Pas de données d'objets disponibles: {e}")

        try:
            data = synthesis_description_queue.get(timeout=60)
            if data[0] == "description":
                text = f"Description de l'environnement: {data[1]}"
                text_to_speech_online(text, 'fr')
        except Exception as e:
            print(f"Pas de données de description disponibles: {e}")


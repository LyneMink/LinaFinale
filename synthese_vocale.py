import os
import subprocess
import requests

def text_to_speech_offline(text, lang='en'):
    try:
        # Essayer d'utiliser espeak si disponible
        subprocess.run(["espeak", "-v", lang, text])
    except FileNotFoundError:
        try:
            # Si espeak n'est pas disponible, essayer pico2wave
            subprocess.run(["pico2wave", "-w", "temp.wav", f"{text}"])
            subprocess.run(["aplay", "temp.wav"])  # Jouer le fichier audio
            os.remove("temp.wav")  # Supprimer le fichier après lecture
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


def run_synthese_vocale():
    try:
        text_to_speech_online(text, lang)
    except Exception as e:
        print(f"Erreur avec la synthèse vocale en ligne : {e}")
        # En cas d'échec, utiliser la synthèse vocale hors ligne
        text_to_speech_offline(text, lang)


import speech_recognition as sr
from gtts import gTTS
import pygame
import os
from lecture_texte import lecture_texte

def ecouter():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Ecoute....")
        audio = recognizer.listen(source)

    try:
        commande = recognizer.recognize_vosk(audio, language="fr-FR")
        print(f"Commande reconnue: {commande}")
        return commande
    except sr.UnknownValueError:
        print("Impossible de comprendre la commande")
        return None
    except sr.RequestError as e:
        print(f"Erreur lors de la requête: {e}")
        return None
    
def parler(texte):
    try:
        tts = gTTS(texte, lang='fr')
        tts.save("tempo.mp3")

        pygame.mixer.init()
        pygame.mixer.music.load("tempo.mp3")
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            continue

        os.remove("tempo.mp3")
    except Exception as e:
        print(f"Erreur lors de la synthèse vocale: {e}")


def assistant():
    parler("Voulez-vous une lecture du texte? Oui ou Non")
    commande = ecouter()
    if "oui" in commande:
        lecture_texte()
    else:
        parler("D'accord, je suis à votre disposition pour toute autre lecture a effectuer.")
    



import speech_recognition as sr
from gtts import gTTS
import pygame
import os
import threading
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
    stop_event = threading.Event()
    ocr_thread = None

    while True:
        parler("Dites 'yes lina' pour démarrer la lecture ou 'stop lina' pour arrêter.")
        commande = ecouter()

        if commande and "yes lina" in commande:
            if ocr_thread and ocr_thread.is_alive():
                parler("La lecture est déjà en cours.")
            else:
                stop_event.clear()  # Réinitialiser l'événement
                ocr_thread = threading.Thread(target=lecture_texte, args=(stop_event,))
                ocr_thread.start()
                parler("Lecture du texte démarrée.")

        elif commande and "stop lina" in commande:
            if ocr_thread and ocr_thread.is_alive():
                stop_event.set()  # Signaler l'arrêt
                ocr_thread.join()  # Attendre la fin du thread
                parler("Lecture du texte arrêtée.")
            else:
                parler("Aucune lecture en cours.")

        else:
            parler("Commande non reconnue. Veuillez répéter.")
    



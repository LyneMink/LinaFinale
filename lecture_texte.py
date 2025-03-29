import cv2
from paddleocr import PaddleOCR
import numpy as np
from gtts import gTTS
import pygame
import os
import time

ocr = PaddleOCR(use_angle_cls=True, lang='fr')

def text_to_speech(text):
    """Convertit un texte en parole et le joue."""
    try:
        tts = gTTS(text=text, lang='fr')
        tts.save("temp_ocr.mp3")
        
        pygame.mixer.init()
        pygame.mixer.music.load("temp_ocr.mp3")
        pygame.mixer.music.play()
        
        # Attendre la fin de la lecture
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
            
        os.remove("temp_ocr.mp3")
    except Exception as e:
        print(f"Erreur TTS: {e}")

def lecture_texte(stop_event=None):

    cap = cv2.VideoCapture("http://192.168.1.111:81/stream")

    while True:

        if stop_event and stop_event.is_set():
            break

        ret, frame = cap.read()
        if not ret:
            break

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Perform OCR on the frame
        result = ocr.ocr(rgb_frame, cls=True)

        # Draw the results on the frame
        for line in result:
            for word_info in line:
                text = word_info[1][0]
                confidence = word_info[1][1]
                box = word_info[0]

                # Filtrer les textes peu fiables et éviter les répétitions
                if confidence > 0.7 and text != last_text:
                    print(f"Texte détecté: {text} (Confiance: {confidence:.2f})")
                    text_to_speech(text)  
                    last_text = text
                    pts = np.array([[int(p[0]), int(p[1])] for p in box], np.int32)
                    cv2.polylines(frame, [pts], isClosed=True, color=(0, 255, 0), thickness=2)
                    cv2.putText(frame, text, (int(box[0][0]), int(box[0][1] - 10)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
        
        cv2.imshow("OCR Result", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
from mindnlp.transformers.models import BlipForConditionalGeneration, BlipProcessor
import cv2

# Charger le modèle BLIP et le processeur
processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

# URL du flux vidéo de l'ESP32-CAM (remplacez par votre URL)
video_stream_url = "http://192.168.1.111:81/stream"

# Ouvrir le flux vidéo
cap = cv2.VideoCapture(video_stream_url)

def run_description_environnement():

    if not cap.isOpened():
        print("Erreur: Impossible d'ouvrir le flux vidéo.")
        exit()

    while True:
        # Capturer une image du flux vidéo
        ret, frame = cap.read()
        if not ret:
            print("Erreur: Impossible de lire l'image.")
            break

        # Convertir l'image en format RGB (BLIP attend du RGB)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Prétraiter l'image pour BLIP
        inputs = processor(rgb_frame, return_tensors="ms")

        # Générer une description avec BLIP
        out = model.generate(**inputs)
        description = processor.decode(out[0], skip_special_tokens=True)

        # Afficher la description sur l'image
        cv2.putText(frame, description, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # Afficher l'image avec la description
        cv2.imshow("ESP32-CAM avec BLIP", frame)

        # Quitter si la touche 'q' est pressée
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Libérer les ressources
    cap.release()
    cv2.destroyAllWindows()
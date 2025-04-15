from mindnlp.transformers.models import BlipForConditionalGeneration, BlipProcessor
import cv2
import queue  # Pour Empty exception

processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

video_stream_url = "http://192.168.1.111:81/stream"

def run_description_environnement(description_queue, mode_control_queue, max_queue_size=5):
    cap = cv2.VideoCapture(video_stream_url)
    if not cap.isOpened():
        print("Erreur: Impossible d'ouvrir le flux vidéo.")
        exit()

    while True:
        # Vérifier si on doit vider la queue
        try:
            control_signal = mode_control_queue.get_nowait()
            if control_signal == "SWITCH_TO_DESCRIPTION":
                # Vider les anciennes descriptions
                while not description_queue.empty():
                    description_queue.get()
                # Remettre le signal dans la queue pour les autres processus
                mode_control_queue.put(control_signal)
        except queue.Empty:
            pass

        ret, frame = cap.read()
        if not ret:
            print("Erreur: Impossible de lire l'image.")
            break

        # Ne générer une description que si la queue n'est pas pleine
        if description_queue.qsize() < max_queue_size:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            inputs = processor(rgb_frame, return_tensors="ms")
            out = model.generate(**inputs)
            description = processor.decode(out[0], skip_special_tokens=True)
            description_queue.put(description)

    cap.release()
    cv2.destroyAllWindows()
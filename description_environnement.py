from mindnlp.transformers.models import BlipForConditionalGeneration, BlipProcessor
import cv2

processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

video_stream_url = "http://192.168.1.111:81/stream"

def run_description_environnement(description_queue):
    cap = cv2.VideoCapture(video_stream_url)
    if not cap.isOpened():
        print("Erreur: Impossible d'ouvrir le flux vidéo.")
        exit()

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Erreur: Impossible de lire l'image.")
            break

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        inputs = processor(rgb_frame, return_tensors="ms")
        out = model.generate(**inputs)
        description = processor.decode(out[0], skip_special_tokens=True)
        description_queue.put(description)

        cv2.putText(frame, description, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.imshow("ESP32-CAM avec BLIP", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
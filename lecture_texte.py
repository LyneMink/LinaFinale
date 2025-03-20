import cv2
import mindspore as ms
import numpy as np
from mindocr.mindocr.models import build_model
from mindocr.mindocr.postprocess.det_db_postprocess import DBPostprocess
from mindocr.mindocr.postprocess.rec_postprocess import CTCLabelDecode

ESP32_CAM_URL = "http://192.168.1.100:8080/video"

def process_frame(frame, dbnet, crnn, det_postprocess, rec_postprocess):
    # Prétraitement pour la détection
    input_image = cv2.resize(frame, (640, 640))
    input_image = input_image.astype(np.float32) / 255.0
    input_image = np.transpose(input_image, (2, 0, 1))
    input_image = np.expand_dims(input_image, axis=0)
    input_tensor = ms.Tensor(input_image, dtype=ms.float32)
    
    # Détection des zones de texte
    det_results = dbnet(input_tensor)
    boxes = det_postprocess(det_results)
    
    result_frame = frame.copy()
    print(f"Nombre de boîtes détectées : {len(boxes)}")
    
    # Reconnaissance des textes détectés
    for box in boxes:
        x_min, y_min, x_max, y_max = [int(coord) for coord in box]
        
        # Vérification que les coordonnées sont dans les limites de l'image
        x_min = max(0, x_min)
        y_min = max(0, y_min)
        x_max = min(frame.shape[1], x_max)
        y_max = min(frame.shape[0], y_max)
        
        if x_max <= x_min or y_max <= y_min:
            continue  # Ignorer les boîtes invalides
            
        # Extraction et prétraitement de la région de texte
        try:
            cropped_image = frame[y_min:y_max, x_min:x_max]
            if cropped_image.size == 0:
                continue
                
            cropped_image = cv2.resize(cropped_image, (100, 32))
            cropped_image = cropped_image.astype(np.float32) / 255.0
            cropped_image = np.transpose(cropped_image, (2, 0, 1))
            cropped_image = np.expand_dims(cropped_image, axis=0)
            cropped_tensor = ms.Tensor(cropped_image, dtype=ms.float32)
            
            # Reconnaissance du texte
            rec_results = crnn(cropped_tensor)
            pred_text = rec_postprocess(rec_results)
            
            print(f"Texte prédit : {pred_text}")
            print(f"Boite englobante : {box}")
            
            # Dessin des résultats
            cv2.rectangle(result_frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
            cv2.putText(result_frame, pred_text, (x_min, y_min - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
        except Exception as e:
            print(f"Erreur lors du traitement d'une boîte: {e}")
            
    return result_frame

def lecture_texte():
    try:
        # Initialisation des modèles
        dbnet = build_model('dbnet_resnet50', pretrained=True)
        crnn = build_model('crnn_vgg7', pretrained=True)
        det_postprocess = DBPostprocess()
        rec_postprocess = CTCLabelDecode()

        cap = cv2.VideoCapture(ESP32_CAM_URL)
        if not cap.isOpened():
            raise Exception("Impossible d'ouvrir le flux vidéo")
        
        print("Connexion etablie avec la camera")

        while True:
            ret, frame = cap.read()
            if not ret:
                print("Impossible de lire le flux vidéo")
                break

            result_frame = process_frame(frame, dbnet, crnn, det_postprocess, rec_postprocess)
            cv2.imshow("Text Detection", result_frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    except Exception as e:
        print(f"Erreur: {e}")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("Connexion avec la camera fermee")

lecture_texte()
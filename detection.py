import yaml
import numpy as np
import cv2
import mindspore as ms
import os
from mindspore import Tensor, nn
from mindyolo.models import create_model
from mindyolo.utils import non_max_suppression
from lecture_texte import lecture_texte


def merge_yaml_configs(base_files, main_config, base_dir):
    merged_config = main_config.copy()  # Commencer par une copie de la configuration principale
    for file in base_files:
        # Résoudre le chemin relatif par rapport au répertoire de base
        file_path = os.path.join(base_dir, file)
        with open(file_path, "r") as f:
            base_config = yaml.safe_load(f)
            # Fusionner récursivement les dictionnaires
            merged_config = recursive_merge(merged_config, base_config)
    return merged_config

# Fonction pour fusionner récursivement deux dictionnaires
def recursive_merge(dict1, dict2):
    for key, value in dict2.items():
        if key in dict1 and isinstance(dict1[key], dict) and isinstance(value, dict):
            # Fusionner récursivement les sous-dictionnaires
            recursive_merge(dict1[key], value)
        else:
            # Écraser ou ajouter la valeur
            dict1[key] = value
    return dict1

# Classe Config
class Config:
    def __init__(self, config_dict):
        for key, value in config_dict.items():
            if isinstance(value, dict):
                setattr(self, key, Config(value))  # Récursif pour les dictionnaires imbriqués
            else:
                setattr(self, key, value)

    def get(self, key, default=None):
        return getattr(self, key, default)

# Charger le fichier de configuration
conf_path = "mindyolo/configs/yolox/yolox-m.yaml"
base_dir = os.path.dirname(conf_path) 
with open(conf_path, "r") as f:
    cfg_dict = yaml.safe_load(f)

# Fusion des fichiers YAML references par __BASE__
base_files = cfg_dict.pop("__BASE__", [])
merged_config = merge_yaml_configs(base_files, cfg_dict, base_dir)


if 'data' in merged_config and 'nc' in merged_config['data']:
    merged_config['nc'] = merged_config['data']['nc']  # Ajout au niveau racine
    merged_config['network']['nc'] = merged_config['data']['nc']  # Ajout dans 'network'
else:
    raise ValueError("'nc' non trouvé dans la section 'data'.")

# Vérifier la configuration fusionnée
print("Configuration fusionnée :")
print(yaml.dump(merged_config))

# Convertir le dictionnaire en un objet Config
cfg = Config(merged_config)

nc = cfg.data.nc
print("Valeur de nc extraite de cfg.data.nc:", nc)  # Doit afficher 80

print("Valeur de nc dans network:", cfg.network.nc)  # Doit afficher 80

cfg.network.depth_multiple = 0.67
cfg.network.width_multiple = 0.75

# Extraire 'stride' et 'anchors' du réseau
cfg.stride = cfg.network.stride
cfg.depth_multiple = cfg.network.depth_multiple
cfg.width_multiple = cfg.network.width_multiple
cfg.backbone = cfg.network.backbone
cfg.head = cfg.network.head

# Instancier le modèle
model = create_model(
    num_classes=nc,
    model_name="yolox",
    model_cfg=cfg,
    checkpoint_path="checkpoints/yolox-m_300e_map467-1db321ee.ckpt",
)

def preprocess_image(img, input_size=(640, 640), color=(114, 114, 114)):
    h, w, _ = img.shape
    new_h, new_w = input_size
    scale = min(new_w / w, new_h / h)
    resized_w, resized_h = int(w * scale), int(h * scale)
    img_resized = cv2.resize(img, (resized_w, resized_h), interpolation=cv2.INTER_LINEAR)
    
    # Calcul du padding
    dw = new_w - resized_w
    dh = new_h - resized_h
    top = dh // 2
    bottom = dh - top
    left = dw // 2
    right = dw - left
    
    img_padded = cv2.copyMakeBorder(img_resized, top, bottom, left, right,
                                    cv2.BORDER_CONSTANT, value=color)
    img = img_padded.astype(np.float32) /255.0
    img = np.transpose(img, (2, 0, 1))
    img = np.expand_dims(img, axis=0)
    img_tensor = Tensor(img, ms.float32)
    return img_tensor, scale, (left, top)


def run_inference(model, frame):
    img_tensor, ratio, dwdh = preprocess_image(frame)
    preds = model(img_tensor)
    if isinstance(preds, (tuple, list)):
        preds = preds[0]
    return preds, ratio, dwdh

def draw_boxes(frame, detections, ratio, dwdh, class_names):
    for det in detections:
        x1, y1, x2, y2, conf, cls = det
        x1 = int((x1 - dwdh[0]) / ratio)
        y1 = int((y1 - dwdh[1]) / ratio)
        x2 = int((x2 - dwdh[0]) / ratio)
        y2 = int((y2 - dwdh[1]) / ratio)
        label = f"{class_names[int(cls)]}: {conf:.2f}"
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(frame, label, (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    return frame

def run_detection(distance):
    cap = cv2.VideoCapture("http://192.168.1.111:81/stream")
    if not cap.isOpened():
        print("Error: Could not open video.")
        return
    
    detected_objects = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        detections, ratio, dwdh = run_inference(model, frame)
        nms_results = non_max_suppression(detections, 0.7, 0.25)
        if len(nms_results) > 0 and nms_results[0] is not None:
            for det in nms_results[0]:
                x1, y1, x2, y2, conf, cls = det
                class_name = model.names[int(cls)]  # Récupérer le nom de la classe
                detected_objects.append(class_name)  # Ajouter à la liste
                print(f"Objet détecté : {class_name}, Confiance : {conf:.2f}")

            frame = draw_boxes(frame, nms_results[0], ratio, dwdh, model.names)
        cv2.imshow("Object Detection", frame)
        if cv2.waitKey(1) == 27:
            break
        
    cap.release()
    cv2.destroyAllWindows()

import serial
import logging


logger = logging.getLogger(__name__)

# Configuration du port série
port = '/dev/ttyACM0'  # Remplacez par le bon port (Windows : 'COMX', Linux/Mac : '/dev/ttyUSB0' ou '/dev/ttyACM0')
baudrate = 9600  # Doit correspondre au baudrate du microcontrôleur

def run_capteur(distance_queue, control_queue):
    # Ouvrir la connexion série
    try:
        ser = serial.Serial(port, baudrate, timeout=1)
        print(f"Connexion série établie sur {port}")
    except serial.SerialException as e:
        print(f"Erreur : Impossible d'ouvrir le port série. {e}")
        exit()

    # Lire les données du port série
    try:
        while True:
            signal = control_queue.get()
            if signal != "NEXT_DISTANCE":
                continue
            if ser.in_waiting > 0:  # Vérifier si des données sont disponibles
                line = ser.readline().decode('utf-8').strip()  # Lire une ligne et la décoder
                try:
                   cleaned_line = line.lower().replace('distance', '').replace(':', '').replace('cm', '')
                   cleaned_line = ''.join(c for c in cleaned_line if c.isdigit() or c in {'.', ',','-'}).strip()
                   cleaned_line = cleaned_line.replace(',', '.')

                   if cleaned_line:
                       raise ValueError("Donnee vide apres nettoyage")
                   
                   distance = float(cleaned_line)

                   if not 0 <= distance <= 500:
                       raise ValueError("Distance hors limites")
                   
                   logger.info("[CAPTEUR] Distance lue : %s cm", distance)
                   distance_queue.put(distance)
                except ValueError:
                    print(f"Données reçues invalides : {line}")
    except KeyboardInterrupt:
        print("Arrêt du programme.")

    # Fermer la connexion série
    ser.close()
print("Connexion série fermée.")
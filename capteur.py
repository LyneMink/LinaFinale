import serial

# Configuration du port série
port = '/dev/ttyACM0'  # Remplacez par le bon port (Windows : 'COMX', Linux/Mac : '/dev/ttyUSB0' ou '/dev/ttyACM0')
baudrate = 9600  # Doit correspondre au baudrate du microcontrôleur

def run_capteur(distance_queue):
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
            if ser.in_waiting > 0:  # Vérifier si des données sont disponibles
                line = ser.readline().decode('utf-8').strip()  # Lire une ligne et la décoder
                try:
                    distance = float(line)  # Convertir en float
                    print(f"Distance mesurée : {distance} cm")
                    distance_queue.put(distance)
                except ValueError:
                    print(f"Données reçues invalides : {line}")
    except KeyboardInterrupt:
        print("Arrêt du programme.")

    # Fermer la connexion série
    ser.close()
print("Connexion série fermée.")
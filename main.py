from dask.distributed import Client, Queue
from synthese_vocale import run_synthese_vocale
from detection import run_detection
from capteur import run_capteur
from description_environnement import run_description_environnement

# Initialiser le client Dask
client = Client()

# Créer des files pour la communication entre les tâches
distance_queue = Queue()  # Pour envoyer la distance de run_capteur à run_detection
detection_queue = Queue()  # Pour envoyer le nom de l'objet détecté à run_synthese_vocale
description_queue = Queue()  # Pour envoyer la description de l'environnement à run_synthese_vocale

# Fonction pour la première synchronisation
def synchronisation_1():
    while True:
        # Attendre une distance non nulle de run_capteur
        distance = distance_queue.get()
        if distance > 0:
            # Lancer la détection
            object_name = run_detection(distance)
            # Envoyer le nom de l'objet et la distance à run_synthese_vocale
            detection_queue.put((object_name, distance))

# Fonction pour la deuxième synchronisation
def synchronisation_2():
    while True:
        # Attendre une description de run_description_environnement
        description = description_queue.get()
        # Envoyer la description à run_synthese_vocale
        detection_queue.put(("description", description))

# Soumettre les tâches à Dask
futures = [
    client.submit(run_capteur, distance_queue),  # run_capteur envoie des distances à distance_queue
    client.submit(synchronisation_1),  # Première synchronisation
    client.submit(synchronisation_2),  # Deuxième synchronisation
    client.submit(run_description_environnement, description_queue),  # run_description_environnement envoie des descriptions à description_queue
    client.submit(run_synthese_vocale, detection_queue)  # run_synthese_vocale reçoit des données de detection_queue
]

# Attendre la fin des tâches
for future in futures:
    future.result()
import multiprocessing as mp
from capteur import run_capteur
import time
import logging
from detection import run_detection
from synthese_vocale import run_synthese_vocale
from description_environnement import run_description_environnement


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("system.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def synchronisation_1(distance_queue, synthesis_object_queue):
    """
    Synchronise les données du capteur avec le module de détection,
    puis transmet les résultats au module de synthèse vocale.
    
    Args:
        distance_queue: Queue pour recevoir les données du capteur
        synthesis_object_queue: Queue pour envoyer les objets détectés à la synthèse vocale
    """
    logger.info("[synchronisation_1] Démarrage de la tâche de synchronisation 1")
    
    while True:
        try:
            # Attendre une distance non nulle du capteur avec timeout
            distance = distance_queue.get(timeout=60)
            if distance > 0:
                logger.info(f"[synchronisation_1] Distance reçue : {distance:.1f} cm")
                
                # Lancer la détection
                object_name = run_detection(distance)
                logger.info(f"[synchronisation_1] Objet détecté : {object_name}")
                
                # Envoyer le nom de l'objet et la distance à la synthèse vocale
                synthesis_object_queue.put((object_name, distance))
                logger.info(f"[synchronisation_1] Envoi à la synthèse vocale : {object_name} à {distance:.1f} cm")
        except mp.queues.Empty:
            logger.warning("[synchronisation_1] Timeout - Aucune distance reçue pendant 60 secondes")
        except Exception as e:
            logger.error(f"[synchronisation_1] Exception: {e}")
            time.sleep(5)  # Attendre avant de réessayer

# Fonction pour la deuxième synchronisation
def synchronisation_2(description_queue, synthesis_description_queue):
    """
    Synchronise les descriptions d'environnement avec le module de synthèse vocale.
    
    Args:
        description_queue: Queue pour recevoir les descriptions
        synthesis_description_queue: Queue pour envoyer les descriptions à la synthèse vocale
    """
    logger.info("[synchronisation_2] Démarrage de la tâche de synchronisation 2")
    
    while True:
        try:
            # Attendre une description avec timeout
            logger.info("[synchronisation_2] En attente de description...")
            description = description_queue.get(timeout=60)
            logger.info(f"[synchronisation_2] Description reçue : {description}")
            
            # Envoyer la description à la synthèse vocale
            synthesis_description_queue.put(("description", description))
            logger.info(f"[synchronisation_2] Envoi à la synthèse vocale : {description}")
        except mp.queues.Empty:
            logger.warning("[synchronisation_2] Timeout - Aucune description reçue pendant 60 secondes")
        except Exception as e:
            logger.error(f"[synchronisation_2] Exception: {e}")
            time.sleep(5) 


if __name__ == "__main__":

    # Créer des files pour la communication entre les tâches
    distance_queue = mp.Queue()  # Pour envoyer la distance de run_capteur à run_detection\
    description_queue = mp.Queue()  # Pour envoyer la description de l'environnement à run_synthese_vocale
    synthesis_object_queue = mp.Queue()
    synthesis_description_queue = mp.Queue() # Pour envoyer la description de run_description_environnement à run_synthese_vocale

    processes = [
        mp.Process(target=run_capteur, args=(distance_queue,)),
        mp.Process(target=run_synthese_vocale, args=(synthesis_object_queue, synthesis_description_queue)),
        mp.Process(target=run_description_environnement, args=(description_queue,)),
        mp.Process(target=synchronisation_1, args=(distance_queue, synthesis_object_queue)),
        mp.Process(target=synchronisation_2, args=(description_queue, synthesis_description_queue))
    ]

    for p in processes:
        p.start()

    for p in processes:
        p.join()
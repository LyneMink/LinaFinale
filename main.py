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

def synchronisation_1(distance_queue, synthesis_object_queue, sensor_control_queue, mode_control_queue):
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
            if not sensor_control_queue.full():
                sensor_control_queue.put("NEXT DISTANCE")
            else:
                logger.warning("[synchronisation_1] La queue de contrôle du capteur est pleine, attente de 5 secondes")
                time.sleep(0.1)
                continue
            # Attendre une distance non nulle du capteur avec timeout
            try:
                distance = distance_queue.get(timeout=60)
                if distance > 0:
                    logger.info(f"[synchronisation_1] Distance reçue : {distance:.1f} cm")
                    
                    # Lancer la détection
                    object_name = run_detection(distance)
                    if object_name is None:
                        logger.warning("[synchronisation_1] Aucun objet détecté")
                        if not mode_control_queue.full():
                            logger.debug("[synchronisation_1] Envoi de la commande SWITCH_TO_DESCRIPTION")
                            mode_control_queue.put("SWITCH_TO_DESCRIPTION")
                        time.sleep(1)
                        continue

                    # Cas où l'objet est détecté
                    logger.info(f"[synchronisation_1] Objet détecté : {object_name}")
                    
                    # Envoyer le nom de l'objet et la distance à la synthèse vocale
                    synthesis_object_queue.put((object_name, distance))
                    logger.info(f"[synchronisation_1] Envoi à la synthèse vocale : {object_name} à {distance:.1f} cm")

                    if not mode_control_queue.full():
                        logger.debug("[synchronisation_1] Envoi de la commande SWITCH_TO_DESCRIPTION")
                        mode_control_queue.put("SWITCH_TO_DESCRIPTION")
                    else:
                        logger.warning("[synchronisation_1] La queue de contrôle du mode est pleine, attente de 5 secondes")
                        time.sleep(0.1)

            except mp.queues.Empty:
                logger.warning("[synchronisation_1] Timeout - Aucune distance reçue pendant 60 secondes")
                if not mode_control_queue.full():
                    logger.debug("[synchronisation_1] Envoi de la commande SWITCH_TO_DESCRIPTION")
                    mode_control_queue.put("SWITCH_TO_DESCRIPTION")
        except Exception as e:
            logger.error(f"[synchronisation_1] Exception: {e}")
            time.sleep(5)  # Attendre avant de réessayer

# Fonction pour la deuxième synchronisation
def synchronisation_2(description_queue, synthesis_description_queue, mode_control_queue):
    """
    Synchronise les descriptions d'environnement avec le module de synthèse vocale.
    
    Args:
        description_queue: Queue pour recevoir les descriptions
        synthesis_description_queue: Queue pour envoyer les descriptions à la synthèse vocale
    """
    logger.info("[synchronisation_2] Démarrage de la tâche de synchronisation 2")
    
    while True:
        try:

            try:
                control_signal = mode_control_queue.get(timeout=120)

                if control_signal == "SWITCH_TO_DESCRIPTION":
                    logger.info(f"[synchronisation_2] Signal de contrôle reçu : {control_signal}")
                    logger.info("[synchronisation_2] En attente de description...")
                    try:
                        description = description_queue.get(timeout=120)
                        logger.info(f"[synchronisation_2] Description reçue : {description}")
                        
                        # Envoyer la description à la synthèse vocale
                        synthesis_description_queue.put(("description", description))
                        logger.info(f"[synchronisation_2] Envoi à la synthèse vocale : {description}")
                    
                        if not mode_control_queue.full():
                            logger.debug("[synchronisation_2] Envoi de la commande SWITCH_TO_DETECTION")
                            mode_control_queue.put("SWITCH_TO_DETECTION")
                        continue
                    except mp.queues.Empty:
                        logger.warning("[synchronisation_2] Timeout - Aucune description reçue pendant 120 secondes")
                        if not mode_control_queue.full():
                            logger.debug("[synchronisation_2] Envoi de la commande SWITCH_TO_DETECTION")
                            mode_control_queue.put("SWITCH_TO_DETECTION")
                        continue
                elif control_signal == "SWITCH_TO_DETECTION":
                    logger.debug(f"[synchronisation_2] Signal de contrôle reçu : {control_signal} et ignoré car en mode détection")
                else:
                    logger.warning(f"[synchronisation_2] Signal de contrôle inattendu : {control_signal}")
                
            except mp.queues.Empty:
                logger.warning("[synchronisation_2] Timeout - Aucun signal de controle")
                if not mode_control_queue.full():
                    logger.debug("[synchronisation_2] Envoi de la commande SWITCH_TO_DETECTION")
                    mode_control_queue.put("SWITCH_TO_DETECTION")
                continue
        
        except Exception as e:
            logger.error(f"[synchronisation_2] Exception: {e}")
            time.sleep(5) 


if __name__ == "__main__":

    # Créer des files pour la communication entre les tâches
    distance_queue = mp.Queue()  # Pour envoyer la distance de run_capteur à run_detection\
    description_queue = mp.Queue()  # Pour envoyer la description de l'environnement à run_synthese_vocale
    synthesis_object_queue = mp.Queue()
    synthesis_description_queue = mp.Queue() # Pour envoyer la description de run_description_environnement à run_synthese_vocale
    sensor_control_queue = mp.Queue()  # Pour contrôler le capteur
    mode_control_queue = mp.Queue()  # Pour contrôler le mode de fonctionnement


    init_barrier = mp.Barrier(5)  # Barrière pour synchroniser les processus
    def wrapped_capteur(*args):
        try:
            logger.debug("[capteur] Démarrage du capteur")
            init_barrier.wait()  # Attendre que tous les processus soient prêts
            run_capteur(*args)
        except Exception as e:
            print(f"[capteur] Erreur dans le capteur: {e}")
            raise

    def wrapped_synthese_vocale(*args):
        try:
            logger.debug("[synthese_vocale] Démarrage de la synthèse vocale")
            init_barrier.wait()  # Attendre que tous les processus soient prêts
            run_synthese_vocale(*args)
        except Exception as e:
            print(f"[synthese_vocale] Erreur dans la synthèse vocale: {e}")
            raise

    def wrapped_description_environnement(*args):
        try:
            logger.debug("[description_environnement] Démarrage de la description de l'environnement")
            init_barrier.wait()  # Attendre que tous les processus soient prêts
            run_description_environnement(*args)
        except Exception as e:
            print(f"[description_environnement] Erreur dans la description de l'environnement: {e}")
            raise

    def wrapped_sync1(*args):
        try:
            logger.debug("[synchronisation_1] Démarrage de la synchronisation 1")
            init_barrier.wait()  # Attendre que tous les processus soient prêts
            synchronisation_1(*args)
        except Exception as e:
            print(f"[synchronisation_1] Erreur dans la synchronisation 1: {e}")
            raise

    def wrapped_sync2(*args):
        try:
            logger.debug("[synchronisation_2] Démarrage de la synchronisation 2")
            init_barrier.wait()  # Attendre que tous les processus soient prêts
            synchronisation_2(*args)
        except Exception as e:
            print(f"[synchronisation_2] Erreur dans la synchronisation 2: {e}")
            raise

    # Vidange initial des queues et initialisation
    while not mode_control_queue.empty():
        mode_control_queue.get()
    mode_control_queue.put("SWITCH_TO_DETECTION")
    logger.info("[main] Initialisation des queues et démarrage des processus")

    processes = [
        mp.Process(target=wrapped_capteur, args=(distance_queue, sensor_control_queue)),
        mp.Process(target=wrapped_synthese_vocale, args=(synthesis_object_queue,
                                                          synthesis_description_queue)),
        mp.Process(target=wrapped_description_environnement, args=(description_queue,)),
        mp.Process(target=wrapped_sync1, args=(distance_queue, synthesis_object_queue,
                                                sensor_control_queue,
                                                mode_control_queue)),
        mp.Process(target=wrapped_sync2, args=(description_queue, synthesis_description_queue, 
                                               mode_control_queue))
    ]

    for p in processes:
        logger.info(f"[main] Démarrage du processus bloques par barriere")
        p.daemon = True
        p.start()

    time.sleep(0.5)


    try:
        while any (p.is_alive() for p in processes):
            status = [(i, p.is_alive()) for i, p in enumerate(processes)]
            logger.info(f"[main] État des processus: {status}")
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("[main] Arrêt du programme par l'utilisateur")
        for p in processes:
            p.terminate()
    finally:
        for p in processes:
            p.join(timeout=1)
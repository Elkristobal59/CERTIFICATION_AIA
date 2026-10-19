import os
import sys
import time
import numpy as np
import soundfile as sf

# Forcer encodage console UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

STUDIO_DIR = r"D:\CODE JEDHA\LOCAL_TTS_STUDIO"
if STUDIO_DIR not in sys.path:
    sys.path.insert(0, STUDIO_DIR)

from src.engine.chunker import SmartTextChunker, concatenate_audio_segments
from src.engine.kokoro_engine import KokoroEngine

PITCH_TEXT = """Bonjour à tous. En tant que Data Architecte pour ce troisième bloc de compétences, je vais vous présenter la conception et la mise en œuvre de notre pipeline de données pour la détection automatisée des fraudes aux cartes bancaires.

Dans l'Union Européenne, la fraude financière représente plus d'un milliard d'euros de préjudice annuel. Le département métier de notre banque nous a mandatés pour répondre à deux exigences opérationnelles très concrètes :
Premièrement, une alerte immédiate : dès qu'un paiement suspect survient, une notification instantanée doit être émise pour bloquer la carte ou déclencher une vérification forte.
Deuxièmement, un audit quotidien chaque matin : vérifier l'ensemble des paiements et des fraudes survenus au cours de la journée précédente pour alimenter les tableaux de bord de la direction des risques.

Face à ces deux besoins radicalement différents en termes de latence, mon rôle a été de concevoir une infrastructure hybride conciliant streaming temps réel et traitement par lots.

Pour satisfaire la première exigence de détection instantanée, nous avons banni toute logique de batch périodique au profit d'une architecture événementielle en streaming.
La source de données : nous ingérons les transactions en flux continu depuis une API de paiement en temps réel hébergée sur HuggingFace Spaces.
Le bus de messages Apache Kafka : dès qu'une transaction est reçue, notre Producer la publie instantanément dans un topic Kafka nommé raw-transactions. Kafka joue ici le rôle de tampon haute cadence, garantissant l'élasticité face aux pics de paiements sans jamais saturer notre système aval.
Le microservice d'inférence FastAPI : notre Consumer Kafka dépile chaque événement et interroge notre microservice de scoring conteneurisé. Ce service extrait les caractéristiques à la volée et calcule la probabilité de fraude en moins de trois millisecondes.
L'alerte flash : dès que la probabilité dépasse le seuil critique de 50%, notre service d'alerte déclenche une notification immédiate avec le détail de la transaction, le marchand et le porteur de carte, permettant le blocage du paiement avant son règlement définitif.

Une question fondamentale se posait : pourquoi ne pas avoir tout implémenté sous Apache Airflow, comme suggéré dans l'intitulé initial du cours ?
La réponse réside dans le compromis de latence :
Airflow est un orchestrateur de batchs planifiés. Même avec un cron toutes les cinq minutes, une fraude de mille euros serait détectée avec cinq minutes de retard : la marchandise serait déjà expédiée et le préjudice irréversible.
Kafka, à l'inverse, est conçu pour l'événementiel à la milliseconde. C'est l'outil indispensable pour l'interception de fraude en temps réel.

En revanche, Airflow retrouve toute sa légitimité pour la deuxième exigence métier : notre DAG daily-fraud-audit s'exécute chaque matin à six heures UTC. Il extrait l'historique des vingt-quatre dernières heures depuis notre base opérationnelle, consolide le taux de fraude, identifie les catégories de marchands les plus attaquées et génère le rapport matinal pour la direction financière.
Nous avons donc l'alliance idéale : Kafka pour la protection instantanée, Airflow pour la gouvernance et l'audit.

Sur le plan de l'intelligence artificielle et de la donnée :
Nous avons entraîné un algorithme HistGradientBoosting sur les 550 000 transactions réelles du jeu de données avec rééquilibrage de classe.
Au-delà du montant de la transaction, notre variable la plus discriminante est la distance orthodromique de Haversine, calculée en temps réel entre les coordonnées GPS du client et celles du terminal de paiement. Un paiement physique à 500 kilomètres du domicile du client est un signal immédiat d'anomalie.
Notre modèle atteint un ROC-AUC de 0.9866 et intercepte plus de 92% des fraudes réelles.
Enfin, chaque transaction enrichie de son score et de sa décision est persistée avec garanties ACID dans notre base de données relationnelle, garantissant une traçabilité intégrale pour les audits bancaires et la conformité PCI-DSS.

Le code source de l'ensemble de cette infrastructure est entièrement modulaire et opérationnel dans notre repository : de l'entraînement au conteneur de l'API, jusqu'au cluster Kafka et au DAG Airflow.
Comme vous allez le voir dans notre démonstration live, le pipeline ingère les flux de transactions, discrimine les opérations légitimes en vert et fait retentir l'alerte dès qu'une anomalie critique est détectée, avant de compiler le rapport quotidien.
Ce pipeline illustre parfaitement le rôle de l'Architecte IA : concevoir une chaîne de bout en bout résiliente, scalable et directement alignée sur la rentabilité de l'entreprise.

Je vous remercie pour votre attention et je suis à votre disposition pour vos questions."""

def synthesize():
    base_dir = r"d:\AIL-FT-02\CERTIF AIL\FRAUD_DETECTION_BLOC_3"
    out_mp3 = os.path.join(base_dir, "pitch_defense_5min_bloc3.mp3")
    out_wav = os.path.join(base_dir, "pitch_defense_5min_bloc3.wav")

    print("=" * 65)
    print("🎙️ GÉNÉRATION AUDIO DU PITCH ORAL BLOC 3 (KOKORO-82M GPU)")
    print("=" * 65)

    chunker = SmartTextChunker(max_chars=220)
    chunks = chunker.split_text(PITCH_TEXT, clean_markdown=True)
    print(f"✨ Script découpé en {len(chunks)} phrases optimisées.")

    print("🚀 Initialisation du moteur Kokoro-82M sur RTX 3060...")
    engine = KokoroEngine()
    engine.initialize()

    voice = "ff_siwis"
    print(f"🗣️ Voix sélectionnée : {voice} (Français Féminin Siwis - Posée & Naturelle)")
    print("⏳ Synthèse vocale haute fidélité en cours...")

    audio_segments = []
    start_total = time.time()

    for i, chunk in enumerate(chunks, 1):
        t0 = time.time()
        seg = engine.synthesize_chunk(chunk, voice=voice, speed=1.0)
        audio_segments.append(seg)
        dt = time.time() - t0
        chunk_sec = len(seg) / 24000.0
        if i % 5 == 0 or i == len(chunks):
            pct = i * 100 // len(chunks)
            print(f"  [{i:02d}/{len(chunks)}] Prog: {pct:3d}% | Segment: {chunk_sec:.1f}s généré en {dt:.2f}s")

    print("\n🔗 Concaténation avec micro-pauses respiratoires (180 ms)...")
    combined = concatenate_audio_segments(audio_segments, sample_rate=24000, silence_ms=180)
    total_audio_sec = len(combined) / 24000.0
    elapsed_total = time.time() - start_total

    print(f"💾 Sauvegarde du fichier MP3 : {out_mp3}")
    sf.write(out_mp3, combined, 24000, format='MP3')

    print(f"💾 Sauvegarde du fichier WAV : {out_wav}")
    sf.write(out_wav, combined, 24000, format='WAV')

    size_mp3_mb = os.path.getsize(out_mp3) / (1024 * 1024)
    minutes = int(total_audio_sec // 60)
    seconds = int(total_audio_sec % 60)

    print("\n" + "=" * 65)
    print("✅ PITCH AUDIO BLOC 3 GÉNÉRÉ AVEC SUCCÈS !")
    print(f"⏱️ Durée du pitch oral : {minutes} min {seconds:02d} sec ({total_audio_sec:.1f} s)")
    print(f"⚡ Vitesse de rendu GPU : {elapsed_total:.1f} sec (RTF : {elapsed_total/total_audio_sec:.2f}x)")
    print(f"🎧 MP3 : {out_mp3} ({size_mp3_mb:.2f} Mo)")
    print("=" * 65)

if __name__ == "__main__":
    synthesize()

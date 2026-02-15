# 📅 Générateur de Planning Intelligent

Ce projet est une application web basée sur **Streamlit** conçue pour automatiser la création de plannings mensuels complexes. Il utilise la puissance de **Google OR-Tools** pour résoudre les contraintes de rotation tout en garantissant une équité maximale entre les agents.

## 🌟 Fonctionnalités Clés

*   **Intelligence Artificielle (CP-SAT)** : Résolution automatique des conflits et optimisation des rotations.
*   **Équité Algorithmique** : Distribution basée sur le ratio (Heures travaillées / Disponibilité) pour compenser les congés.
*   **Gestion Spécifique au Genre** : Intègre des règles particulières pour les agentes (ex: pas de nuit, repos week-end).
*   **Continuité Mensuelle** : Prend en compte les derniers jours du mois précédent pour éviter les doubles gardes.
*   **Exports Professionnels** : Génération instantanée de fichiers Excel (Global et par Agent).
*   **Interface Intuitive** : Gestion simple des congés et des paramètres de l'équipe via une interface moderne.

## 🛠️ Installation

1.  Assurez-vous d'avoir Python 3.8 ou plus installé.
2.  Installez les dépendances nécessaires :
    ```bash
    pip install streamlit pandas ortools openpyxl
    ```
3.  Lancez l'application :
    ```bash
    streamlit run app.py
    ```

## 🏗️ Structure du Projet

*   `app.py` : Interface utilisateur Streamlit et logique de présentation.
*   `scheduler.py` : Moteur de calcul (Cœur de l'application) utilisant OR-Tools.
*   `constraints_reference.md` : Documentation technique des règles métier.
*   `export_utils.py` : Utilitaires pour la génération de fichiers Excel.

## 📝 Licence
Développé par **Abdennour Ryahi**.

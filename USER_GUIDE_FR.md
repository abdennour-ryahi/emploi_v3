# 📖 Guide Utilisateur - Générateur de Planning Intelligent

Ce guide détaille les étapes pour configurer et générer votre planning mensuel avec succès.

## 1. Configuration Initiale (Barre latérale)

Avant toute chose, configurez les paramètres de base dans le menu à gauche :

*   **Année & Mois** : Sélectionnez la période cible. L'application calcule automatiquement le nombre de jours.
*   **Nombre d'agents** : Ajustez le curseur (min 3, max 10 agents).
*   **Identité des Agents** :
    *   **Pseudo** : Donnez un nom court à chaque agent.
    *   **Sexe** : Définit les règles applicables. Les femmes (ex: Mme Mliyani) ne font pas de nuits et ont leurs week-ends libres.
*   **Jours Fériés** : Sélectionnez les jours de fête nationale. Ces jours seront automatiquement chômés pour les agentes.

## 2. Gestion des Congés & Absences

Dans l'onglet principal, vous trouverez un onglet pour chaque agent :

*   Sélectionnez les jours où l'agent doit être en **repos forcé** (vacances, formation, etc.).
*   L'algorithme s'adaptera pour couvrir la charge de travail avec les agents restants.

## 3. Historique & Continuité

Pour éviter qu'un agent travaille trop en début de mois après avoir fini le mois précédent de manière intense :

*   Ouvrez la section **"Historique (3 derniers jours)"**.
*   Renseignez le dernier poste occupé par chaque agent (Jour, Nuit ou Repos) pour les jours J-1, J-2 et J-3.

## 4. Génération et Analyse

### Lancer le calcul
Cliquez sur le bouton **"🚀 Générer le Planning Optimisé"**. Si l'algorithme trouve une solution (en général moins de 10 secondes), le planning s'affiche.

### Comprendre les Résultats
*   **Tableau de Bord** : Visualisez le nombre de matins/nuits par personne et la charge de travail relative.
*   **Vue Globale** : Un calendrier couleur par jour.
*   **Vue par Agent (Pivot)** : Un tableau Excel-style montrant la rotation de chaque personne (J = Jour, N = Nuit, Vide = Repos).

## 5. Exportation

Utilisez les boutons de téléchargement en bas de page :
*   **Excel Global** : Pour impression et affichage collectif.
*   **Excel par Agent** : Utile pour une lecture rapide des rotations individuelles.

## ❓ Que faire si "Aucune solution trouvée" ?

Si l'application n'affiche rien, c'est que les contraintes sont mathématiquement impossibles à résoudre. Essayez de :
1.  Réduire le nombre de congés simultanés.
2.  Vérifier que vous avez assez d'agents (min 6 recommandés pour 2 personnes par poste).
3.  Vérifier l'historique de continuité.

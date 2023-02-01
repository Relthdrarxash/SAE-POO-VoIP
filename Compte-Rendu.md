<!-- markdownlint-disable MD036 MD033 MD024 -->
<!-- omit in toc -->
# Compte Rendu - SAE POO 2023

**Titre - Compte Rendu Projet DevCloud**

**Auteurs:**
    **- Noilou Quentin**
    **- Person Mathys**
    **- Rocabois Damien**

**Créé le - 28 Janvier 2023**

---

- [Fonctionnalités](#fonctionnalités)
  - [Serveur](#serveur)
    - [Fonctionnalités de la base de données](#fonctionnalités-de-la-base-de-données)
    - [Fonctionnalités du serveur](#fonctionnalités-du-serveur)
    - [Fonctionnalités de l'interface utilisateur](#fonctionnalités-de-linterface-utilisateur)
  - [Client](#client)
    - [Connexion au serveur](#connexion-au-serveur)
    - [Appel en direct](#appel-en-direct)
    - [Interface utilisateur](#interface-utilisateur)
    - [Utilisation de thread](#utilisation-de-thread)
- [Protocoles](#protocoles)
  - [Protocole Communication serveur](#protocole-communication-serveur)
  - [Protocole Communication client](#protocole-communication-client)
- [Diagrammes des flux](#diagrammes-des-flux)
  - [Appel Normal](#appel-normal)
  - [Appel refusé](#appel-refusé)
  - [Double Appel](#double-appel)
- [Gestion des erreurs](#gestion-des-erreurs)
  - [Client](#client-1)
- [Gestion de projet](#gestion-de-projet)
  - [Répartition des tâches](#répartition-des-tâches)
  - [Communication](#communication)
  - [Gestion des risques](#gestion-des-risques)
  - [Retex](#retex)
    - [Quentin](#quentin)
    - [Mathys](#mathys)
    - [Damien](#damien)
    - [Groupe](#groupe)
  - [Gantt](#gantt)
- [Evolutions possibles](#evolutions-possibles)
- [TODO](#todo)

 <div style='page-break-before: always;' />

## Fonctionnalités

### Serveur

- Lancement d'une écoute sur le port 10000 et l'adresse qui permet de contacter le WAN (à défaut d'accès WAN, il faut hardcoder l'adresse)

#### Fonctionnalités de la base de données

- Enregistrement d'utilisateurs avec un nom d'utilisateur et une adresse IP
- Récupération de l'adresse IP d'un utilisateur en utilisant son nom d'utilisateur
- Suppression d'utilisateurs en utilisant leur nom d'utilisateur

#### Fonctionnalités du serveur

- Écoute de nouvelles connexions de clients
- Traitement des commandes reçues des clients (REG, GET, DISCONNECT)
- Envoi de réponses aux clients en fonction des commandes reçues
- Gestion des erreurs et des déconnexions de clients :
  - Si le client se déconnecte ou ferme la connexion TCP, suppression du client dans la BDD

#### Fonctionnalités de l'interface utilisateur

- Affichage du socket d'écoute
- Affichage des informations de journalisation pour suivre les activités du serveur
- Bouton pour fermer le serveur et quitter l'application.

### Client

- Pas de connaissance de sa propre IP, c'est le serveur qui enregistre l'IP avec laquelle il a été contacté (pas de support du NAT)

#### Connexion au serveur

- Le client peut se connecter à un serveur en saisissant l'adresse IP et le port dans la fenêtre de connexion.
- Le client peut envoyer son nom d'utilisateur au serveur lors de la connexion.
- Le client peut recevoir la liste des utilisateurs en ligne du serveur et l'afficher dans sa fenêtre.
- Le client peut se déconnecter du serveur en utilisant le bouton de déconnexion ou en fermant la fenêtre.

#### Appel en direct

- Le client peut envoyer une demande d'appel à un autre utilisateur en ligne en sélectionnant son nom dans la liste des utilisateurs et en appuyant sur le bouton "Appeler".
- Le client peut recevoir une demande d'appel d'un autre utilisateur dans une fenêtre contextuelle, avec les options pour accepter ou rejeter l'appel.
- Le client peut accepter ou rejeter un appel en utilisant les boutons appropriés dans la fenêtre contextuelle d'appel entrant.
- Le client peut transmettre et recevoir de l'audio en direct avec un autre utilisateur lorsqu'un appel est accepté.
- Le client peut raccrocher à un appel en cours en utilisant le bouton "Raccrocher" ou en fermant la fenêtre.

#### Interface utilisateur

- Le client a une interface graphique avec une fenêtre de connexion, une fenêtre principale et une fenêtre contextuelle pour les appels entrants.
- Le client affiche des messages dans une zone de texte pour indiquer les actions en cours, comme la connexion au serveur, les demandes d'appel et les appels en cours.
- Le client utilise des boutons pour les actions telles que la connexion, l'appel, l'acceptation et le rejet des appels, et le raccrochage.

#### Utilisation de thread

- Le client utilise des threads pour écouter les demandes d'appel entrantes en arrière-plan, pour transmettre et recevoir de l'audio en direct lors d'un appel, et pour se déconnecter du serveur en arrière-plan

## Protocoles

Voici le protocole que nous avons mis en place :

### Protocole Communication serveur

Via le protocole TCP :

`{"command": "GET", "name": nom_destinataire}` : Récupère l'adresse IP associée au nom demandé, si le client n'existe pas, retourne "None".

Réponses possibles :

- `{"ip": "None"}`
- `{"ip": 127.0.0.1}`

`{"command": "REG", "name": nom_client}` : Envoie une demande d'enregistrement au serveur avec notre nom. Le serveur récupère automatiquement notre ip depuis le paquet qu'il reçoit (en-tête IP).

Réponses possibles :

- `{"ack": "Registered successfully"}` : l'enregistrement s'est bien déroulé dans la BDD
- `{"ack": "Error Registering"}` : la BDD n'a pas pu enregistrer notre nom
- `{"ack": "Error"}` : le serveur a buggé pour nous enregistrer

`{"command": "DISCONNECT", "name": nom_client}` : permet la déconnexion propre du client connecté au serveur (fermeture thread et socket de connexion, suppression de l'entrée dans la BDD)

### Protocole Communication client

Lorsqu'on envoie une demande d'appel, le socket d'écoute se ferme.
De même, lorsqu'on reçoit une demande d'appel, on ferme notre socket d'écoute le temps de répondre

`"START nom_appellant"` : Envoie une demande d'appel à l'appelé après avoir récupéré son IP à partir du serveur, ferme l'écoute sur le socket

`"ACCEPT"` : Accepte une demande d'appel reçu, ouvre l'échange d'audio (fonction transmit_audio())

`"REJECT"`: Rejette une demande d'appel reçu, rouvre l'écoute sur le socket

`"CLOSE"` : Permet de raccrocher (fermeture socket et pyaudio en écoute et écriture), rouvre l'écoute sur le socket

## Diagrammes des flux

Le serveur est en écoute sur le port 10000 par défaut.

 <div style='page-break-before: always;' />

### Appel Normal

```mermaid
sequenceDiagram
    Note over Client A: Enregistrement de "Client A"
    Client A->>Serveur:TCP | {"cmd" : "REG", "name" : "Client A"}
    Serveur->>Client A:TCP | {"ack": "Registered successfully"}
    Note over Client A: Mise en écoute port 5001
    Note over Client B: Enregistrement de "Client B"
    Client B->>Serveur:TCP | {"cmd" : "REG", "name" : "Client B"}
    Serveur->>Client B:TCP | {"ack": "Registered successfully"}
    Note over Client B: Mise en écoute port 5001
    Note over Client A: Appel de "Client A" vers "Client B"
    Client A->>Serveur: TCP | {"command": "GET", "name": "Client B"}
    Serveur->>Client A: TCP | {"ip": "{ip Client B}"}
    Note over Client A: Fermeture écoute port 5001
    Client A-->>Client B: UDP | "START client A"
    Note over Client B: Authentification Client A
    Client A->>Serveur: TCP | {"command": "GET", "name": "Client B"}
    Serveur->>Client A: TCP | {"ip": "{ip Client B}"}
    Client B-->>Client A: UDP | "ACCEPT"
    Note over Client B: Fermeture écoute port 5001
    Note over Serveur: Phase d'échange voix simultané
    Client A-->>Client B: UDP | ~données voix~
    Client B-->>Client A: UDP | ~données voix~
    Note over Serveur: Fermeture de l'appel si A raccroche
    Client A-->>Client B: UDP | "CLOSE"
    Note over Client A: Mise en écoute port 5001
    Note over Client B: Mise en écoute port 5001
```

 <div style='page-break-before: always;' />

### Appel refusé

```mermaid
sequenceDiagram
    Note over Client A: Enregistrement de "Client A"
    Client A->>Serveur:TCP | {"cmd" : "REG", "name" : "Client A"}
    Serveur->>Client A:TCP | {"ack": "Registered successfully"}
    Note over Client A: Mise en écoute port 5001
    Note over Client B: Enregistrement de "Client B"
    Client B->>Serveur:TCP | {"cmd" : "REG", "name" : "Client B"}
    Serveur->>Client B:TCP | {"ack": "Registered successfully"}
    Note over Client B: Mise en écoute port 5001
    Note over Client A: Appel de "Client A" vers "Client B"
    Client A->>Serveur: TCP | {"command": "GET", "name": "Client B"}
    Serveur->>Client A: TCP | {"ip": "{ip Client B}"}
    Note over Client A: Fermeture écoute port 5001
    Client A-->>Client B: UDP | "START client A"
    Client B-->>Client A: UDP | "REJECT"
    Note over Client A: Mise en écoute port 5001
```

 <div style='page-break-before: always;' />

### Double Appel

```mermaid
sequenceDiagram
    Note over Client A: Enregistrement de "Client A"
    Client A->>Serveur:TCP | {"cmd" : "REG", "name" : "Client A"}
    Serveur->>Client A:TCP | {"ack": "Registered successfully"}
    Note over Client A: Mise en écoute port 5001
    Note over Client B: Enregistrement de "Client B"
    Client B->>Serveur:TCP | {"cmd" : "REG", "name" : "Client B"}
    Serveur->>Client B:TCP | {"ack": "Registered successfully"}
    Note over Client B: Mise en écoute port 5001
    Client C->>Serveur:TCP | {"cmd" : "REG", "name" : "Client B"}
    Serveur->>Client C:TCP | {"ack": "Registered successfully"}
    Note over Client C: Mise en écoute port 5001
    Note over Client A: Appel de "Client A" vers "Client B"
    Client A->>Serveur: TCP | {"command": "GET", "name": "Client B"}
    Serveur->>Client A: TCP | {"ip": "{ip Client B}"}
    Note over Client A: Fermeture écoute port 5001
    Client A-->>Client B: UDP | "START client A"
    Client B-->>Client A: UDP | "ACCEPT"
    Note over Client B: Fermeture écoute port 5001
    Note over Serveur: Phase d'échange voix simultané
    Client A-->>Client B: UDP | ~données voix~
    Note over Client C: Fermeture écoute port 5001
    Client C-->>Client B: UDP | "START client C"
    Note over Client C: Timeout 7 secondes
    Note over Client C: Mise en écoute port 5001
    Client B-->>Client A: UDP | ~données voix~
    Note over Serveur: Fermeture de l'appel si A raccroche
    Client A-->>Client B: UDP | "CLOSE"
    Note over Client A: Mise en écoute port 5001
    Note over Client B: Mise en écoute port 5001
```

## Gestion des erreurs

Codes de sortie :

- 0 : Code complété correctement
- 1 : Avertissement (non critique)
- 2 : Erreur critique
- 3 : Erreur inconnue

XXX METTRE LES SCREENS

### Client

<!-- omit from toc -->
#### Si un client est déjà lancé sur un ordinateur et qu'un socket est déjà bind

Alors la fenêtre principale se ferme en annoncant l'erreur dans la sortie standard (Terminal).
Exit code : 2 (CRITICAL)

## Gestion de projet

### Répartition des tâches

Nous avons décidé de diviser le projet en 2 parties:

- Le "Front-end", qui correspond aux interfaces graphiques
- Le "Back-end", qui correspond aux gestions de la base de données, des flux réseaux, des threads etc...

De fait, chacun s'est retrouvé avec des missions claires :

- Mathys :

  - Design de l'IHM du serveur
  - Création de l'IHM du serveur
  - Accords avec Quentin concernant les fonctionnalités attendues de l'interface du serveur (logs, bouton de fermeture, affichage du socket d'écoute)
  - Interfaçage avec le back-end (relier les boutons aux fonctions)

- Damien :
  - Design de l'IHM du client
  - Création de l'IHM du client
  - Accords avec Quentin concernant les fonctionnalités attendues de l'interface du client (logs, bouton de configuration, connexion, appel, raccrochage, pop-up lorsqu'on reçoit un appel)
  - Interfaçage avec le back-end (relier les boutons aux fonctions)

- Quentin

  - Design du fonctionnement de l'application
    - Flux résaux (ports d'écoute et d'envoi)

  - Etablissement du protocole téléphonique (Cf. [Ici](#protocoles))
  - Gestion des threads
  - Gestion de la BDD
  - Gestion des sockets

### Communication

Pour ce projet, nous avons utilisé Discord avec des channels spécifiques(Front, Back, IHM-Back Serveur, IHM-Back Client).

Ainsi nous pouvions retrouver nos conversations facilement lorsqu'elles concernaient des points spécifiques.

Nous avions également un channel général pour planifier les séances d'autonomie et nos réunions.

### Gestion des risques

Pour éviter de perdre notre avancée, nous avons utilisé github pour héberger nos codes sources, gérer le versioning et collaborer plus facilement.

### Retex

#### Quentin

#### Mathys

#### Damien

#### Groupe

|Ce qu'on a bien réussi|Ce qu'on aurait pu améliorer|
|-|-|
|Les IHM sont modernes efficaces (logs, boutons simples)||
|Le protocole d'échange|La sécurité des échanges : on aurait pu inclure une fonction de chiffrement de la voix et un échange de clé secrète pour mieux gérer la confidentialité de l'appel|
Ce qu'on a bien réussi: Les interfaces sont designs, d'un côté le serveur met à jour la bed toute les secondes et on a les informations de connexion, ce qui est un avantage.
Ce qu'on aurait pu améliorer : On aurait pu gérer les différents cas de figure tel qu'un appel intervenant dans l'appel déjà existant entre deux clients par exemple. On aurait aussi pu gérer la sécurité car n'importe qui sur le réseau peut récupérer le flux TCP mais nous avons décidé d'aller au plus simple

### Gantt

```mermaid
gantt
    title Conception d'un client de téléphonie
    dateFormat  YYYY-MM-DD
    section Serveur
        Conception de l'architecture:active, 2021-01-01,2021-01-10
        Implémentation des fonctionnalités de base:active, 2021-01-11,2021-01-25
        Test et débogage:active, 2021-01-26,2021-02-01
    section Client
        Conception de l'interface utilisateur:active, 2021-02-01,2021-02-10
        Implémentation des fonctionnalités de base:active, 2021-02-11,2021-03-01
        Test et débogage:active, 2021-03-02,2021-03-15
    section Fin
        Présentation :active, 2021-03-16,2021-03-20
```

## Evolutions possibles

- Ajout d'une fonctionnalité de chat en direct pendant un appel: Il serait possible d'ajouter une fonctionnalité de chat en direct pendant un appel, qui permettrait aux utilisateurs de communiquer par écrit en plus de parler.

- Ajout d'une fonctionnalité de partage d'écran: Il serait possible d'ajouter une fonctionnalité de partage d'écran pour permettre aux utilisateurs de partager leur écran avec les autres utilisateurs en cours d'appel.

- Support de plusieurs utilisateurs en appel simultanément: Il serait possible d'ajouter une fonctionnalité de conférence téléphonique pour permettre à plusieurs utilisateurs de participer à un appel simultanément.

- Ajout de fonctionnalités de sécurité: Il serait possible d'ajouter des fonctionnalités de sécurité pour protéger les communications, comme la chiffrement de bout en bout pour garantir la confidentialité des conversations.

- Ajout de fonctionnalités de personnalisation: Il serait possible d'ajouter des fonctionnalités de personnalisation pour permettre aux utilisateurs de personnaliser l'apparence de l'application, comme changer les couleurs, les polices, etc.

## TODO

- Décrire le fonctionnement avec des Screenshots des applications aux différentes étapes
- Repasser sur les fonctionnalités pour vérifier que tout est correct et bien décrit
- Dire ce qu'on a aimé ou pas dans le projet
- Pour Gantt, dire ce qui allait ou pas, ce qui nous a pris le plus de temps etc

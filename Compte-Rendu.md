<!-- markdownlint-disable MD036 MD033 MD024 -->
<!-- omit in toc -->
# Compte Rendu - SAE POO 2023

**Titre - Compte Rendu Projet DevCloud**

**Auteurs:**
    **- Noilou Quentin**
    **- Person Mathys**
    **- Rocabois Damien**

**Créé le - 11 novembre 2022**

---

- [Fonctionnalités](#fonctionnalités)
  - [Démarrage Serveur](#démarrage-serveur)
    - [Fonctionnalités de la base de données](#fonctionnalités-de-la-base-de-données)
    - [Fonctionnalités du serveur](#fonctionnalités-du-serveur)
    - [Fonctionnalités de l'interface utilisateur](#fonctionnalités-de-linterface-utilisateur)
  - [Configuration Client](#configuration-client)
- [Diagrammes des flux](#diagrammes-des-flux)
  - [Appel Normal](#appel-normal)
  - [Appel refusé](#appel-refusé)
  - [Double Appel](#double-appel)

 <div style='page-break-before: always;' />

## Fonctionnalités

### Démarrage Serveur

#### Fonctionnalités de la base de données

- Enregistrement d'utilisateurs avec un nom d'utilisateur et une adresse IP
- Récupération de l'adresse IP d'un utilisateur en utilisant son nom d'utilisateur
- Suppression d'utilisateurs en utilisant leur nom d'utilisateur

#### Fonctionnalités du serveur

- Écoute de nouvelles connexions de clients
- Traitement des commandes reçues des clients (REG, GET, DISCONNECT)
- Envoi de réponses aux clients en fonction des commandes reçues
- Gestion des erreurs et des déconnexions de clients

#### Fonctionnalités de l'interface utilisateur

- Affichage des informations de journalisation pour suivre les activités du serveur
- Bouton pour fermer le serveur et quitter l'application.

Threads

Son adresse est récupérée en envoyant un paquet à 8.8.8.8 et en utilisant l'IP depuis laquelle il envoie le paquet. Cette méthode permet d'utiliser une adresse IP qui a un accès à internet.
Il est également possible de la "hardcoder" si on se trouve dans un réseau sans accès internet.

### Configuration Client

- Pas de connaissance de sa propre IP, c'est le serveur qui enregistre l'IP avec laquelle il a été contacté (pas de support du NAT)

## Diagrammes des flux

Le serveur est en écoute sur le port 10000 par défaut.

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
    Note over Client B: Timeout 7 secondes
    Note over Client C: Mise en écoute port 5001
    Client C-->>Client B: UDP | "START client C"
    Client B-->>Client A: UDP | ~données voix~
    Note over Serveur: Fermeture de l'appel si A raccroche
    Client A-->>Client B: UDP | "CLOSE"
    Note over Client A: Mise en écoute port 5001
    Note over Client B: Mise en écoute port 5001
```

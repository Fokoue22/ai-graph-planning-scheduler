# AI Graph Planning Scheduler

Planificateur de taches base sur Graphplan en Python.

Ce projet implemente une strategie de planification par graphe de synthese pour construire un plan d'actions optimal (au sens du nombre minimal d'actions) permettant d'atteindre des objectifs a partir d'un etat initial.

## 1) Objectif du projet

Au sein du planificateur, l'appel de la fonction logique `DoPlan(r_ops, r_facts)` retourne un plan d'actions qui satisfait les objectifs cibles a partir des conditions de depart.

- `r_ops`: fichier texte contenant la liste des operateurs autorises (actions)
- `r_facts`: fichier texte contenant les conditions initiales et les objectifs

Un plan est considere optimal s'il contient le moins d'actions possible parmi les plans valides trouves.

## 2) Strategie utilisee

Le projet suit l'algorithme Graphplan:

1. Construction progressive d'un graphe de planification (niveaux de faits et d'actions)
2. Calcul des relations de mutex (incompatibilites) entre faits et entre actions
3. Verification de la presence des objectifs a un niveau donne
4. Extraction retrograde d'un plan sans conflits
5. Expansion du graphe si aucun plan valide n'est extractible au niveau courant

Cette approche garantit la recherche d'un plan de longueur minimale en termes de niveaux de planification lorsque le probleme est solvable.

## 3) Ce qui a ete implemente

Le depot contient une implementation complete et testable avec separation des responsabilites:

- Lecture et parsing des fichiers d'entree (`parser.py`)
- Construction et gestion du graphe de planification (`planning_graph.py`)
- Coeur de l'algorithme Graphplan (`graphplan.py`)
- Point d'entree d'execution (`main.py`)
- Script de reproduction d'un cas fourni (`run_fact9.py`)
- Traces/resultats d'execution pour validation (`trace_case3.txt`, `trace_case9.txt`, `fact9_out.txt`, `fact9_summary.txt`)
- Jeux de donnees d'exemple (`Exemples/`)

## 4) Structure des fichiers / Architecture

Vue d'ensemble du depot:

```text
ai-graph-planning-scheduler/
|- Exemples/
|  |- r_ops.txt
|  |- r_fact2.txt ... r_fact9.txt
|  |- simulation_fact2.txt ... simulation_fact9.txt
|  |- my_case3.txt
|  `- my_case9.txt
|- parser.py
|- planning_graph.py
|- graphplan.py
|- main.py
|- run_fact9.py
|- trace_case3.txt
|- trace_case9.txt
|- fact9_out.txt
|- fact9_summary.txt
|- readme.txt
`- README.md
```

Architecture logique:

- `main.py`: point d'entree CLI, orchestration globale et affichage des resultats
- `parser.py`: lecture/validation des fichiers `r_ops` et `r_facts`
- `planning_graph.py`: construction des niveaux de faits/actions et gestion des mutex
- `graphplan.py`: extraction du plan, backtracking et controle d'optimalite
- `run_fact9.py`: script de demonstration/reproduction rapide sur un cas de reference
- `Exemples/`: jeux d'essai pour verifier la conformite des entrees/sorties
- `trace_*.txt` et `fact9_*.txt`: traces et sorties de verification

Flux principal:

1. `main.py` recoit les chemins des fichiers d'entree
2. `parser.py` transforme les fichiers texte en structures internes
3. `planning_graph.py` construit le graphe couche par couche
4. `graphplan.py` tente l'extraction d'un plan valide et minimal
5. Le plan (ou l'echec) est affiche/sauvegarde selon le mode d'execution

## 5) Structure des fichiers d'entree

Le projet suit le format d'E/S attendu dans l'enonce et les exemples fournis.

- Fichier operateurs (ex: `Exemples/r_ops.txt`)
- Fichier faits/objectifs (ex: `Exemples/r_fact9.txt`)

Important: dans cette version, l'appel standard est base sur deux fichiers (`r_ops` et `r_facts`) afin de rester conforme a la specification generale.

## 6) Execution rapide

Depuis la racine du projet:

```bash
python main.py Exemples/r_ops.txt Exemples/r_fact9.txt
```

Ou via le script dedie au cas 9:

```bash
python run_fact9.py
```

Selon la configuration du script principal, la sortie affiche:

- Le statut (plan trouve ou non)
- La sequence d'actions du plan
- Eventuellement des informations de trace/debug

## 7) Correspondance avec la description du TP

Ce qui est respecte par rapport a la description:

- Implementation en Python
- Utilisation de Graphplan comme strategie de planification
- Traitement des operateurs et faits via fichiers texte
- Recherche d'un plan valide et optimal (minimal en nombre d'actions/niveaux)
- Format inspire des exemples fournis pour faciliter l'evaluation

## 8) Exemples inclus

Le dossier `Exemples/` contient plusieurs cas (`r_fact2`, `r_fact3`, ..., `r_fact9`) ainsi que des fichiers de simulation. Cela permet:

- De verifier le comportement sur differents problemes
- De comparer les sorties avec les traces deja generees
- De reproduire rapidement des scenarios vus pendant le developpement

## 9) Limites et pistes d'amelioration

Ameliorations possibles pour une version production:

- Ajouter des tests unitaires automatises pour parser, mutex et extraction de plan
- Ajouter une sortie structurée (JSON) en plus du mode texte
- Ameliorer les performances memoisation/backtracking sur les grands problemes
- Ajouter une CLI plus robuste (validation des arguments, niveaux de verbosite)
- Ajouter une visualisation du graphe de planification

## 10) Credits

Projet realise dans le cadre du cours IFT702 - Planification en intelligence artificielle, puis structure en depot Git autonome pour conservation, reproductibilite et evolution.

## 11) Auteur

Ce projet a ete realise par **Fokoue Thomas**. La conception, l'implementation et l'integration des elements du projet ont ete effectuees par l'auteur.


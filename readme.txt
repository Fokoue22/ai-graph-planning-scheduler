======================================================================
 GRAPHPLAN — Rocket Domain Planner
 IFT702 — Planification en intelligence artificielle — TP2
=====================================================================

----------------------------------------------------------------------
 STRUCTURE DES FICHIERS
----------------------------------------------------------------------
  main.py           — Point d'entrée (ligne de commande)
  graphplan.py      — Algorithme Graphplan : DoPlan(), EXPAND-GRAPH,
                      EXTRACT-SOLUTION, trace détaillée
  planning_graph.py — Structures de données : PlanningGraph,
                      PropositionLevel, ActionLevel, no-ops,
                      calcul des mutex
  parser.py         — Parseur r_ops.txt et r_factX.txt,
                      instanciation (grounding) des opérateurs
  Exemples/         — Fichiers d'entrée fournis
    r_ops.txt       — Opérateurs STRIPS (LOAD, UNLOAD, MOVE)
    r_fact2.txt     — 2 cargos
    r_fact3.txt     — 3 cargos (complexité 3)
    r_fact4.txt     — 4 cargos
    r_fact6.txt     — 6 cargos
    r_fact8.txt     — 8 cargos
    r_fact9.txt     — 9 cargos (complexité 9)
    simulation_factX.txt — Plans de référence

---------------------------------------------------------------------
 UTILISATION
---------------------------------------------------------------------
Python 3.7+ requis. Aucune librairie tierce nécessaire.

  Forme courte (1 fichier - r_ops.txt pris dans Exemples/ par défaut) :
    python main.py Exemples/r_fact2.txt

  Forme complète (2 fichiers) :
    python main.py Exemples/r_ops.txt Exemples/r_fact2.txt 

  DoPlan peut aussi être appelée directement depuis Python :
    from graphplan import DoPlan
    plan = DoPlan("Exemples/r_ops.txt", "Exemples/r_fact2.txt")

DoPlan requiert DEUX fichiers : r_ops (opérateurs) et r_facts (faits). 
Nous n’avons pas encodé les opérateurs dans le code source; 
ils sont lus depuis r_ops.txt. Donc DoPlan utilise r_ops et r_facts 
(avec une forme CLI courte qui fixe r_ops par défaut).

------------------------------------------------------------------------
 SORTIE
------------------------------------------------------------------------
Le programme affiche une trace complète :
  - Objets typés et état initial
  - À chaque niveau : propositions présentes, mutex de propositions,
    actions applicables (précond/add/del), mutex d'actions
  - Le plan final trouvé (format OPERATEUR_arg1_arg2_arg3)

Pour sauvegarder la trace dans un fichier :
  python main.py Exemples/r_ops.txt Exemples/r_fact3.txt > trace_fact3.txt
  python main.py Exemples/r_ops.txt Exemples/r_fact9.txt > trace_fact9.txt

Générer les traces des nouveaux cas (complexité 3 et 9) :
  python main.py Exemples/r_ops.txt Exemples/my_case3.txt > trace_case3.txt
  python main.py Exemples/r_ops.txt Exemples/my_case9.txt > trace_case9.txt



"""
main.py
-------
Point d'entrée du planificateur Graphplan — Rocket Domain.

Usage :
    python main.py <r_ops_file> <r_facts_file>
    python main.py <r_facts_file>          (si r_ops.txt est dans le même dossier)

Exemples :
    python main.py Exemples/r_ops.txt Exemples/r_fact2.txt
    python main.py Exemples/r_fact3.txt
"""

import sys
import os
from graphplan import DoPlan

# Chemin par défaut du fichier opérateurs (même dossier que ce script)
DEFAULT_OPS = os.path.join(os.path.dirname(__file__), "Exemples", "r_ops.txt")


def main():
    if len(sys.argv) == 3:
        r_ops_file   = sys.argv[1]
        r_facts_file = sys.argv[2]
    elif len(sys.argv) == 2:
        r_ops_file   = DEFAULT_OPS
        r_facts_file = sys.argv[1]
    else:
        print("Usage :")
        print("  python main.py <r_ops_file> <r_facts_file>")
        print("  python main.py <r_facts_file>   (utilise Exemples/r_ops.txt par défaut)")
        sys.exit(1)

    if not os.path.isfile(r_ops_file):
        print(f"Erreur : fichier opérateurs introuvable : {r_ops_file}")
        sys.exit(1)
    if not os.path.isfile(r_facts_file):
        print(f"Erreur : fichier de faits introuvable : {r_facts_file}")
        sys.exit(1)

    plan = DoPlan(r_ops_file, r_facts_file)

    if plan is None:
        print("\nRésultat : AUCUN PLAN TROUVÉ (failure)")
        sys.exit(2)


if __name__ == "__main__":
    main()

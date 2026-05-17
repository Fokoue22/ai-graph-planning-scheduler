"""
graphplan.py
------------
Implémentation de l'algorithme Graphplan pour le Rocket Domain.

Point d'entrée principal :
    DoPlan(r_ops_file, r_facts_file) -> list of str (plan) ou None

La fonction génère également une trace détaillée sur stdout.
""" 

from parser import parse_operators, parse_facts, ground_operators
from planning_graph import PlanningGraph, make_noop

# Limite maximale de niveaux pour éviter une boucle infinie
MAX_LEVELS = 100


# ---------------------------------------------------------------------------
# Fonction principale DoPlan
# ---------------------------------------------------------------------------

def DoPlan(r_ops, r_facts):
    """
    Planificateur Graphplan pour le Rocket Domain.

    Paramètres :
      r_ops  : chemin vers le fichier des opérateurs (r_ops.txt)
      r_facts: chemin vers le fichier des faits (r_factX.txt)

    Retourne :
      list of str : le plan optimal (liste de noms d'actions)
      None        : si aucun plan n'est possible
    """
    # ---- 1. Parsing ----
    operators = parse_operators(r_ops)
    typed_objects, initial_state, goals = parse_facts(r_facts)

    print("=" * 70)
    print("GRAPHPLAN - ROCKET DOMAIN")
    print("=" * 70)
    print("\n[Objets par type]")
    for typ, objs in typed_objects.items():
        print(f"  {typ}: {objs}")
    print(f"\n[Etat initial] ({len(initial_state)} propositions)")
    for p in sorted(initial_state):
        print(f"  {_fmt_prop(p)}")
    print(f"\n[Objectifs] ({len(goals)} propositions)")
    for g in sorted(goals):
        print(f"  {_fmt_prop(g)}")
    print()

    # ---- 2. Grounding ----
    ground_actions = ground_operators(operators, typed_objects)
    print(f"[Actions instanciees] {len(ground_actions)} actions\n")

    # ---- 3. Construction du graphe de planification ----
    graph = PlanningGraph(initial_state, ground_actions)

    # Afficher S0
    _print_prop_level(graph.prop_levels[0], 0)

    # Pour la terminaison correcte (Blum & Furst) :
    # On arrête seulement quand le graphe ET les no_goods se sont tous deux stabilisés.
    prev_no_goods_keys = None
    graph_leveled = False

    for level in range(1, MAX_LEVELS + 1):
        # Expansion
        a_level, s_next = graph.expand()

        # Afficher le niveau d'actions et le nouveau niveau de propositions
        _print_action_level(a_level, level)
        _print_prop_level(s_next, level)

        goals_present = s_next.all_present(goals)
        goals_non_mutex = not s_next.any_mutex_pair(goals)

        if goals_present and goals_non_mutex:
            print(f"\n[Niveau {level}] Tous les objectifs sont presents et non-mutex."
                  f" Tentative d'extraction de solution...")

            # Nouvelle table no_goods pour chaque tentative de niveau distinct
            no_goods = {}
            solution = _extract_solution(graph, list(goals), level, no_goods)

            if solution is not None:
                print("\n" + "=" * 70)
                print("PLAN TROUVE :")
                print("=" * 70)
                # Filtrer les no-ops et aplatir les niveaux
                plan = _flatten_plan(solution)
                for action_name in plan:
                    print(f" {action_name}")
                print(f"\nNombre d'actions : {len(plan)}")
                print(f"Profondeur du graphe : {level} niveaux")
                return plan
            else:
                print(f"[Niveau {level}] Extraction echouee.")

            # Critere de terminaison de Blum & Furst :
            # Le graphe est stabilise ET les no_goods se sont stabilises aussi
            if graph_leveled:
                current_keys = frozenset(no_goods.keys())
                if current_keys == prev_no_goods_keys:
                    print("\n[Graphe et no_goods stabilises] Aucun plan possible.")
                    return None
                prev_no_goods_keys = current_keys

        # Detecter la stabilisation du graphe
        if graph.has_leveled_off():
            if not graph_leveled:
                print(f"\n[Niveau {level}] Le graphe a atteint son point fixe.")
            graph_leveled = True

    print("\n[Limite atteinte] Aucun plan trouve apres", MAX_LEVELS, "niveaux.")
    return None


# ---------------------------------------------------------------------------
# Extraction de solution (backtracking arrière)
# ---------------------------------------------------------------------------

def _extract_solution(graph, goals, level, no_goods):
    """
    Tente d'extraire un plan depuis le niveau `level` en remontant jusqu'à S0.

    Retourne :
      list of list of GroundAction : actions choisies à chaque niveau (du niveau 1 au niveau `level`)
      None si aucune solution trouvée
    """
    key = (frozenset(goals), level)
    if key in no_goods:
        return None

    # Cas de base : niveau 0 → vérifier que tous les goals sont dans S0
    if level == 0:
        s0 = graph.prop_levels[0]
        if s0.all_present(goals):
            return []
        return None

    s_level = graph.prop_levels[level]
    a_level = graph.action_levels[level - 1]

    # Choisir un ensemble d'actions non-mutex qui couvrent les goals
    result = _choose_actions(graph, goals, level, a_level, s_level, no_goods)

    if result is None:
        no_goods[key] = True
        return None

    return result


def _choose_actions(graph, goals, level, a_level, s_level, no_goods):
    """
    Sélectionne récursivement un ensemble d'actions non-mutex couvrant tous les goals.
    Utilise un backtracking optimisé pour les cas complexes.
    """
    goals = list(goals)

    # Pré-calcul des producteurs par goal : NOOPs d'abord pour éviter les oscillations
    producers_by_goal = {}
    for g in goals:
        producers_real = [a for a in a_level.actions
                          if g in a.add_effects and not a.name.startswith("NOOP_")]
        producers_noop = [a for a in a_level.actions
                          if g in a.add_effects and a.name.startswith("NOOP_")]
        producers_by_goal[g] = producers_noop + producers_real

    # Heuristique "most constrained first" : traiter d'abord les goals
    # qui ont le moins de producteurs réduit énormément l'espace de recherche.
    goals.sort(key=lambda g: len(producers_by_goal[g]))

    # Cache local d'échecs partiels pour éviter de revisiter les mêmes branches
    dead_ends = set()

    return _assign(
        graph=graph,
        goals=goals,
        idx=0,
        chosen=[],
        level=level,
        a_level=a_level,
        no_goods=no_goods,
        producers_by_goal=producers_by_goal,
        dead_ends=dead_ends,
    )


def _assign(
    graph,
    goals,
    idx,
    chosen,
    level,
    a_level,
    no_goods,
    producers_by_goal,
    dead_ends,
):
    """
    Assigne une action pour goals[idx], en vérifiant la compatibilité (non-mutex)
    avec les actions déjà choisies.
    """
    chosen_key = tuple(sorted(a.name for a in chosen))
    state_key = (idx, chosen_key)
    if state_key in dead_ends:
        return None

    if idx == len(goals):
        # Tous les goals couverts → récursion vers le niveau précédent
        sub_goals = set()
        for action in chosen:
            sub_goals.update(action.preconds)

        sub_result = _extract_solution(graph, list(sub_goals), level - 1, no_goods)
        if sub_result is not None:
            return sub_result + [chosen[:]]

        dead_ends.add(state_key)
        return None

    goal = goals[idx]

    # Si le goal est déjà couvert par une action déjà choisie
    for action in chosen:
        if goal in action.add_effects:
            result = _assign(
                graph,
                goals,
                idx + 1,
                chosen,
                level,
                a_level,
                no_goods,
                producers_by_goal,
                dead_ends,
            )
            if result is None:
                dead_ends.add(state_key)
            return result

    producers = producers_by_goal.get(goal, [])

    for action in producers:
        # Vérifier non-mutex avec toutes les actions déjà choisies
        compatible = True
        for chosen_action in chosen:
            if a_level.is_mutex(action, chosen_action):
                compatible = False
                break
        if not compatible:
            continue

        # Essayer cette action
        chosen.append(action)
        result = _assign(
            graph,
            goals,
            idx + 1,
            chosen,
            level,
            a_level,
            no_goods,
            producers_by_goal,
            dead_ends,
        )
        if result is not None:
            return result
        chosen.pop()

    dead_ends.add(state_key)
    return None


# ---------------------------------------------------------------------------
# Aplatir le plan (supprimer no-ops, conserver l'ordre logique)
# ---------------------------------------------------------------------------

def _flatten_plan(solution):
    """
    `solution` est une liste de listes d'actions, une par niveau (niveau 1 -> niveau n).
    On supprime les no-ops et on retourne la liste aplatie des noms d'actions.
    """
    plan = []
    seen = set()
    for level_actions in solution:
        for action in level_actions:
            if not action.name.startswith("NOOP_") and action.name not in seen:
                plan.append(action.name)
                seen.add(action.name)
    return plan


# ---------------------------------------------------------------------------
# Utilitaires d'affichage (trace détaillée)
# ---------------------------------------------------------------------------

def _fmt_prop(prop):
    """Formate un tuple de proposition en string lisible."""
    return "(" + " ".join(prop) + ")"


def _print_prop_level(s_level, k):
    """Affiche un niveau de propositions avec ses mutex."""
    print(f"\n{'-' * 60}")
    print(f"  NIVEAU {k} DE PROPOSITIONS  ({len(s_level.propositions)} props, "
          f"{len(s_level.mutex)} paires mutex)")
    print(f"{'-' * 60}")
    print("  Propositions :")
    for p in sorted(s_level.propositions):
        print(f"    {_fmt_prop(p)}")
    if s_level.mutex:
        print("  Mutex de propositions :")
        for pair in sorted(s_level.mutex, key=lambda x: str(sorted(x, key=str))):
            pair_list = sorted(pair, key=str)
            print(f"    {_fmt_prop(pair_list[0])}  ||  {_fmt_prop(pair_list[1])}")


def _print_action_level(a_level, k):
    """Affiche un niveau d'actions (sans les no-ops pour la lisibilite) avec ses mutex."""
    real_actions = [a for a in a_level.actions if not a.name.startswith("NOOP_")]
    real_mutex = [pair for pair in a_level.mutex
                  if not any(a.name.startswith("NOOP_") for a in pair)]

    print(f"\n{'-' * 60}")
    print(f"  NIVEAU {k} D'ACTIONS  ({len(real_actions)} vraies actions, "
          f"{len(a_level.actions) - len(real_actions)} no-ops, "
          f"{len(a_level.mutex)} paires mutex totales)")
    print(f"{'-' * 60}")
    print("  Actions applicables (hors no-ops) :")
    for a in sorted(real_actions, key=lambda x: x.name):
        print(f"    {a.name}")
        print(f"      Précond : {', '.join(_fmt_prop(p) for p in sorted(a.preconds))}")
        print(f"      Add     : {', '.join(_fmt_prop(p) for p in sorted(a.add_effects))}")
        print(f"      Del     : {', '.join(_fmt_prop(p) for p in sorted(a.del_effects))}")

    if real_mutex:
        print("  Mutex d'actions (entre vraies actions) :")
        for pair in sorted(real_mutex, key=lambda x: str(sorted(x, key=lambda a: a.name))):
            pair_list = sorted(pair, key=lambda a: a.name)
            print(f"    {pair_list[0].name}  ||  {pair_list[1].name}")

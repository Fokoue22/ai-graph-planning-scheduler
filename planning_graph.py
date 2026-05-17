"""
planning_graph.py
-----------------
Structure du graphe de planification utilisée par l'algorithme Graphplan.

Niveaux alternés :
  PropositionLevel (S0) -> ActionLevel (A1) -> PropositionLevel (S1) -> ...
""" 

from parser import GroundAction


# ---------------------------------------------------------------------------
# No-op (action de persistance)
# ---------------------------------------------------------------------------

def make_noop(prop):
    """
    Crée une action de persistance pour la proposition `prop`.
    Précond = {prop}, add = {prop}, del = {}.
    """
    name = "NOOP_" + "_".join(prop)
    return GroundAction(name, [prop], [prop], [])


# ---------------------------------------------------------------------------
# Niveau de propositions
# ---------------------------------------------------------------------------

class PropositionLevel:
    """
    Un niveau de propositions S_k dans le graphe de planification.

    Attributs :
      propositions : frozenset of tuples  — toutes les propositions présentes
      mutex        : set of frozenset     — paires de propositions mutellement exclusives
    """

    def __init__(self, propositions, mutex=None):
        self.propositions = frozenset(propositions)
        self.mutex = set(mutex) if mutex else set()   # chaque élément est frozenset({p1, p2})

    def is_mutex(self, p1, p2):
        return frozenset({p1, p2}) in self.mutex

    def all_present(self, props):
        """Retourne True si toutes les props sont présentes dans ce niveau."""
        return all(p in self.propositions for p in props)

    def any_mutex_pair(self, props):
        """Retourne True si au moins une paire dans props est mutex."""
        props = list(props)
        for i in range(len(props)):
            for j in range(i + 1, len(props)):
                if self.is_mutex(props[i], props[j]):
                    return True
        return False

    def __repr__(self):
        return f"PropositionLevel({len(self.propositions)} props, {len(self.mutex)} mutex)"


# ---------------------------------------------------------------------------
# Niveau d'actions
# ---------------------------------------------------------------------------

class ActionLevel:
    """
    Un niveau d'actions A_k dans le graphe de planification.

    Attributs :
      actions : list of GroundAction  — toutes les actions applicables (y compris no-ops)
      mutex   : set of frozenset      — paires d'actions mutuellement exclusives
    """

    def __init__(self, actions, mutex=None):
        self.actions = list(actions)
        self.mutex = set(mutex) if mutex else set()

    def is_mutex(self, a1, a2):
        return frozenset({a1, a2}) in self.mutex

    def __repr__(self):
        return f"ActionLevel({len(self.actions)} actions, {len(self.mutex)} mutex)"


# ---------------------------------------------------------------------------
# Graphe de planification complet
# ---------------------------------------------------------------------------

class PlanningGraph:
    """
    Graphe de planification complet.

    self.prop_levels  : [PropositionLevel, ...]   indices 0, 1, 2, ...
    self.action_levels: [ActionLevel, ...]         indices 0, 1, 2, ...
      (action_levels[k] se situe entre prop_levels[k] et prop_levels[k+1])
    """

    def __init__(self, initial_state, all_ground_actions):
        self.all_ground_actions = all_ground_actions
        # S0
        s0 = PropositionLevel(initial_state, mutex=set())
        self.prop_levels = [s0]
        self.action_levels = []

    # ------------------------------------------------------------------
    # Expansion d'un niveau
    # ------------------------------------------------------------------

    def expand(self):
        """
        Étend le graphe d'un niveau :
          S_k -> A_{k+1} -> S_{k+1}
        Retourne (action_level, prop_level).
        """
        k = len(self.prop_levels) - 1
        s_k = self.prop_levels[k]

        # ---- 1. Actions applicables à S_k ----
        applicable = []
        for action in self.all_ground_actions:
            if _action_applicable(action, s_k):
                applicable.append(action)

        # ---- 2. No-ops ----
        noops = [make_noop(p) for p in s_k.propositions]
        all_actions = applicable + noops

        # ---- 3. Mutex d'actions ----
        action_mutex = _compute_action_mutex(all_actions, s_k)

        a_level = ActionLevel(all_actions, action_mutex)
        self.action_levels.append(a_level)

        # ---- 4. Propositions de S_{k+1} ----
        new_props = set()
        for action in all_actions:
            new_props.update(action.add_effects)

        # ---- 5. Mutex de propositions ----
        prop_mutex = _compute_prop_mutex(new_props, a_level)

        s_next = PropositionLevel(new_props, prop_mutex)
        self.prop_levels.append(s_next)

        return a_level, s_next

    # ------------------------------------------------------------------
    # Détection du point fixe (leveled off)
    # ------------------------------------------------------------------

    def has_leveled_off(self):
        """
        Retourne True si le dernier niveau de propositions est identique
        au précédent (mêmes propositions ET mêmes mutex).
        """
        if len(self.prop_levels) < 2:
            return False
        s_prev = self.prop_levels[-2]
        s_curr = self.prop_levels[-1]
        return (s_curr.propositions == s_prev.propositions and
                s_curr.mutex == s_prev.mutex)

    # ------------------------------------------------------------------
    # Représentation pour la trace
    # ------------------------------------------------------------------

    def depth(self):
        """Nombre de niveaux d'actions construits (= index du dernier S)."""
        return len(self.action_levels)


# ---------------------------------------------------------------------------
# Fonctions internes de calcul
# ---------------------------------------------------------------------------

def _action_applicable(action, s_k):
    """
    Une action est applicable si toutes ses préconditions sont présentes
    ET aucune paire de préconditions n'est mutex dans S_k.
    """
    for p in action.preconds:
        if p not in s_k.propositions:
            return False
    prec_list = list(action.preconds)
    for i in range(len(prec_list)):
        for j in range(i + 1, len(prec_list)):
            if s_k.is_mutex(prec_list[i], prec_list[j]):
                return False
    return True


def _compute_action_mutex(actions, s_k):
    """
    Calcule les paires d'actions mutex selon les 3 règles :
      1. Inconsistance  : effet-del de A ∩ effet-add de B ≠ ∅ (ou vice-versa)
      2. Interférence   : effet-del de A ∩ précond de B ≠ ∅ (ou vice-versa)
      3. Ressources conflictuelles : une précond de A et une précond de B sont mutex dans S_k
    """
    mutex = set()
    n = len(actions)
    for i in range(n):
        for j in range(i + 1, n):
            a, b = actions[i], actions[j]
            if _actions_are_mutex(a, b, s_k):
                mutex.add(frozenset({a, b}))
    return mutex


def _actions_are_mutex(a, b, s_k):
    # 1. Inconsistance
    if a.del_effects & b.add_effects:
        return True
    if b.del_effects & a.add_effects:
        return True
    # 2. Interférence
    if a.del_effects & b.preconds:
        return True
    if b.del_effects & a.preconds:
        return True
    # 3. Ressources conflictuelles
    for pa in a.preconds:
        for pb in b.preconds:
            if pa != pb and s_k.is_mutex(pa, pb):
                return True
    return False


def _compute_prop_mutex(props, a_level):
    """
    Calcule les paires de propositions mutex selon 2 règles :
      1. Support inconsistant : toutes les paires d'actions produisant P et Q sont mutex
      (La règle de négation directe n'existe pas en STRIPS positif pur, mais on peut
       vérifier si P et ¬P coexistent — non applicable ici car pas de négatifs.)
    """
    props = list(props)
    mutex = set()

    # Pour chaque prop, quelles actions la produisent ?
    producers = {}
    for p in props:
        producers[p] = [a for a in a_level.actions if p in a.add_effects]

    for i in range(len(props)):
        for j in range(i + 1, len(props)):
            p, q = props[i], props[j]
            pp = producers[p]
            pq = producers[q]
            if not pp or not pq:
                continue
            # Support inconsistant : TOUTES les paires sont mutex
            all_mutex = True
            for ap in pp:
                for aq in pq:
                    if ap == aq:
                        # La même action produit p et q → pas mutex
                        all_mutex = False
                        break
                    if frozenset({ap, aq}) not in a_level.mutex:
                        all_mutex = False
                        break
                if not all_mutex:
                    break
            if all_mutex:
                mutex.add(frozenset({p, q}))

    return mutex

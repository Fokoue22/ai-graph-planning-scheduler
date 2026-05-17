"""
parser.py
---------
Parseur pour les fichiers r_ops.txt et r_factX.txt du Rocket Domain.
"""  

import re


# ---------------------------------------------------------------------------
# Structures de données renvoyées par le parseur
# ---------------------------------------------------------------------------

class Operator:
    """Représente un opérateur STRIPS non instancié (template)."""

    def __init__(self, name, params, preconds, add_effects, del_effects):
        # name        : str               ex. "LOAD"
        # params      : list of (var, type)  ex. [("<object>","CARGO"), ...]
        # preconds    : list of tuple     ex. [("at","<rocket>","<place>"), ...]
        # add_effects : list of tuple
        # del_effects : list of tuple
        self.name = name
        self.params = params          # [(variable, type), ...]
        self.preconds = preconds
        self.add_effects = add_effects
        self.del_effects = del_effects

    def __repr__(self):
        return f"Operator({self.name}, params={self.params})"


class GroundAction:
    """Représente une action instanciée (grounded)."""

    def __init__(self, name, preconds, add_effects, del_effects):
        self.name = name              # str  ex. "LOAD_alex_r1_London"
        self.preconds = frozenset(preconds)
        self.add_effects = frozenset(add_effects)
        self.del_effects = frozenset(del_effects)

    def __repr__(self):
        return f"Action({self.name})"

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return isinstance(other, GroundAction) and self.name == other.name


# ---------------------------------------------------------------------------
# Tokeniseur minimal (ignore les commentaires /* ... */)
# ---------------------------------------------------------------------------

def _strip_comments(text):
    """Supprime les commentaires de style /* ... */ et // ..."""
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    text = re.sub(r'//[^\n]*', '', text)
    return text


def _tokenize(text):
    """Retourne une liste de tokens (parenthèses et mots)."""
    text = _strip_comments(text)
    tokens = re.findall(r'\(|\)|[^\s()]+', text)
    return tokens


class _TokenStream:
    """Flux de tokens avec un curseur."""

    def __init__(self, tokens):
        self._tokens = tokens
        self._pos = 0

    def peek(self):
        if self._pos < len(self._tokens):
            return self._tokens[self._pos]
        return None

    def consume(self):
        tok = self._tokens[self._pos]
        self._pos += 1
        return tok

    def expect(self, val):
        tok = self.consume()
        if tok != val:
            raise ValueError(f"Attendu '{val}', obtenu '{tok}' (pos={self._pos})")
        return tok

    def has_more(self):
        return self._pos < len(self._tokens)


# ---------------------------------------------------------------------------
# Parseur d'une liste S-expression (...)  → liste de tokens plats ou imbriqués
# ---------------------------------------------------------------------------

def _parse_sexp(stream):
    """
    Lit une S-expression à partir du flux.
    Retourne une liste récursive.
    ex. "(at <rocket> <place>)" -> ["at", "<rocket>", "<place>"]
    """
    stream.expect('(')
    result = []
    while stream.peek() != ')':
        if stream.peek() == '(':
            result.append(_parse_sexp(stream))
        else:
            result.append(stream.consume())
    stream.expect(')')
    return result


# ---------------------------------------------------------------------------
# Conversion d'une S-expression de prédicat en tuple
# ---------------------------------------------------------------------------

def _sexp_to_literal(sexp):
    """
    Convertit une S-expression de prédicat en tuple.
    ["at", "<rocket>", "<place>"] -> ("at", "<rocket>", "<place>")
    ["del", "at", "<object>", "<place>"] -> marque del séparément
    Retourne (is_delete, tuple_literal)
    """
    if not sexp:
        raise ValueError("S-expression vide")
    if sexp[0].lower() == 'del':
        return True, tuple(sexp[1:])
    return False, tuple(sexp)


# ---------------------------------------------------------------------------
# Parseur des opérateurs (r_ops.txt)
# ---------------------------------------------------------------------------

def parse_operators(filepath):
    """
    Lit un fichier r_ops.txt et retourne une liste d'Operator.
    """
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        text = f.read()

    tokens = _tokenize(text)
    stream = _TokenStream(tokens)
    operators = []

    while stream.has_more():
        if stream.peek() != '(':
            stream.consume()
            continue

        sexp = _parse_sexp(stream)
        # sexp[0] doit être "operator"
        if not sexp or sexp[0].lower() != 'operator':
            continue

        op_name = sexp[1]

        params = []
        preconds = []
        add_eff = []
        del_eff = []

        # Parcourir les sous-sections
        i = 2
        while i < len(sexp):
            section = sexp[i]
            if not isinstance(section, list):
                i += 1
                continue

            section_name = section[0].lower()

            if section_name in ('params', 'arg'):
                # chaque élément est [variable, type]
                for item in section[1:]:
                    if isinstance(item, list) and len(item) == 2:
                        params.append((item[0], item[1]))

            elif section_name in ('preconds', 'p'):
                for item in section[1:]:
                    if isinstance(item, list):
                        is_del, lit = _sexp_to_literal(item)
                        if is_del:
                            del_eff.append(lit)
                        else:
                            preconds.append(lit)

            elif section_name in ('effects', 'a'):
                for item in section[1:]:
                    if isinstance(item, list):
                        is_del, lit = _sexp_to_literal(item)
                        if is_del:
                            del_eff.append(lit)
                        else:
                            add_eff.append(lit)

            elif section_name == 'd':
                for item in section[1:]:
                    if isinstance(item, list):
                        _, lit = _sexp_to_literal(item)
                        del_eff.append(lit)

            i += 1

        operators.append(Operator(op_name, params, preconds, add_eff, del_eff))

    return operators


# ---------------------------------------------------------------------------
# Parseur des faits (r_factX.txt)
# ---------------------------------------------------------------------------

def parse_facts(filepath):
    """
    Lit un fichier r_factX.txt et retourne:
      - typed_objects : dict {type: [obj, ...]}  ex. {'PLACE':['London','Paris'], ...}
      - initial_state : frozenset of tuples       ex. {("at","r1","London"), ...}
      - goals         : frozenset of tuples
    """
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        text = f.read()

    tokens = _tokenize(text)
    stream = _TokenStream(tokens)

    typed_objects = {}   # type → list of objects
    initial_state = []
    goals = []

    while stream.has_more():
        if stream.peek() != '(':
            stream.consume()
            continue

        sexp = _parse_sexp(stream)
        if not sexp:
            continue

        first = sexp[0].lower()

        if first == 'preconds':
            for item in sexp[1:]:
                if isinstance(item, list):
                    initial_state.append(tuple(item))

        elif first == 'effects':
            for item in sexp[1:]:
                if isinstance(item, list):
                    goals.append(tuple(item))

        elif len(sexp) == 2 and isinstance(sexp[0], str) and isinstance(sexp[1], str):
            # Déclaration de type : (r1 ROCKET) ou (London PLACE)
            obj_name = sexp[0]
            obj_type = sexp[1]
            typed_objects.setdefault(obj_type, []).append(obj_name)

    return typed_objects, frozenset(initial_state), frozenset(goals)


# ---------------------------------------------------------------------------
# Grounding : instanciation des opérateurs
# ---------------------------------------------------------------------------

def ground_operators(operators, typed_objects):
    """
    Instancie tous les opérateurs avec les objets du bon type.
    Retourne une liste de GroundAction.
    """
    from itertools import product

    ground_actions = []

    for op in operators:
        # Construire les domaines pour chaque paramètre
        domains = []
        for (var, typ) in op.params:
            objs = typed_objects.get(typ, [])
            domains.append(objs)

        if not domains:
            continue

        # Générer toutes les combinaisons
        for combo in product(*domains):
            # Vérifier que les arguments sont distincts si nécessaire
            # Pour MOVE, <from> ≠ <to> (même type PLACE)
            if _has_duplicate_same_type(op.params, combo):
                continue

            # Construire le mapping variable → valeur
            binding = {var: val for (var, _), val in zip(op.params, combo)}

            # Instancier les préconditions et effets
            preconds = [_instantiate(lit, binding) for lit in op.preconds]
            add_eff  = [_instantiate(lit, binding) for lit in op.add_effects]
            del_eff  = [_instantiate(lit, binding) for lit in op.del_effects]

            # Nom de l'action instanciée
            action_name = op.name + '_' + '_'.join(combo)

            ground_actions.append(GroundAction(action_name, preconds, add_eff, del_eff))

    return ground_actions


def _has_duplicate_same_type(params, combo):
    """
    Retourne True si deux paramètres du même type ont la même valeur.
    (Pour éviter MOVE_r1_Paris_Paris)
    """
    type_to_vals = {}
    for (var, typ), val in zip(params, combo):
        type_to_vals.setdefault(typ, []).append(val)
    for typ, vals in type_to_vals.items():
        if len(vals) != len(set(vals)):
            return True
    return False


def _instantiate(literal, binding):
    """Remplace les variables d'un literal par leurs valeurs."""
    return tuple(binding.get(term, term) for term in literal)

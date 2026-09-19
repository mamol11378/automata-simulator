from collections import deque
from dataclasses import dataclass
from typing import Dict, List, Set, Tuple, FrozenSet

EPSILON = "ε"

@dataclass
class Transition:
    source: str
    symbol: str
    target: str

class FiniteAutomaton:
    def __init__(self, states=None, alphabet=None, transitions=None, start=None, finals=None):
        self.states: List[str] = list(dict.fromkeys(states or []))
        self.alphabet: List[str] = list(dict.fromkeys(alphabet or []))
        self.transitions: List[Transition] = list(transitions or [])
        self.start = start
        self.finals: Set[str] = set(finals or [])

    def add_state(self, name: str, final=False):
        name = name.strip()
        if not name:
            raise ValueError("State name cannot be empty.")
        if name not in self.states:
            self.states.append(name)
        if final:
            self.finals.add(name)
        return name

    def remove_state(self, name: str):
        self.states = [s for s in self.states if s != name]
        self.transitions = [t for t in self.transitions if t.source != name and t.target != name]
        self.finals.discard(name)
        if self.start == name:
            self.start = self.states[0] if self.states else None

    def add_transition(self, source: str, symbol: str, target: str):
        source, symbol, target = source.strip(), symbol.strip(), target.strip()
        if source not in self.states or target not in self.states:
            raise ValueError("Source and target states must exist.")
        if not symbol:
            raise ValueError("Transition symbol cannot be empty.")
        if symbol != EPSILON and symbol not in self.alphabet:
            self.alphabet.append(symbol)
        t = Transition(source, symbol, target)
        if t not in self.transitions:
            self.transitions.append(t)

    def destinations(self, source: str, symbol: str) -> Set[str]:
        return {t.target for t in self.transitions if t.source == source and t.symbol == symbol}

    def is_deterministic(self) -> bool:
        seen = set()
        for t in self.transitions:
            if t.symbol == EPSILON:
                return False
            key = (t.source, t.symbol)
            if key in seen:
                return False
            seen.add(key)
        return True

    def validate(self):
        if not self.states:
            raise ValueError("Add at least one state.")
        if self.start not in self.states:
            raise ValueError("Select a valid start state.")
        if not self.finals.issubset(set(self.states)):
            raise ValueError("Final states must exist in the state set.")
        for t in self.transitions:
            if t.source not in self.states or t.target not in self.states:
                raise ValueError("A transition references a missing state.")

    def step_dfa(self, state: str, symbol: str) -> str:
        targets = self.destinations(state, symbol)
        if len(targets) != 1:
            raise ValueError(f"DFA transition is not unique for ({state}, {symbol}).")
        return next(iter(targets))

    def simulate_dfa(self, text: str) -> Tuple[bool, List[str]]:
        self.validate()
        if not self.is_deterministic():
            raise ValueError("The current automaton is not deterministic.")
        state = self.start
        path = [state]
        for ch in text:
            if ch not in self.alphabet:
                raise ValueError(f"Symbol '{ch}' is not in the alphabet.")
            state = self.step_dfa(state, ch)
            path.append(state)
        return state in self.finals, path

    def epsilon_closure(self, states: Set[str]) -> Set[str]:
        closure = set(states)
        stack = list(states)
        while stack:
            current = stack.pop()
            for target in self.destinations(current, EPSILON):
                if target not in closure:
                    closure.add(target)
                    stack.append(target)
        return closure

    def move(self, states: Set[str], symbol: str) -> Set[str]:
        return {t.target for t in self.transitions if t.source in states and t.symbol == symbol}

    def simulate_nfa(self, text: str) -> Tuple[bool, List[Set[str]]]:
        self.validate()
        current = self.epsilon_closure({self.start})
        path = [set(current)]
        for ch in text:
            if ch not in self.alphabet:
                raise ValueError(f"Symbol '{ch}' is not in the alphabet.")
            current = self.epsilon_closure(self.move(current, ch))
            path.append(set(current))
        return bool(current & self.finals), path

    def to_dfa(self):
        self.validate()
        if self.is_deterministic():
            return self
        alphabet = list(self.alphabet)
        start_set = frozenset(self.epsilon_closure({self.start}))
        names = {start_set: self._subset_name(start_set)}
        queue = deque([start_set])
        dfa_states = [names[start_set]]
        dfa_transitions = []
        dfa_finals = set()

        while queue:
            subset = queue.popleft()
            name = names[subset]
            if set(subset) & self.finals:
                dfa_finals.add(name)
            for symbol in alphabet:
                target = frozenset(self.epsilon_closure(self.move(set(subset), symbol)))
                if not target:
                    continue
                if target not in names:
                    names[target] = self._subset_name(target)
                    dfa_states.append(names[target])
                    queue.append(target)
                dfa_transitions.append(Transition(name, symbol, names[target]))

        return FiniteAutomaton(
            states=dfa_states,
            alphabet=alphabet,
            transitions=dfa_transitions,
            start=names[start_set],
            finals=dfa_finals,
        )

    @staticmethod
    def _subset_name(subset: FrozenSet[str]) -> str:
        if not subset:
            return "∅"
        return "{" + ",".join(sorted(subset)) + "}"

    def clone(self):
        return FiniteAutomaton(
            self.states[:], self.alphabet[:],
            [Transition(t.source, t.symbol, t.target) for t in self.transitions],
            self.start, set(self.finals)
        )

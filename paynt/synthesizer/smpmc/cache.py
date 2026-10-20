"""Memo for ColoredMdpTheory.check() results -- Algorithm 1's per-literal conflict cache (arXiv:2511.08078).

Subsumption rules (from the monotonicity of choice removal: fixing more parameters can only narrow the induced sub-MDP's choices, which can only lower Vmax
and raise Vmin):
  - a REFUTED entry for polarity p, keyed by a *subset* of the current query, refutes the query too: "every completion fails" only gets stronger as more
    parameters are pinned down.
  - an INCONCLUSIVE entry for polarity p, keyed by a *superset* of the current query, makes the query inconclusive too: if a more constrained region was not
    refuted, a less constrained one, whose completions are a superset of its completions, cannot be either.
  - a REFUTED entry for the *opposite* polarity (1-p), whether a subset or a superset of the query, can only be used to conclude "inconclusive" for polarity p,
    never a refutation, so both directions are safe to check.

The cache is epoch-aware: tightening the optimality threshold (a new epoch) can invalidate verdicts. A refuted `viable` ("no completion meets the threshold")
stays valid under a tighter threshold, but a refuted `not viable` ("every completion meets it") need not, and neither need an inconclusive verdict; those tries
are replaced with empty ones whenever the epoch advances, which is cheaper than per-entry filtering. (Refuted `not viable` literals only arise under a
quantifier, so plain existential optimality never has any to drop.)

The tries are payntbind's own (payntbind.synthesis.SetTrie). Its sets are lists of integers, so a (parameter, option) pair is the integer `(parameter << 32) |
option` (see _element). Its payloads are integers too: a refutation's payload (its Refutation) lives in a dict under a unique integer id, so removing one
entry never removes another.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Any, Final

import payntbind.synthesis


class _Miss(enum.Enum):
    MISS = enum.auto()


# a single-member enum rather than object(), so that `is MISS` narrows lookup()'s result for mypy
MISS: Final = _Miss.MISS


@dataclass(frozen=True)
class Refutation:
    """A cached refutation: the minimized conflict, and the value that refuted it.

    If exact (computed on a full assignment), every member of the conflict's region has that value: the parameters dropped by the minimization do not affect the
    reachable Markov chain. Otherwise it bounds the values of the region's members.
    """

    conflict_parameters: list[int]
    value: Any = None
    exact: bool = False


def _element(parameter: int, option: int) -> int:
    """The element of a set trie that stands for "parameter is fixed to option"."""
    return (parameter << 32) | option


def _key(fixed: dict[int, int]) -> list[int]:
    """The set of the pairs of the partial assignment fixed, as a list of the elements of a set trie."""
    return [_element(parameter, option) for parameter, option in fixed.items()]


class PartialModelCache:
    """Caches ColoredMdpTheory.check(fixed, polarity) verdicts, with subset/superset subsumption so a single refutation (or inconclusive verdict) can answer
    many future queries without another Storm call.

    See module docstring for the subsumption rules and the epoch-driven reset.
    """

    def __init__(self) -> None:
        # index 0 -> polarity False, index 1 -> polarity True
        self._refuted: list[payntbind.synthesis.SetTrie] = [payntbind.synthesis.SetTrie(), payntbind.synthesis.SetTrie()]
        # per polarity: trie set id -> its refutation
        self._refutations: list[dict[int, Refutation]] = [{}, {}]
        self._next_id = 0
        self._inconclusive: list[payntbind.synthesis.SetTrie] = [payntbind.synthesis.SetTrie(), payntbind.synthesis.SetTrie()]
        self._epoch = 0

    def _sync_epoch(self, epoch: int) -> None:
        if epoch != self._epoch:
            # a tighter threshold: refuted not-viable literals and inconclusive verdicts may no longer hold, see the module docstring
            self._refuted[0] = payntbind.synthesis.SetTrie()
            self._refutations[0] = {}
            self._inconclusive = [payntbind.synthesis.SetTrie(), payntbind.synthesis.SetTrie()]
            self._epoch = epoch

    def lookup(self, fixed: dict[int, int], polarity: bool, epoch: int) -> list[Refutation] | None | _Miss:
        """:returns: every cached refutation of this polarity whose conflict fixed agrees with (each one refutes the query), None on a still-valid cached (or
        subsumed) inconclusive verdict, or the MISS sentinel if nothing usable is cached."""
        self._sync_epoch(epoch)
        key = _key(fixed)
        p = int(polarity)

        refutations = [self._refutations[p][entry] for entry in self._refuted[p].subsets(key)]
        if refutations:
            return refutations

        # has_superset and not any(supersets(...)): the first set stored in a trie has the payload 0, which is falsy
        if self._inconclusive[p].has_superset(key):
            return None

        # cross-polarity: a subset or superset already refuted for the *opposite* polarity means that this region is entirely one thing or the other, which can
        # only make the current polarity's literal inconclusive, never refuted
        other = 1 - p
        if self._refuted[other].has_subset(key) or self._refuted[other].has_superset(key):
            return None

        return MISS

    def insert_refuted(self, fixed: dict[int, int], polarity: bool, conflict_parameters: list[int], epoch: int, value: Any = None, exact: bool = False) -> None:
        """:param value: the value that refuted the literal, see Refutation
        :param exact: whether value was computed on a full assignment, see Refutation"""
        self._sync_epoch(epoch)
        key = [_element(parameter, fixed[parameter]) for parameter in conflict_parameters]
        p = int(polarity)
        # this new (already minimized) conflict subsumes every cached entry that is a superset of it: whatever the larger entry could answer, this one answers
        # too, so drop the redundant entries to keep the trie lean. The dropped entry's value may have bounded its smaller region more tightly; the new one
        # still bounds it.
        for stale in self._refuted[p].supersets(key):
            self._refuted[p].remove(stale)
            del self._refutations[p][stale]
        entry = self._next_id
        self._next_id += 1
        self._refuted[p].insert(key, entry)
        self._refutations[p][entry] = Refutation(sorted(conflict_parameters), value, exact)

    def insert_inconclusive(self, fixed: dict[int, int], polarity: bool, epoch: int) -> None:
        self._sync_epoch(epoch)
        key = _key(fixed)
        p = int(polarity)
        if not self._inconclusive[p].contains(key):
            self._inconclusive[p].insert(key, len(self._inconclusive[p]))

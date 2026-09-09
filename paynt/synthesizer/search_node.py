'''
Search-time bookkeeping for AR/CEGIS/Hybrid/policy-tree synthesis, kept separate from ParameterSpace
(paynt.parameter_space.parameter_space.ParameterSpace), which represents only the parameter-domain value
(V of the colored MDP C = (M, V, kappa)) and carries no notion of "where in the search this came from".
'''

from __future__ import annotations

from typing import Any

import paynt.parameter_space.parameter_space
import paynt.parameter_space.smt
import paynt.specification.property_result
import paynt.underlying_model.underlying_model

import logging
logger = logging.getLogger(__name__)


class ParentInfo():
    '''
    Snapshot of a parent SearchNode's state, handed to each child produced by splitting it. A snapshot
    rather than a live reference to the parent node itself: a parent is never reconsidered once split, so
    keeping only what a child actually needs (rather than the parent's full state, including its built MDP)
    keeps memory bounded on a deep search.
    '''
    def __init__(self):
        self.selected_choices : Any = None
        self.constraint_indices : list[int] | None = None
        self.refinement_depth : int | None = None
        # set only by dt.synthesizer.SynthesizerARDt.split_undecided_space; None for every other caller and
        # for a multi-property DT specification
        self.analysis_result : paynt.specification.property_result.SpecificationResult | None = None
        self.scheduler_choices : Any = None


class SearchNode:
    '''
    The current state of exploring one parameter (sub)space: which parameter_space it covers, the MDP induced
    by building that parameter_space against a ColoredMdp, and the outcome of checking the specification
    against it. Constructed fresh for the search root and for every child produced by splitting; never copied
    from a parent to a child wholesale (see ParentInfo above for the one deliberate handoff mechanism).
    '''
    def __init__(self, parameter_space : paynt.parameter_space.parameter_space.ParameterSpace, parent_info : ParentInfo | None = None):
        self.parameter_space = parameter_space
        self.parent_info = parent_info
        if parent_info is None:
            self.refinement_depth = 0
        else:
            assert parent_info.refinement_depth is not None
            self.refinement_depth = parent_info.refinement_depth + 1
        self.constraint_indices : list[int] | None = parent_info.constraint_indices if parent_info is not None else None

        # populated by ColoredMdp.build(self.parameter_space, ...)
        self.selected_choices : Any = None
        self.mdp : paynt.underlying_model.underlying_model.Mdp | None = None
        # populated by Synthesizer.check_specification / SynthesizerARDt.verify_parameter_space
        self.analysis_result : paynt.specification.property_result.SpecificationResult | None = None
        # lazily populated by SearchNode.encode, CEGIS/Hybrid only
        self.encoding : paynt.parameter_space.smt.ParameterSpaceEncoding | None = None

    def collect_parent_info(self) -> ParentInfo:
        ''' Snapshot this node's state for handoff to the children it is about to be split into. '''
        pi = ParentInfo()
        pi.selected_choices = self.selected_choices
        pi.refinement_depth = self.refinement_depth
        assert self.analysis_result is not None
        cr = self.analysis_result.constraints_result
        pi.constraint_indices = cr.undecided_constraints if cr is not None else []
        return pi

    def split(self, splitter : int, suboptions : list[list[int]]) -> list["SearchNode"]:
        '''
        Split self.parameter_space into subspaces and wrap each as a fresh child node of the same concrete
        type as self (so DtSearchNode/PolicyTreeNode children are produced automatically), carrying this
        node's snapshotted state via ParentInfo.
        '''
        parent_info = self.collect_parent_info()
        parameter_subspaces = self.parameter_space.split(splitter, suboptions)
        return [type(self)(parameter_subspace, parent_info) for parameter_subspace in parameter_subspaces]

    def encode(self, smt_solver : paynt.parameter_space.smt.SmtSolver) -> None:
        if self.encoding is None:
            self.encoding = paynt.parameter_space.smt.ParameterSpaceEncoding(smt_solver, self.parameter_space)

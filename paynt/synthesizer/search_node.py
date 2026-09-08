'''
Search-time bookkeeping for AR/CEGIS/Hybrid/policy-tree synthesis, kept separate from ParameterSpace
(paynt.parameter_space.parameter_space.ParameterSpace), which represents only the parameter-domain value
(V of the colored MDP C = (M, V, kappa)) and carries no notion of "where in the search this came from".
'''

import paynt.parameter_space.smt

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
        self.selected_choices = None
        self.constraint_indices = None
        self.refinement_depth = None
        # set only by dt.synthesizer.SynthesizerARDt.split_undecided_space; None for every other caller and
        # for a multi-property DT specification
        self.analysis_result = None
        self.scheduler_choices = None


class SearchNode:
    '''
    The current state of exploring one parameter (sub)space: which parameter_space it covers, the MDP induced
    by building that parameter_space against a ColoredMdp, and the outcome of checking the specification
    against it. Constructed fresh for the search root and for every child produced by splitting; never copied
    from a parent to a child wholesale (see ParentInfo above for the one deliberate handoff mechanism).
    '''
    def __init__(self, parameter_space, parent_info=None):
        self.parameter_space = parameter_space
        self.parent_info = parent_info
        self.refinement_depth = 0 if parent_info is None else parent_info.refinement_depth + 1
        self.constraint_indices = parent_info.constraint_indices if parent_info is not None else None

        # populated by ColoredMdp.build(self.parameter_space, ...)
        self.selected_choices = None
        self.mdp = None
        # populated by Synthesizer.check_specification / SynthesizerARDt.verify_parameter_space
        self.analysis_result = None
        # lazily populated by SearchNode.encode, CEGIS/Hybrid only
        self.encoding = None

    def collect_parent_info(self):
        ''' Snapshot this node's state for handoff to the children it is about to be split into. '''
        pi = ParentInfo()
        pi.selected_choices = self.selected_choices
        pi.refinement_depth = self.refinement_depth
        cr = self.analysis_result.constraints_result
        pi.constraint_indices = cr.undecided_constraints if cr is not None else []
        return pi

    def split(self, splitter, suboptions):
        '''
        Split self.parameter_space into subspaces and wrap each as a fresh child node of the same concrete
        type as self (so DtSearchNode/PolicyTreeNode children are produced automatically), carrying this
        node's snapshotted state via ParentInfo.
        '''
        parent_info = self.collect_parent_info()
        parameter_subspaces = self.parameter_space.split(splitter, suboptions)
        return [type(self)(parameter_subspace, parent_info) for parameter_subspace in parameter_subspaces]

    def encode(self, smt_solver):
        if self.encoding is None:
            self.encoding = paynt.parameter_space.smt.ParameterSpaceEncoding(smt_solver, self.parameter_space)

import xml.etree.ElementTree as ET

import logging
logger = logging.getLogger(__name__)


# class for POMDP policy represented as a set of alpha vectors
# alpha_vectors property is a list of list of floats, where each inner list has a length equal to number of states in a POMDP
# alpha_vector_actions is a list of ints, where the values in the list represent the chosen action
class AlphaVectorSet:

    def __init__(self, alpha_vectors, alpha_vector_actions):
        self.alpha_vectors = alpha_vectors
        self.alpha_vector_actions = alpha_vector_actions
        assert len(self.alpha_vectors) == len(self.alpha_vector_actions), "alpha vector count and the number of their corresponding actions should match"

        
# currently supporting only the output of SARSOP C++ implementation, we can extend this to support the Julia POMDP format in the future
class AlphaVectorParser:

    def __init__(self):
        pass

    @classmethod
    def parse_sarsop_xml(self, filename):
        logger.info("parsing alpha vectors from SARSOP XML format")
        tree = ET.parse(filename)
        root = tree.getroot()

        alpha_vector_policy = root[0]
        vector_length = int(alpha_vector_policy.attrib['vectorLength'])

        alpha_vectors = []
        alpha_vector_actions = []

        for alpha_vector in alpha_vector_policy:
            parsed_vector = [float(x) for x in alpha_vector.text.split(' ')[:-1]]
            assert vector_length == len(parsed_vector), "the length of the vector differs from the expected length"
            parsed_action = int(alpha_vector.attrib['action'])
            alpha_vectors.append(parsed_vector)
            alpha_vector_actions.append(parsed_action)

        return AlphaVectorSet(alpha_vectors, alpha_vector_actions)



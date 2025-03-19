class Variable:

    def __init__(self, name, domain):
        self.name = name
        self.domain = domain

    @classmethod
    def create_variable(cls, variable, name, domain):
        # LADA TODO: delete or explain why
        # domain = set()
        #for state,valuation in enumerate(state_valuations):
        #    value = valuation[variable]
        #    domain.add(value)
        #domain = list(domain)
        # conversion of boolean variables to integers
        domain_new = []
        for value in domain:
            if value is True:
                value = 1
            elif value is False:
                value = 0
            domain_new.append(value)
        domain = domain_new
        domain = sorted(domain)
        return cls(name,domain)

    @property
    def domain_min(self):
        return self.domain[0]

    @property
    def domain_max(self):
        return self.domain[-1]

    @property
    def hole_domain(self):
        '''
        Hole domain does not include the maximum value.
        '''
        return self.domain[:-1]

    def __str__(self):
        # domain = "bool" if self.has_boolean_type else f"[{self.domain_min}..{self.domain_max}]"
        domain = f"[{self.domain_min}..{self.domain_max}]"
        return f"{self.name}:{domain}"

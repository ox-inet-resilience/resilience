from economicsl.contract import Contract


class Bond(Contract):
    ctype = 'Bond'

    def __init__(self, assetParty, liabilityParty, maturityType, principal, rate):
        super().__init__(assetParty, liabilityParty)
        self.maturityType = maturityType
        self.principal = principal
        self.rate = rate

    def start(self):
        self.assetParty.append(self)
        self.liabilityParty.append(self)

    def get_name(self):
        return "Bond. NOT IMPLEMENTED WHY ARE YOU USING ME???"

    def get_action(self, me):
        # TODO
        if self.assetParty == me:
            # SellBond()
            return None
        elif self.liabilityParty == me:
            # If the bond is my liability, I cannot do anything (?)
            return None

    def is_eligible(self, me):
        # TODO
        # if this bond is encumbered, or if agent is not a party, none.
        # if this is a Gvt bond, an interbank bond or a non-me bond, the agent gets a SellBond action with the correct parameters
        return False

    def get_valuation(self, side):
        return self.principal

    def get_maturity_type(self):
        return self.maturityType

    def set_maturity_type(self, maturityType):
        self.maturityType = maturityType

    def set_principal(self, principal):
        self.principal = principal

    def get_rate(self):
        return self.rate

    def set_rate(self, rate):
        self.rate = rate

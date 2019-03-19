from economicsl import Contract


class LongTermUnsecured(Contract):
    ctype = 'LTU'

    def __init__(self, liabilityParty, amount):
        super().__init__(None, liabilityParty)
        self.amount = amount
        self.liabilityParty = liabilityParty
        self._lcr = liabilityParty.model.parameters.LONG_TERM_LCR

    def get_LCR_weight(self):
        return self._lcr

    def get_name(self, me):
        return "Long term unsecured liabilities"

    def get_value(self):
        return self.amount

from economicsl import Contract


class EquityHolding(Contract):
    __slots__ = 'me', 'holdings'
    ctype = 'EquityHolding'

    def __init__(self, me):
        super().__init__(me, None)
        self.me = me
        self.holdings = set()

    def get_name(self, me):
        return "Equity holdings of " + me.get_name()

    def get_value(self):
        return sum(b.CET1E_holders[self.me] * b.cached_CET1E for b in self.holdings)

    def add_holding(self, b):
        self.holdings.add(b)

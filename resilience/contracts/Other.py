from economicsl import Contract
from ..actions import PayLoan


class Other(Contract):
    __slots__ = 'parameters', 'principal', '_payloan'
    ctype = 'Other'

    # TODO: See the TODO in the definition of Deposit
    def __init__(self, assetParty, liabilityParty, amount):
        super().__init__(assetParty, liabilityParty)
        _model = (assetParty or liabilityParty).model
        self.parameters = _model.parameters
        self.principal = amount
        self._payloan = PayLoan(liabilityParty, self)

    def get_LCR_weight(self):
        return self.parameters.OTHER_LCR

    def get_name(self, me):
        return "Other"

    def get_value(self):
        return self.principal

    def set_amount(self, amount):
        self.principal = amount

    def is_eligible(self, me):
        # Only Other Liability has action
        return (self.assetParty is None) and self.get_value() > 0

    def get_action(self, me):
        return self._payloan

    def get_funding_already_pulled(self):
        return 0.0

    def reduce_principal(self, amount):
        value = self.get_value()
        self.set_amount(value - amount)

    def pay_loan(self, amount):
        # update the amount required to be paid because it could have decreased due to bail-in
        value = self.get_value()
        amount = min(amount, value)
        self.liabilityParty.pay_liability(amount, self)
        self.liabilityParty.get_ledger().subtract_cash(amount)
        self.reduce_principal(amount)

    def liquidate(self):
        self.fundingAlreadyPulled = 0
        self.principal = 0.0

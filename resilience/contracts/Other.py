from economicsl.contract import Contract
from ..actions import PayLoan


class Other(Contract):
    __slots__ = 'principal', '_payloan', 'fundingAlreadyPulled', 'lcr_weight'
    ctype = 'Other'

    # TODO: See the TODO in the definition of Deposit
    def __init__(self, assetParty, liabilityParty, amount):
        super().__init__(assetParty, liabilityParty)
        _model = (assetParty or liabilityParty).model
        self.principal = amount
        self._payloan = PayLoan(liabilityParty, self)
        self.fundingAlreadyPulled = 0.0
        self.lcr_weight = _model.parameters.OTHER_LCR

    def get_LCR_weight(self):
        return self.lcr_weight

    def get_name(self):
        return "Other"

    def get_notional(self):
        return self.principal

    def get_valuation(self, side):
        return self.get_notional()

    def set_amount(self, amount):
        self.principal = amount

    def is_eligible(self, me):
        # Only Other Liability has action
        return (self.assetParty is None) and self.get_notional() > 0

    def get_action(self, me):
        return self._payloan

    def get_funding_already_pulled(self):
        return 0.0

    def reduce_principal(self, amount):
        notional = self.get_notional()
        self.set_amount(notional - amount)

    def pay_loan(self, amount):
        # update the amount required to be paid because it could have decreased due to bail-in
        notional = self.get_notional()
        amount = min(amount, notional)
        self.liabilityParty.pay_liability(amount, self)
        self.liabilityParty.get_ledger().subtract_cash(amount)
        self.reduce_principal(amount)

    def liquidate(self):
        self.fundingAlreadyPulled = 0
        self.principal = 0.0

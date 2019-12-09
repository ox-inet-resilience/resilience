from economicsl import Action


# the Payloan action represents the chance to pay back a loan that the agent has on its liability side.
class PayLoan(Action):
    __slots__ = 'loan', 'parameters'

    def __init__(self, me, loan):
        super().__init__(me)
        self.loan = loan
        self.parameters = (loan.assetParty or loan.liabilityParty).model.parameters

    def get_loan(self):
        return self.loan

    def perform(self):
        super().perform()
        if not self.parameters.FUNDING_CONTAGION_INTERBANK:
            # TODO accounting is not done here
            amount = self.get_amount()
            if self.loan.assetParty:
                self.loan.assetParty.add_cash(amount)
            self.loan.liabilityParty.get_ledger().subtract_cash(amount)
            self.loan.reduce_principal(amount)
            return
        self.loan.pay_loan(self.get_amount())

    def get_max(self):
        # Truncate max to be always positive because
        # sometimes it is a negative infinitesimal number.
        return max(0, self.loan.get_notional() - self.loan.get_funding_already_pulled())

    def print(self):
        print(f"Pay Loan action by {self.loan.get_liability_party().get_name()} -> amount: {self.get_amount()}")

    def get_name(self):
        asset_party = self.loan.get_asset_party()
        ap_name = 'unspecified lender' if asset_party is None else asset_party.get_name()
        return f"Pay Loan to {ap_name} [max: {self.get_max()}]"

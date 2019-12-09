from economicsl import Action
from ..contracts.obligations import PullFundingObgn


class PullFunding(Action):
    __slots__ = 'loan', 'parameters'

    def __init__(self, me, loan):
        super().__init__(me)
        self.loan = loan
        self.parameters = (loan.assetParty or loan.liabilityParty).model.parameters

    def get_loan(self):
        return self.loan

    def perform(self):
        super().perform()
        amount = self.get_amount()

        if self.loan.get_liability_party() is None:
            # If there's no counter-party the payment can happen instantaneously
            self.loan.pay_loan(amount)
            return

        if not self.parameters.FUNDING_CONTAGION_INTERBANK:
            # TODO accounting is not done here
            self.loan.assetParty.get_ledger().add_cash(amount)
            # assume bailin is always off
            self.loan.liabilityParty.add(type(self.loan)(None, self.loan.liabilityParty, amount))
            self.loan.reduce_principal(amount)
        else:
            self.loan.increase_funding_pulled(amount)
            # If there is a counter-party AND we have funding contagion, we must send a Obligation.
            ttp = self.parameters.TIMESTEPS_TO_PAY
            obligation = PullFundingObgn(self.loan, amount, ttp)
            self.loan.get_asset_party().send_obligation(self.loan.get_liability_party(), obligation)

    def get_max(self):
        # Truncate max to be always positive because
        # sometimes it is a negative infinitesimal number.
        return max(0, self.loan.get_notional() - self.loan.get_funding_already_pulled())

    def print(self):
        print(f"Pull Funding action by {self.loan.get_asset_party().get_name()}"
              f" -> amount {self.get_amount()}"
              f", borrower is {self.loan.get_liability_party().get_name()}")

    def get_name(self):
        return f"Pull Funding from {self.loan.get_liability_party().get_name()} [max: {self.get_max()}]"

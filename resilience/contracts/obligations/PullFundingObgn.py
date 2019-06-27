import logging

from economicsl import Obligation


class PullFundingObgn(Obligation):
    __slots__ = ['loan']

    def __init__(self, loan, amount, timeLeftToPay):
        super().__init__(loan, amount, timeLeftToPay)
        self.loan = loan

    def fulfil(self):
        self.loan.pay_loan(self.amount)
        logging.debug(self.loan.get_liability_party().get_name() + " has fulfilled an obligation to pay " +
                      self.loan.get_asset_party().get_name() +
                      " an amount %.2f." % self.amount)

        self.loan.reduce_funding_pulled(self.amount)
        self.set_fulfilled()

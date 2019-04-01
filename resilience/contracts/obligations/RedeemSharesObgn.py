import logging

from economicsl import Obligation


class RedeemSharesObgn(Obligation):
    __slots__ = ('shares', 'nSharesToRedeem')

    def __init__(self, shares, numberOfShares, timeToPay):
        super().__init__(shares, numberOfShares * shares.get_NAV(), timeToPay)
        self.shares = shares
        self.nSharesToRedeem = numberOfShares

    def get_amount(self):
        return self.nSharesToRedeem * self.shares.get_NAV()

    def fulfil(self):
        self.shares.redeem(self.nSharesToRedeem)
        logging.debug(
            self.shares.get_liability_party().get_name()+ " has fulfilled an obligation to redeem shares and pay " +
            self.shares.get_asset_party().get_name() +
            " an amount %.2f." % self.amount)
        self.set_fulfilled()

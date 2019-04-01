from ..contracts.obligations import RedeemSharesObgn

from economicsl import Action


class RedeemShares(Action):
    __slots__ = 'shares', '_ttrs'

    def __init__(self, me, shares):
        super().__init__(me)
        self.shares = shares
        self._ttrs = me.model.parameters.TIMESTEPS_TO_REDEEM_SHARES

    def perform(self):
        super().perform()
        self.shares.add_shares_pending_to_redeem(self.get_amount())
        obligation = RedeemSharesObgn(self.shares, self.get_amount(),
                                     self.get_time() + self._ttrs)
        self.shares.get_asset_party().send_obligation(self.shares.get_liability_party(), obligation)

    def get_max(self):
        return self.shares.get_nShares() - self.shares.get_nShares_pending_to_redeem()

    def print(self):
        print(f"Redeem Shares action by {self.shares.get_asset_party().get_name()} -> number: ",
              "%.2f" % self.get_amount(),
              f", issues is {self.shares.get_liability_party().get_name()}")

    def get_name(self):
        return f"Redeem Shares from {self.shares.get_liability_party().get_name()} [max: {self.get_max()}]"

    def get_shares(self):
        return self.shares

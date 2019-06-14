import logging

from ..actions import RedeemShares
from economicsl.contract import Contract


# This contract represents a bunch of shares of some Institution which can issue shares.
class Shares(Contract):
    ctype = 'Shares'

    def __init__(self, owner, issuer, nShares, originalNAV):
        super().__init__(owner, issuer)
        self.nShares = nShares
        self.originalNumberOfShares = nShares
        self.previousValueOfShares = self.get_new_valuation()
        self.originalNAV = originalNAV
        self.nSharesPendingToRedeem = 0

        assert issuer is not None

    def get_name(self):
        ass = self.assetParty.get_name()
        lia = self.liabilityParty.get_name()
        return f"Shares of the firm: {lia} owned by shareholder {ass}"

    def redeem(self, number, amount):
        assert number <= self.nShares
        self.liabilityParty.get_ledger().subtract_cash(amount)
        # TODO this is disabled because AM investor is disabled for now
        # self.assetParty.get_ledger().sell_asset(number * nav, self)
        self.nShares -= number
        self.nSharesPendingToRedeem -= number

    def get_valuation(self, side):
        return self.previousValueOfShares

    def get_new_valuation(self):
        return self.nShares * self.liabilityParty.get_net_asset_valuation()

    def get_NAV(self):
        return self.liabilityParty.get_net_asset_valuation()

    def get_nShares(self):
        return self.nShares

    def get_action(self, me):
        return RedeemShares(me, self)

    def is_eligible(self, me):
        return (me == self.assetParty) and self.nShares > 0

    def update_valuation(self):
        valueChange = self.get_new_valuation() - self.previousValueOfShares
        self.previousValueOfShares = self.get_new_valuation()
        return

        # accounting disabled because AM Investor is disabled
        if valueChange > 0:
            self.assetParty.get_ledger().appreciate_asset(self, valueChange)
            self.liabilityParty.get_ledger().appreciate_liability(self, valueChange)
        elif valueChange < 0:
            logging.debug("value of shares fell.")
            self.assetParty.get_ledger().devalue_asset(self, -1.0 * valueChange)
            self.liabilityParty.get_ledger().devalue_liability(self, -1.0 * valueChange)

    def get_original_NAV(self):
        return self.originalNAV

    def add_shares_pending_to_redeem(self, number):
        self.nSharesPendingToRedeem += number

    def get_nShares_pending_to_redeem(self):
        return self.nSharesPendingToRedeem

    def get_original_number_of_shares(self):
        return self.originalNumberOfShares

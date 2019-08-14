from .FailedMarginCallException import FailedMarginCallException
from .Loan import Loan

from ..parameters import eps


# A Repo is a securitized Loan, i.e. it includes collateral. Collateral is stored as hashmap of CanBeCollateral contracts
# and quantities of each. The Repo can value its collateral by valuing each contract in the Collateral hashmap, and
# weighting each by its haircut.
#
#
# @author rafa
class Repo(Loan):
    __slots__ = (
        'collateral', 'cash_collateral', 'prev_margin_call', 'future_margin_call', 'future_max_collateral',
        'MARGIN_CALL_ON', 'POSTDEFAULT_FIRESALE_CONTAGION', 'parameters'
    )
    ctype = 'Repo'

    def __init__(self, assetParty, liabilityParty, principal):
        super().__init__(assetParty, liabilityParty, principal)
        self.collateral = {}
        self.cash_collateral = 0.0
        self.prev_margin_call = 0.0
        self.future_margin_call = 0.0
        self.future_max_collateral = 0.0
        _model = (assetParty or liabilityParty).model
        self.parameters = _model.parameters
        # These method are used for checking MARGIN_CALL_ON and
        # POSTDEFAULT_FIRESALE_CONTAGION
        self.MARGIN_CALL_ON = _model.parameters.MARGIN_CALL_ON
        self.POSTDEFAULT_FIRESALE_CONTAGION = _model.parameters.POSTDEFAULT_FIRESALE_CONTAGION

    def get_LCR_weight(self):
        return self.parameters.REPO_LCR

    def get_name(self):
        _from = self.assetParty.get_name() if self.assetParty is not None else "uninitialised Institution"
        _to = self.liabilityParty.get_name() if self.liabilityParty is not None else "uninitialised Institution"
        return f"Repo from {_from} to {_to}"

    def pledge_collateral(self, asset, quantity):
        asset.encumber(quantity)
        self.collateral[asset] += quantity

    def pledge_cash_collateral(self, amount):
        amount_encumbered = self.liabilityParty.encumber_cash(amount)
        self.cash_collateral += amount_encumbered
        return amount_encumbered

    def unpledge_cash_collateral(self, amount):
        _amount = min(amount, self.cash_collateral)
        self.cash_collateral -= _amount
        self.liabilityParty.unencumber_cash(_amount)
        return _amount

    def unpledge_collateral(self, asset, amount):
        _amount = min(self.collateral.get(asset), amount)
        asset.unEncumber(_amount)
        self.collateral[asset] -= _amount

    def get_max_ue_haircutted_collateral(self):
        return sum(c.get_haircutted_ue_valuation() for c in self.collateral.keys())

    def get_mc_size(self):
        current_haircutted_collateral = self.get_haircutted_collateral_valuation()
        return self.principal - current_haircutted_collateral

    def fulfil_margin_call(self):
        """
        equation 39
        """
        if not self.MARGIN_CALL_ON:
            return
        borrower = self.liabilityParty
        if borrower is not None and borrower.isaBank:
            # Do not run margin call if borrower is a bank
            # see https://resilience.zulipchat.com/#narrow/stream/122180-SimulationsOrganised/subject/FF2/near/135901302
            return

        _max_collateral = self.get_max_ue_haircutted_collateral() + borrower.get_ue_cash()

        if self.prev_margin_call > 0:
            # The borrower is short of collateral for an amount of self.prev_margin_call
            if self.prev_margin_call > _max_collateral:
                self.prev_margin_call = _max_collateral
                # The margin call on this repo failed. However, pledge collateral as much as possible
                self.pledge_proportionally(self.prev_margin_call)
                raise FailedMarginCallException("Failed Margin Call")
            else:
                # We can put in the necessary collateral -> Margin call succeeds
                self.pledge_proportionally(self.prev_margin_call)

        current_margin_call = self.get_mc_size()
        if current_margin_call < 0:
            # The borrower needs to return collateral by an amount of -current_margin_call
            self.unpledge_proportionally(-current_margin_call)

        # update current_margin_call
        current_margin_call = self.get_mc_size()

        # These 2 variables are to be used on step 1b of SPDA, i.e. preparing to meet margin call of the next day
        self.future_margin_call = current_margin_call
        self.future_max_collateral = self.get_max_ue_haircutted_collateral() + borrower.get_ue_cash()

        # Update the stored margin call size to be the current one for the subsequent margin call
        self.prev_margin_call = current_margin_call

    def prepare_future_margin_call(self):
        if (self.future_margin_call > 0) and (self.future_margin_call > self.future_max_collateral):
            # Now, prepare to firesell the amount needed
            # if the available extra collateral is not sufficient
            # to meet the subsequent margin call
            amount2firesell = self.future_margin_call - self.future_max_collateral
            self.liabilityParty.sell_assets_proportionally(amount2firesell)

    def get_haircutted_collateral_valuation(self):
        return sum(a.get_price() * quantity * (1.0 - a.get_haircut())
                   for (a, quantity) in self.collateral.items()) + self.cash_collateral

    def get_collateral(self):
        return self.collateral

    def pledge_proportionally(self, total):
        maxHaircutValue = self.get_max_ue_haircutted_collateral()
        assert maxHaircutValue >= -eps, maxHaircutValue
        pledged = 0
        if maxHaircutValue > 0:
            _total_noncash = min(total, maxHaircutValue)
            _factor = _total_noncash / maxHaircutValue
            for asset in self.collateral.keys():
                quantity_to_pledge = asset.get_unencumbered_quantity() * _factor
                self.pledge_collateral(asset, quantity_to_pledge)
                pledged += quantity_to_pledge * asset.get_price() * (1 - asset.get_haircut())

        remainder = total - pledged
        if remainder > 0:
            # resort to encumber cash
            self.pledge_cash_collateral(remainder)

    def unpledge_proportionally(self, excess):
        cash_unpledged = self.unpledge_cash_collateral(excess)
        remainder = excess - cash_unpledged
        if remainder <= eps:
            return

        initial_collateral = self.get_haircutted_collateral_valuation()
        if initial_collateral > 0:
            _factor = remainder / initial_collateral

            for a, quantity in self.collateral.items():
                quantityToUnpledge = quantity * _factor
                self.unpledge_collateral(a, quantityToUnpledge)

    def liquidate(self):
        # When we liquidate a Repo, we must:
        # change the ownership of all the collateral and give it to the asset party.

        for asset, quantity in self.collateral.items():
            # 1. Take one type of collateral at a time
            # 2. Change the ownership of the asset
            newAsset = asset.change_ownership(self.assetParty, quantity)
            # Give the new asset to the new owner
            self.assetParty.add(newAsset)

            if self.POSTDEFAULT_FIRESALE_CONTAGION:
                newAsset.put_for_sale(newAsset.quantity)

        # 3. Reduce the notional of this repo to zero.
        # TODO uncomment this for correct accounting
        # NOTE: the ledger keeps track of valuation, not
        # notional!
        #if self.assetParty is not None:
        #    self.assetParty.get_ledger().devalue_asset(self, self.principal)
        #self.liabilityParty.get_ledger().devalue_liability(self, self.principal)
        self.principal = 0

    def print_collateral(self):
        print("\nCollateral of ", self.liabilityParty.get_name())
        for k, v in self.collateral.items():
            asset = k
            quantity = v

            print((asset.get_name(self.liabilityParty), " for an amount ", quantity,
                  ", price ", asset.get_price(), " and haircut ", asset.get_haircut()))
        print("Cash collateral is ", self.cash_collateral)
        print("Principal of the Repo is ", self.principal)
        print("Amount already pulled is ", self.get_funding_already_pulled())
        print("Amount of collateral needed is ", (self.principal - self.get_funding_already_pulled()))
        print("Current valuation of collateral is ", self.get_haircutted_collateral_valuation())

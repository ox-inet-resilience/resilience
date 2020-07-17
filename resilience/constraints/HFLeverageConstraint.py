import numpy as np

from ..contracts import TradableAsset, AssetCollateral, Repo, Other


class HFLeverageConstraint(object):
    r"""
    Hedge fund's leverage constraint is calculated just like bank's except that
    the params differ for each hedge fund. Additionally, an effective minimum
    leverage is used to calculate the leverage buffer and leverage target.
    1 > \lambda_{buffer} (HF leverage buffer) > \lambda_{min} (HF minimum leverage)
    """
    __slots__ = 'me', 'ASSETTYPE'

    def __init__(self, me) -> None:
        self.me = me
        self.ASSETTYPE = me.model.parameters.AssetType

    def is_below_min(self) -> bool:
        return self.me.get_leverage() < self.get_effective_min_leverage()

    def get_effective_min_leverage(self):
        ldg = self.me.get_ledger()
        cash = self.me.get_cash()  # TODO or unencumbered cash?
        collateral = cash + ldg.get_asset_valuation_of(AssetCollateral)
        assert collateral >= 0, collateral

        if collateral == 0:
            return 0

        w_cash = cash / collateral
        _tradable = ldg.get_assets_of_type(AssetCollateral)
        repo = ldg.get_liability_valuation_of(Repo)
        # Sometimes _denominator is 0
        _denominator = w_cash + sum((1 - t.get_haircut()) * t.get_valuation('A') for t in _tradable) / collateral
        elligible_asset_minimum = repo / _denominator if _denominator > 0 else 0

        other = ldg.get_asset_valuation_of(Other)
        external = ldg.get_asset_valuation_of(TradableAsset, self.ASSETTYPE.EXTERNAL1)
        A_minimum = elligible_asset_minimum + other + external
        if A_minimum > 0:
            lev_min = (A_minimum - repo) / A_minimum
            return lev_min
        return 0

    def get_leverage_buffer(self, eml=None) -> float:
        if eml is None:
            eml = self.get_effective_min_leverage()
        return (self.me.LEVERAGE_INITIAL - eml) / 3 + eml

    def get_leverage_target(self, eml=None) -> float:
        if eml is None:
            eml = self.get_effective_min_leverage()
        return (self.me.LEVERAGE_INITIAL - eml) * 2 / 3 + eml

    def get_amount_to_delever(self) -> float:
        lev = self.me.get_leverage()
        eml = self.get_effective_min_leverage()
        is_below_buffer = lev < self.get_leverage_buffer(eml)
        if not is_below_buffer:
            # leverage ratio is still at safe zone
            return 0.0
        E = self.me.get_equity_valuation()
        current = E / lev
        target = E / self.get_leverage_target(eml)
        return current - target

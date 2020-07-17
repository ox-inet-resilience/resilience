import numpy as np
from ..contracts import Other, Loan, Repo, TradableAsset
from ..parameters import eps


def get_notional_minus_pulled(ldg, ctype):
    return sum((l.get_notional() - l.get_funding_already_pulled()) for l in ldg.get_assets_of_type(ctype))

class RWA_Constraint(object):
    __slots__ = 'me', 'ASSETTYPE'

    def __init__(self, me) -> None:
        self.me = me
        self.ASSETTYPE = me.model.parameters.AssetType

    def get_RWCR_min(self) -> float:
        if hasattr(self.me, 'RWCR_FLTF'):
            return self.me.RWCR_FLTF
        return self.me.model.parameters.RWCR_FLTF

    def is_insolvent(self, cached_equity=None) -> bool:
        rwa_ratio = self.get_RWA_ratio(cached_equity)
        return rwa_ratio < (self.get_RWCR_min() - eps)

    def is_below_buffer(self, cached_equity=None) -> bool:
        rwa_ratio = self.get_RWA_ratio(cached_equity)
        return rwa_ratio < self.me.RWCR_buffer

    def get_RWA_ratio(self, cached_equity=None) -> float:
        CET1E = self.me.get_CET1E(cached_equity)
        RWA = self.get_RWA()
        assert RWA > 0, RWA
        return CET1E / RWA

    def get_RWA(self) -> float:
        ldg = self.me.get_ledger()
        weights = self.me.RWA_weights
        rw = 0
        # tradable assets
        # If a part of the asset has been marked for sale, do not include it
        # in the RWA calculation
        for tradable_type in ['equities', 'corpbonds', 'govbonds', 'othertradables']:
            rw += weights[tradable_type] * sum((a.quantity - a.putForSale_) * a.price for a in self.me.get_tradable_of_type(tradable_type))

        # other assets
        rw += weights['other'] * ldg.get_asset_valuation_of(Other)
        # external assets
        rw += weights['external'] * ldg.get_asset_valuation_of(TradableAsset, self.ASSETTYPE.EXTERNAL1)
        # loan
        rw += weights['loan'] * get_notional_minus_pulled(ldg, Loan)
        # repo
        rw += weights['repo'] * get_notional_minus_pulled(ldg, Repo)
        return rw

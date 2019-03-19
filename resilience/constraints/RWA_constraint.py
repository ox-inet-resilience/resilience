import numpy as np
from ..contracts import Other, Loan, Repo, TradableAsset
from ..parameters import eps


class RWA_Constraint(object):
    __slots__ = 'me', 'ASSETTYPE'

    def __init__(self, me) -> None:
        self.me = me
        self.ASSETTYPE = me.model.parameters.AssetType

    def get_RWCR_min(self) -> np.longdouble:
        if hasattr(self.me, 'RWCR_min'):
            return self.me.RWCR_min
        return self.me.model.parameters.RWA_RATIO_MIN

    def is_insolvent(self, cached_equity=None) -> bool:
        rwa_ratio = self.get_RWA_ratio(cached_equity)
        return rwa_ratio < (self.get_RWCR_min() - eps)

    def is_below_buffer(self, cached_equity=None) -> bool:
        rwa_ratio = self.get_RWA_ratio(cached_equity)
        if hasattr(self.me, 'RWCR_buffer'):
            return rwa_ratio < self.me.RWCR_buffer
        return rwa_ratio < (self.me.model.parameters.RWA_RATIO_BUFFER - eps)

    def get_RWA_ratio(self, cached_equity=None) -> np.longdouble:
        CET1E = self.me.get_CET1E(cached_equity)
        RWA = self.get_RWA()
        assert RWA > 0, RWA
        return CET1E / RWA

    def get_RWA(self) -> np.longdouble:
        ldg = self.me.get_ledger()
        weights = self.me.RWA_weights
        rw = 0
        # tradables
        # If a part of the asset has been marked for sale, do not include it
        # in the RWA calculation
        for tradable_type in ['equities', 'corpbonds', 'govbonds', 'othertradables']:
            rw += weights[tradable_type] * sum((a.quantity - a.putForSale_) * a.price for a in self.me.get_tradable_of_type(tradable_type))

        # other
        rw += weights['other'] * ldg.get_asset_value_of(Other)
        # external
        rw += weights['external'] * ldg.get_asset_value_of(TradableAsset, self.ASSETTYPE.EXTERNAL1)
        # loan
        rw += weights['loan'] * sum((l.get_value() - l.get_funding_already_pulled()) for l in ldg.get_assets_of_type(Loan))
        # repo
        rw += weights['repo'] * sum((l.get_value() - l.get_funding_already_pulled()) for l in ldg.get_assets_of_type(Repo))
        return rw

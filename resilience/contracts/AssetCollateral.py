from .TradableAsset import TradableAsset
from ..parameters import eps


class AssetCollateral(TradableAsset):
    __slots__ = 'encumberedQuantity',
    ctype = 'AssetCollateral'

    def __init__(self, assetParty, assetType, assetMarket, amount):
        super().__init__(assetParty, assetType, assetMarket, amount)
        self.encumberedQuantity = 0.0
        # PERF This is SWST-specific view of asset collaterals for faster access
        assetParty.asset_collaterals[assetType].append(self)

    def is_eligible(self, me):
        is_external = self.assetType in [self.ASSETTYPE.EXTERNAL1, self.ASSETTYPE.EXTERNAL2, self.ASSETTYPE.EXTERNAL3]
        # PERF always assume that me is self.assetParty, hence no need to check (self.assetParty == me)
        return not is_external and ((self.quantity - self.encumberedQuantity) > self.putForSale_)

    def encumber(self, quantity):
        self.encumberedQuantity += quantity

    def unEncumber(self, quantity):
        self.encumberedQuantity -= quantity

    def get_haircut(self):
        return self.assetMarket.get_haircut(self.assetType)

    def get_unencumbered_quantity(self):
        # PERF optimized
        return self.quantity - self.encumberedQuantity

    def get_unencumbered_valuation(self):
        return (self.quantity - self.encumberedQuantity) * self.price

    def get_haircutted_ue_valuation(self):
        return self.get_unencumbered_valuation() * (1 - self.get_haircut())

    def get_valuation(self, side):
        return self.quantity * self.price

    def change_ownership(self, newOwner, quantity):
        assert self.quantity >= quantity - eps, (self.quantity, quantity)

        # First, reduce the quantity of this asset
        self.quantity -= quantity
        self.encumberedQuantity -= quantity

        # Have the owner lose the value of the asset
        self.assetParty.get_ledger().devalue_asset(self, quantity * self.price)

        new_asset = AssetCollateral(newOwner, self.get_asset_type(), self.assetMarket, quantity)

        return new_asset

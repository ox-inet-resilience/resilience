from ..actions import SellAsset
from economicsl.contract import Contract
from ..parameters import eps


def enum(**enums):
    return type('Enum', (), enums)


class TradableAsset(Contract):
    # TODO: mark the three external assets as non tradable.
    __slots__ = 'assetType', 'assetMarket', 'price', 'quantity', 'putForSale_', '_action', 'lcr_weight', 'ASSETTYPE'
    ctype = 'TradableAsset'

    def __init__(self, assetParty, assetType, assetMarket, quantity=0.0):
        # An Asset does not have a liability party
        super().__init__(assetParty, None)
        self.assetType = assetType
        self.assetMarket = assetMarket
        self.price = assetMarket.get_price(assetType)
        self.quantity = quantity
        self.putForSale_ = 0.0
        self._action = SellAsset(assetParty, self)
        self.ASSETTYPE = assetParty.model.parameters.AssetType
        self.lcr_weight = assetParty.model.parameters.EXTERNAL_LCR if assetType == self.ASSETTYPE.EXTERNAL1 else 0

    def get_name(self):
        return "Asset of type " + str(self.assetType)

    def get_action(self, me):
        # PERF me is always self.assetParty
        return self._action

    def is_eligible(self, me):
        is_external = self.assetType in [self.ASSETTYPE.EXTERNAL1, self.ASSETTYPE.EXTERNAL2, self.ASSETTYPE.EXTERNAL3]
        # PERF always assume that me is self.assetParty, hence no need to check (self.assetParty == me)
        return not is_external and (self.quantity > self.putForSale_)

    def put_for_sale(self, quantity):
        if abs(quantity) < eps:
            quantity = 0
        if (quantity == 0) or (self.price <= eps):
            # do not perform if quantity or price is 0
            return
        effective_qty = self.get_valuation('A') / self.price
        if abs(effective_qty - quantity) <= 2 * eps:
            quantity = effective_qty
        assert effective_qty - quantity >= -eps, (effective_qty - quantity)
        self.putForSale_ += quantity
        # TODO uncomment this for correct accounting
        # self.assetParty.get_ledger().devalue_asset(self, quantity * self.price)
        self.assetMarket.put_for_sale(self, quantity)

    def get_valuation(self, side):
        return self.quantity * self.price

    def get_price(self):
        return self.price

    def get_market_price(self):
        return self.assetMarket.get_price(self.assetType)

    def price_fell(self):
        return self.get_market_price() < self.price

    def value_lost(self):
        return (self.price - self.get_market_price()) * self.quantity

    def update_price(self):
        self.price = self.get_market_price()

    def get_asset_type(self):
        return self.assetType

    def get_put_for_sale(self):
        return self.putForSale_

    def get_LCR_weight(self):
        return self.lcr_weight

from economicsl import Action

from ..parameters import eps


class SellAsset(Action):
    __slots__ = 'asset',

    def __init__(self, me, asset):
        super().__init__(me)
        self.asset = asset

    def perform(self):
        super().perform()
        if self.asset.get_price() > 0:
            quantityToSell = self.get_amount() / self.asset.get_price()
            if abs(quantityToSell) <= eps:
                # do not perform is quantity is negligible
                return
            max_qty = self.get_max() / self.asset.get_price()
            assert max_qty >= quantityToSell - eps, (max_qty, quantityToSell, self.get_amount())
            assert quantityToSell > 0, quantityToSell  # positive value
            self.asset.put_for_sale(quantityToSell)

    def get_max(self):
        return self.asset.get_unencumbered_valuation() - self.asset.putForSale_ * self.asset.price

    def print(self):
        print(f"Sell Asset action by {self.asset.get_asset_party().get_name()}"
              f"-> asset type: {self.asset.get_asset_type()}, amount: "
              "%.2f" % self.get_amount())

    def get_name(self):
        return (f"Sell Asset of type {self.asset.get_asset_type()} [max: {self.get_max()}]")

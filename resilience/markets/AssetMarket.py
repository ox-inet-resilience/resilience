import logging
import math
from collections import defaultdict

import numpy as np

from .Market import Market
from ..parameters import eps

def linear_price_impact(fraction_sold, param):
    """
    For linear price function, see Greenwood 2015
    p' = p - fraction_sold * param
    """
    return -fraction_sold * param


def exponential_price_impact(fraction_sold, param):
    """
    exponential price impact as described in Cont Schaanning 2017 equation 30
    https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2541114
    """
    return math.exp(-fraction_sold * param)


# todo: should not be public
class Order(object):
    __slots__ = 'asset', 'quantity'

    def __init__(self, asset, quantity):
        self.asset = asset
        self.quantity = quantity

    def settle(self):
        # clear sale
        # We had an quantity Q of asset valued at price P. The we sold a quantity q that made the price fall to p. The
        # sale happened at the mid-point price (P+p)/2.
        #
        # 1) We gain a 'pq' of cash.
        # 2) We make a loss q(P-p)/2 from the sale, and a loss (Q-q)*(P-p) due to the devaluation.
        # @param quantity_sold the quantity of asset sold, in units
        quantity_sold = min(self.asset.quantity, self.quantity)
        assert quantity_sold > 0
        old_price = self.asset.assetMarket.oldPrices[self.asset.assetType]
        # Sell the asset at the mid-point price
        self.asset.quantity -= quantity_sold
        self.asset.putForSale_ -= quantity_sold
        value_sold = quantity_sold * (self.asset.price + old_price) / 2
        if value_sold >= eps:
            self.asset.assetParty.add_cash(value_sold)

class AssetMarket(Market):
    __slots__ = 'prices', 'priceImpacts', 'quantities_sold', 'haircuts', 'cumulative_quantities_sold', 'orderbook', 'oldPrices', 'total_quantities'

    def __init__(self, model):
        super().__init__(model)
        self.prices = defaultdict(lambda: 1.0)
        self.priceImpacts = {}
        # The total quantities sold during the most recent market clearing
        self.quantities_sold = defaultdict(np.longdouble)
        self.haircuts = {}
        # The cumulative total quantities sold from the earliest market clearing to
        # the most recent one
        self.cumulative_quantities_sold = defaultdict(np.longdouble)
        self.orderbook = []
        self.oldPrices = {}
        self.total_quantities = defaultdict(np.longdouble)

        self.priceImpacts = self.model.parameters.PRICE_IMPACTS
        # copy the value instead of accessing it directly
        self.haircuts = dict(self.model.parameters.INITIAL_HAIRCUTS)

    def put_for_sale(self, asset, quantity):
        assert quantity > 0, quantity
        self.orderbook.append(Order(asset, quantity))
        atype = asset.get_asset_type()

        logging.debug(f"Putting for sale: {atype} at quantity {quantity}")

        self.quantities_sold[atype] += quantity

    def clear_the_market(self):
        logging.debug("\nMARKET CLEARING\n")
        self.oldPrices = dict(self.prices)
        # 1. Update price based on price impact
        for atype, v in self.quantities_sold.items():
            if self.model.parameters.PREDEFAULT_FIRESALE_CONTAGION or self.model.parameters.POSTDEFAULT_FIRESALE_CONTAGION:
                self.compute_price_impact(atype, v)

                newPrice = self.prices[atype]
                priceLost = self.oldPrices[atype] - newPrice
                if priceLost > 0:
                    self.model.devalueCommonAsset(atype, priceLost)

            if self.model.parameters.HAIRCUT_CONTAGION:
                self.compute_haircut(atype, v)

            self.cumulative_quantities_sold[atype] += v

        self.quantities_sold = defaultdict(np.longdouble)

        # 2. Perform the sale
        for order in self.orderbook:
            order.settle()
        self.orderbook = []

    def compute_price_impact(self, assetType, qty_sold):
        current_price = self.prices[assetType]
        price_impact = self.priceImpacts[assetType]
        total = self.total_quantities[assetType]
        if total <= 0:
            return

        fraction_sold = qty_sold / total

        # new_price = current_price * exponential_price_impact(fraction_sold, price_impact)
        new_price = max(0, current_price + linear_price_impact(fraction_sold, price_impact))

        self.set_price(assetType, new_price)

    def compute_haircut(self, assetType, qty_sold):
        """
        We took a departure from Bookstaber 2014
        """
        if assetType not in self.haircuts:
            return

        h0 = self.model.parameters.INITIAL_HAIRCUTS[assetType]
        p0 = 1.0
        alpha = self.model.parameters.HAIRCUT_SLOPE

        newHaircut = h0 + max(0, alpha * (1 - self.get_price(assetType) / p0))

        # Truncate to 1.0 when the value > 1
        newHaircut = min(newHaircut, 1.0)

        self.haircuts[assetType] = newHaircut

    def get_price(self, assetType):
        return self.prices[assetType]

    def get_haircut(self, assetType):
        return self.haircuts.get(assetType, 0.0)

    def set_price(self, assetType, newPrice):
        self.prices[assetType] = newPrice

    def get_asset_types(self):
        """
        """
        return self.prices.keys()

    def get_cumulative_quantities_sold(self, assetType):
        """
        Returns the cummulative total quantities sold of all the market clearings
        """
        return self.cumulative_quantities_sold[assetType]

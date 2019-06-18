cimport cython
from .Market cimport Market

cdef double linear_price_impact(double fraction, double param)

# This is an internal C-only class
@cython.final
cdef class Order:
    cdef object asset
    cdef double quantity
    cdef void settle(self)


@cython.final
cdef class AssetMarket(Market):
    cdef object prices
    cdef object quantities_sold
    cdef object cumulative_quantities_sold
    cdef object orderbook
    cdef public object oldPrices
    cdef public object total_quantities
    cdef object priceImpacts
    cdef object haircuts
    cpdef void put_for_sale(self, object asset, double quantity)
    @cython.locals(order=Order)
    cpdef void clear_the_market(self)
    @cython.locals(current_price=double, price_impact=double, total=double, fraction_sold=double, new_price=double)
    cpdef void compute_price_impact(self, int assetType, double qty_sold)
    @cython.locals(h0=double, p0=double, alpha=double, newHaircut=double)
    cpdef void compute_haircut(self, int assetType, double qty_sold)
    cpdef double get_price(self, int assetType)
    cpdef double get_haircut(self, int assetType)
    cpdef void set_price(self, int assetType, double newPrice)
    cpdef object get_asset_types(self)
    cpdef double get_cumulative_quantities_sold(self, int assetType)

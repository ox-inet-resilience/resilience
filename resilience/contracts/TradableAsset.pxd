# cython: language_level=3, infer_types=True
cimport cython
from economicsl.contract cimport Contract
from ..markets.AssetMarket cimport AssetMarket

cdef double eps

cdef class TradableAsset(Contract):
    cdef public int assetType
    cdef public AssetMarket assetMarket
    cdef public double price
    cdef public double quantity
    cdef public double putForSale_
    cdef public object _action
    cdef public object ASSETTYPE
    cdef public double lcr_weight
    cpdef object get_name(self)
    cpdef object get_action(self, object me)
    cpdef bint is_eligible(self, object me)
    @cython.locals(effective_qty=double)
    cpdef void put_for_sale(self, double quantity)
    cpdef double get_valuation(self, str side)
    cpdef double get_price(self)
    cpdef double get_market_price(self)
    cpdef bint price_fell(self)
    cpdef double value_lost(self)
    cpdef void update_price(self)
    cpdef int get_asset_type(self)
    cpdef double get_put_for_sale(self)
    cpdef double get_LCR_weight(self)

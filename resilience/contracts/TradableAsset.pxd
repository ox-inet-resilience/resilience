cimport cython
from economicsl.contract cimport Contract

cdef class TradableAsset(Contract):
    cdef public int assetType
    cdef public object assetMarket
    cdef public double price
    cdef public double quantity
    cdef public double putForSale_
    cdef public object _action
    cdef public object ASSETTYPE
    cdef public double lcr_weight
    cpdef object get_name(self)
    cpdef object get_action(self, object me)
    cpdef bint is_eligible(self, object me)
    cpdef void put_for_sale(self, object quantity)
    cpdef long double get_valuation(self, str side)
    cpdef double get_price(self)
    cpdef double get_market_price(self)
    cpdef bint price_fell(self)
    cpdef long double value_lost(self)
    cpdef void update_price(self)
    cpdef int get_asset_type(self)
    cpdef long double get_put_for_sale(self)
    cpdef double get_LCR_weight(self)

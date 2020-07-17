# cython: language_level=3
cimport cython
from .TradableAsset cimport TradableAsset

cdef double eps

# This class must not be subclassed
# TODO fix that enabling final doesn't raise error
#@cython.final
cdef class AssetCollateral(TradableAsset):
    cdef public double encumberedQuantity
    cpdef bint is_eligible(self, object me)
    cpdef void encumber(self, double quantity)
    cpdef void unEncumber(self, double quantity)
    cpdef double get_haircut(self)
    cpdef double get_unencumbered_quantity(self)
    cpdef double get_unencumbered_valuation(self)
    cpdef double get_haircutted_ue_valuation(self)
    cpdef double get_valuation(self, str side)
    cpdef object change_ownership(self, object newOwner, double quantity)

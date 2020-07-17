cimport cython

cdef class RWA_Constraint:
    cdef object me
    cdef object ASSETTYPE
    cpdef double get_RWCR_min(self)
    cpdef bint is_insolvent(self, object cached_equity=*)
    cpdef bint is_below_buffer(self, object cached_equity=*)
    cpdef double get_RWA_ratio(self, object cached_equity=*)
    @cython.locals(ldg=object, weights=object, rw=double, val=double)
    cpdef double get_RWA(self)

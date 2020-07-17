cimport cython
from economicsl.contract cimport Contract

cdef class Other(Contract):
    cdef double principal
    cdef object _payloan
    cdef double fundingAlreadyPulled
    cdef double lcr_weight
    cpdef double get_LCR_weight(self)
    cpdef object get_name(self)
    cpdef double get_notional(self)
    cpdef double get_valuation(self, str side)
    cpdef void set_amount(self, double amount)
    cpdef bint is_eligible(self, object me)
    cpdef object get_action(self, object me)
    cpdef double get_funding_already_pulled(self)
    @cython.locals(notional=double)
    cpdef void reduce_principal(self, double amount)
    @cython.locals(notional=double, amount=double)
    cpdef void pay_loan(self, double amount)
    cpdef void liquidate(self)

cimport cython
from economicsl.contract cimport Contract

cdef class Loan(Contract):
    cdef public object parameters
    cdef public double principal
    cdef public double fundingAlreadyPulled
    cdef object _pullfunding
    cdef object _payloan
    cpdef double get_LCR_weight(self)
    cpdef object get_name(self)
    cpdef void pay_loan(self, amount)
    cpdef void reduce_principal(self, amount)
    cpdef void reduce_pull_funding_amount(self, amount)
    cpdef object get_action(self, me)
    cpdef bint is_eligible(self, me)
    cpdef double get_notional(self)
    cpdef double get_valuation(self, side)
    cpdef void liquidate(self)
    cpdef void increase_funding_pulled(self, fundingPulled)
    cpdef double get_funding_already_pulled(self)

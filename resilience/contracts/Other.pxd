from economicsl.contract cimport Contract

cdef class Other(Contract):
    cdef long double principal
    cdef object _payloan
    cdef long double fundingAlreadyPulled
    cdef double lcr_weight
    cpdef double get_LCR_weight(self)
    cpdef object get_name(self)
    cpdef long double get_notional(self)
    cpdef long double get_valuation(self, str side)
    cpdef void set_amount(self, long double amount)
    cpdef bint is_eligible(self, object me)
    cpdef object get_action(self, object me)
    cpdef long double get_funding_already_pulled(self)
    cpdef void reduce_principal(self, long double amount)
    cpdef void pay_loan(self, long double amount)
    cpdef void liquidate(self)

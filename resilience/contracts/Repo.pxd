from .Loan cimport Loan

cdef class Repo(Loan):
    cdef public object collateral
    cdef public double cash_collateral
    cdef public double prev_margin_call
    cdef public double future_margin_call
    cdef public double future_max_collateral
    cdef public bint MARGIN_CALL_ON
    cdef public bint POSTDEFAULT_FIRESALE_CONTAGION
    cdef public object parameters
    cpdef object get_name(self)
    cpdef void pledge_collateral(self, object asset, double quantity)
    cpdef double pledge_cash_collateral(self, double amount)
    cpdef double unpledge_cash_collateral(self, double amount)
    cpdef void unpledge_collateral(self, object asset, double amount)
    #cpdef double get_max_ue_haircutted_collateral(self)
    cpdef double get_mc_size(self)
    cpdef void fulfil_margin_call(self)
    cpdef void prepare_future_margin_call(self)
    #cpdef double get_haircutted_collateral_valuation(self)
    cpdef double get_collateral(self)
    cpdef void pledge_proportionally(self, double total)
    cpdef void unpledge_proportionally(self, double excess)
    cpdef void liquidate(self)
    cpdef void print_collateral(self)

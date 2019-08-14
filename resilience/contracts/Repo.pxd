from .Loan cimport Loan

cdef class Repo(Loan):
    cdef public object collateral
    cdef public long double cash_collateral
    cdef public long double prev_margin_call
    cdef public long double future_margin_call
    cdef public long double future_max_collateral
    cdef public bint MARGIN_CALL_ON
    cdef public bint POSTDEFAULT_FIRESALE_CONTAGION
    cdef public object parameters
    cpdef object get_name(self)
    cpdef void pledge_collateral(self, object asset, long double quantity)
    cpdef long double pledge_cash_collateral(self, long double amount)
    cpdef long double unpledge_cash_collateral(self, long double amount)
    cpdef void unpledge_collateral(self, object asset, long double amount)
    #cpdef long double get_max_ue_haircutted_collateral(self)
    cpdef long double get_mc_size(self)
    cpdef void fulfil_margin_call(self)
    cpdef void prepare_future_margin_call(self)
    #cpdef long double get_haircutted_collateral_valuation(self)
    cpdef long double get_collateral(self)
    cpdef void pledge_proportionally(self, long double total)
    cpdef void unpledge_proportionally(self, long double excess)
    cpdef void liquidate(self)
    cpdef void print_collateral(self)

from .Loan cimport Loan

cdef class Deposit(Loan):
    cpdef double get_LCR_weight(self)
    cpdef object get_name(self)

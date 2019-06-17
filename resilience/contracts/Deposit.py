from .Loan import Loan


class Deposit(Loan):
    # TODO make a liability class with a pay off liability action
    # that Deposit, Other, and Loan can inherit from instead of Deposit
    # inheriting from Loan as it is currently
    ctype = 'Deposit'

    def __init__(self, depositor, holder, amount):
        super().__init__(depositor, holder, amount)
        _model = (depositor or holder).model
        self.lcr_weight = _model.parameters.DEPOSITS_LCR

    def get_name(self):
        return "Deposits"

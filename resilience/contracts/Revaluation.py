import numpy as np

from economicsl import Contract


class Revaluation(Contract):
    __slots__ = 'me', 'revaluation', 'revaluation_initial', 'notionals_initial'
    ctype = 'Revaluation'

    def __init__(self, me):
        super().__init__(me, None)
        self.me = me
        self.reset_values()
        self.revaluation_initial = None  # to be used only in a version of bail-in run
        self.notionals_initial = None  # to be used only in a version of bail-in run

    def get_name(self, me):
        return "Interbank revaluation of " + me.get_name()

    def get_value(self):
        return self.revaluation

    def add_r9n(self, x):
        self.revaluation += x

    def reset_values(self):
        self.revaluation = 0

    def set_revaluation_initial(self, notionals_initial):
        self.revaluation_initial = sum(self.payoffs)
        self.notionals_initial = sum(notionals_initial)

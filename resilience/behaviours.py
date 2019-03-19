import logging

from .actions import PayLoan, SellAsset
from .parameters import eps

# List of strategies that consists of behavioural units

def do_nothing(bank):
    pass


# List of behavioural units
def perform_proportionally(actions, amount: float = None) -> float:
    # This is a common pattern shared by sell assets and
    # pay loan.
    # See Greenwood 2015 and Cont-Schaanning 2017.

    # maximum is the total amount that can be performed
    maximum = sum(a.get_max() for a in actions)
    if amount is None:
        amount = maximum
    if (maximum <= 0.0) or (amount <= 0.0):
        # we cannot perform any actions
        return 0.0

    _amount = min(maximum, amount)
    for action in actions:
        _each_amount = action.get_max() * _amount / maximum
        if _each_amount > eps:
            action.set_amount(_each_amount)
            action.perform()
    return _amount

def pay_off_liabilities(inst, amount):
    logging.debug(f"Pay off liabilities (delever) proportionally: {amount}")
    payLoanActions = inst.get_all_actions_of_type(PayLoan)
    return perform_proportionally(payLoanActions, amount)

def sell_assets_proportionally(inst, amount=None):
    sellAssetActions = inst.get_all_actions_of_type(SellAsset)
    # TODO when endogenous LGD is calculated, it might be necessary
    # to calibrate the total amount sold by the expected price sold
    return perform_proportionally(sellAssetActions, amount)

import logging
from collections import defaultdict

import numpy as np  # for annotation purpose
from economicsl import Agent

from ..contracts import FailedMarginCallException
from ..contracts import AssetCollateral, Deposit, Other, Repo
from ..behaviours import sell_assets_proportionally

from ..parameters import eps
from .DefaultException import DefaultException


class Institution(Agent):
    __slots__ = 'encumberedCash', 'equityAtDefault', 'availableActions', 'marked_as_default', 'asset_collaterals', 'has_tradable_cache', 'params', 'model', 'params'

    def __init__(self, name, model):
        super().__init__(name, model.simulation)
        self.encumberedCash = 0.0
        self.equityAtDefault = 0.0  # to be calculated at default
        self.availableActions = {}
        self.marked_as_default = False
        # PERF This is SWST-specific "view" of asset collaterals for faster access
        self.asset_collaterals = defaultdict(list)
        self.has_tradable_cache = False
        self.model = model
        self.params = model.parameters

    def _add_tradables(self, arr, template) -> None:
        if len(arr) > 0:
            for i in range(len(arr)):
                if arr[i] > 0:
                    self.add(AssetCollateral(self, getattr(self.params.AssetType, template % (i + 1)),
                                             self.model.assetMarket, arr[i]))

    def init(self, assets, liabilities) -> None:
        """ initiates the agent with a determined amount of:

            Assets:
            - cash
            - equities
            - corporate bonds
            - government bonds
            - other tradable asset
            - otherAsset
            Liabilities:
            - deposits
            - longTerm (not used)
            - otherLiability (initialized in model)
        """
        cash, equities, corp_bonds, gov_bonds, other_tradable, otherAsset = assets
        deposits, longTerm = liabilities
        self.add_cash(cash)

        # Asset side
        self._add_tradables(equities, 'EQUITIES%d')
        self._add_tradables(corp_bonds, 'CORPORATE_BONDS%d')
        self._add_tradables(gov_bonds, 'GOV_BONDS%d')
        self._add_tradables(other_tradable, 'OTHERTRADABLE%d')

        if (otherAsset > 0):
            self.add(Other(self, None, otherAsset))

        # Liability side
        if (deposits > 0):
            self.add(Deposit(None, self, deposits))
        if (longTerm > 0):
            # LongTermUnsecured has been removed
            # TODO remove this from args
            pass

    def pay_liability(self, amount, loan) -> None:
        """
        Pre-condition: we have enough liquidity!

        Args:
            amount: the amount to pay back of this loan
            loan: the loan we are paying back
        """
        diff = self.get_ue_cash() - amount
        if abs(diff) <= 2 * eps:
            amount = self.get_ue_cash()
        assert diff >= -2 * eps, diff
        self.get_ledger().pay_liability(amount, loan)

    def update_asset_prices(self) -> None:
        for asset in self.get_ledger().get_all_assets():
            if asset.price_fell():
                self.get_ledger().devalue_asset(asset, asset.valueLost())
                asset.update_price()

    def devalue_asset_collateral_of_type(self, assetType, priceLost) -> None:
        for asset in self.asset_collaterals[assetType]:
            self.get_ledger().devalue_asset(asset, asset.quantity * priceLost)
            # Update the price
            asset.update_price()

    def get_encumbered_cash(self):
        return self.encumberedCash

    def get_available_actions(self):
        """
        :return: A list of Actions that are available to me at this moment
        is_eligible is a check for the contractual constraint
        """
        eligibleActions = defaultdict(list)
        for contract in (self.get_ledger().get_all_assets() + self.get_ledger().get_all_liabilities()):
            if contract.is_eligible(self):
                action = contract.get_action(self)
                eligibleActions[type(action).__name__].append(action)

        return eligibleActions

    def get_equity_valuation(self) -> float:
        return self.get_ledger().get_equity_valuation() if self.is_alive() else self.equityAtDefault

    def get_tradable_of_type(self, atype):
        if not self.has_tradable_cache:
            def _get(SET):
                return [a for a in self.get_ledger().get_assets_of_type(AssetCollateral) if a.get_asset_type() in SET]
            self.tradables = {
                'govbonds': _get(self.params.govbonds_dict.values()),
                'corpbonds': _get(self.params.corpbonds_dict.values()),
                'equities': _get(self.params.equities_dict.values()),
                'othertradables': _get(self.params.othertradables_dict.values()),
            }
            self.has_tradable_cache = True
        return self.tradables[atype]

    def print_balance_sheet(self) -> None:
        print("\nBalance Sheet of", self.get_name() + "\n**************************")
        self.get_ledger().print_balance_sheet(self)
        print("\nLeverage ratio: %.2f%%" % (100 * self.get_leverage()))

    def fulfil_margin_calls_or_default(self) -> None:
        try:
            repos = self.get_ledger().get_liabilities_of_type(Repo)
            for repo in repos:
                repo.fulfil_margin_call()
        except FailedMarginCallException:
            logging.debug("A margin call failed.")
            raise DefaultException(self, DefaultException.TypeOfDefault.FAILED_MARGIN_CALL)

    def trigger_default(self) -> None:
        self.marked_as_default = False

    def encumber_cash(self, amount):
        ue_cash = self.get_ue_cash()
        if amount > ue_cash:
            # if it is not enough truncate to current unencumbered cash
            amount = ue_cash
        self.encumberedCash += amount
        return amount

    def unencumber_cash(self, amount) -> None:
        assert (self.encumberedCash - amount) >= -eps
        self.encumberedCash -= amount

    def receive_shock_to_asset(self, assetType, fractionLost) -> None:
        assets_tobe_shocked = [asset for asset in
                         self.get_ledger().get_all_assets() if
                         hasattr(asset, 'get_asset_type') and
                         asset.get_asset_type() == assetType]

        for asset in assets_tobe_shocked:
            self.get_ledger().devalue_asset(asset, asset.get_valuation('A') * fractionLost)
            asset.update_price()

    def get_matured_obligations(self):
        return self.mailbox.get_matured_obligations()

    def get_all_pending_obligations(self):
        return self.mailbox.get_all_pending_obligations()

    def get_pending_payments_to_me(self):
        return self.mailbox.get_pending_payments_to_me()

    def fulfil_all_requests(self):
        self.mailbox.fulfil_all_requests()

    def fulfil_matured_requests(self):
        self.mailbox.fulfil_matured_requests()

    def get_cash_commitments(self):
        cashCommitments = [0.0] * self.params.TIMESTEPS_TO_PAY * 3

        for obligation in self.get_obligation_inbox():
            if not obligation.is_fulfilled():
                index = obligation.get_time_to_pay() - self.get_time() - 1
                # Caution: this is the time when python's feature of negative
                # indexing becomes detrimental and hides bugs.
                # If index is negative, it means that an agent might have
                # skipped the step to check matured obligations
                assert index >= 0, (index, obligation.get_time_to_pay(), self.get_time())
                cashCommitments[index] += obligation.get_amount()
        return cashCommitments

    def sell_assets_proportionally(self, amount=None):
        return sell_assets_proportionally(self, amount)

    def get_cash_inflows(self):
        cashInflows = [0.0] * self.params.TIMESTEPS_TO_PAY * 3

        for obligation in self.get_obligation_outbox():
            if not obligation.is_fulfilled():
                index = obligation.get_time_to_receive() - self.get_time() - 1
                if index <= -1:
                    # the obligation is already expired; the bank that is supposed to fulfil it has defaulted
                    continue
                cashInflows[index] += obligation.get_amount()
        return cashInflows

    def get_ue_cash(self):
        # returns unencumberedCash
        # the method name is chosen instead of getUnEncumberedCash so it is not accidentally read as
        # getEncumberedCash
        return self.get_cash() - self.get_encumbered_cash()

    def get_equity_loss(self):
        initial_equity = self.get_ledger().get_initial_equity()
        return (self.get_equity_valuation() - initial_equity) / initial_equity

    def set_initial_valuations(self) -> None:
        self.get_ledger().set_initial_valuations()

    # methods after this line is merged from Behaviour class
    def choose_actions(self):
        pass

    def act_fulfil_contractual_obligations(self):
        pass

    def handle_default(self):
        # This marked_as_default is necessary because
        # trigger_default( needs to be a separate loop from
        # act(), to ensure order independence.
        self.marked_as_default = True
        self.equityAtDefault = self.get_equity_valuation()
        # self.trigger_default()
        self.alive = False
        if hasattr(self, 'isaBank') and self.isaBank:
            self.simulation.bank_defaults_this_round += 1

    def act(self) -> None:
        if not self.is_alive():
            logging.debug(f"{self.get_name()} cannot act. I'm crucified, dead and buried, and have descended into hell.")
            return

        if self.params.PRINT_BALANCE_SHEETS:
            self.print_balance_sheet()
        if self.params.PRINT_MAILBOX:
            self.print_mailbox()

        self.availableActions = self.get_available_actions()

        try:
            self.choose_actions()
        except DefaultException:
            self.handle_default()

        logging.debug(f"{self.get_name()} done.\n*********")

    def get_all_actions_of_type(self, actionType):
        try:
            return self.availableActions[actionType.__name__]
        except KeyError:
            return []

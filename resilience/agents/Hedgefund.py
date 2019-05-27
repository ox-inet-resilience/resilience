from ..constraints.HFLeverageConstraint import HFLeverageConstraint
from ..contracts import FailedMarginCallException, Repo

from .Bank import LeveragedInst


class Hedgefund(LeveragedInst):
    def __init__(self, name, model):
        super().__init__(name, model, False)
        self.leverage_constraint = HFLeverageConstraint(self)

    def get_cash_buffer(self):
        return self.get_ledger().get_asset_valuation() * self.model.parameters.HF_CASH_BUFFER_AS_FRACTION_OF_ASSETS

    def get_HQLA_target(self):
        return self.get_ledger().get_asset_valuation() * self.model.parameters.HF_CASH_TARGET_AS_FRACTION_OF_ASSETS

    def trigger_default(self):
        super().trigger_default()

        # firesell assets
        self.sell_assets_proportionally()

        # liquidate repos
        repos = self.get_ledger().get_liabilities_of_type(Repo)
        for repo in repos:
            repo.liquidate()

    def prepare_future_margin_call(self):
        repos = self.get_ledger().get_liabilities_of_type(Repo)
        for repo in repos:
            repo.prepare_future_margin_call()

    def create_repos(self, lender, principal):
        def _pledge_one_asset_group(name, amount):
            _r = Repo(lender, self, amount)
            lender.add(_r)
            self.add(_r)

            principal = _r.principal
            collateral = self.get_tradable_of_type(name)
            _r.collateral = {c: 0 for c in collateral}
            max_collateral = _r.get_max_ue_haircutted_collateral()
            pledge_amount = min(max_collateral, principal)
            _r.pledge_proportionally(pledge_amount)
            isnot_enough = pledge_amount < _r.principal
            if isnot_enough:
                _r.principal = pledge_amount
            return principal - pledge_amount, isnot_enough, _r

        remainder, isnot_enough, _ = _pledge_one_asset_group('corpbonds', principal)
        if not isnot_enough:
            return

        remainder, isnot_enough, _ = _pledge_one_asset_group('equities', remainder)
        if not isnot_enough:
            return

        remainder, isnot_enough, _ot_repo = _pledge_one_asset_group('othertradables', remainder)
        if not isnot_enough:
            return

        remainder, isnot_enough, _ = _pledge_one_asset_group('govbonds', remainder)
        if not isnot_enough:
            return

        # cash
        cash_pledged = _ot_repo.pledge_cash_collateral(remainder)
        _ot_repo.principal += cash_pledged
        if cash_pledged < remainder:
            raise FailedMarginCallException("Failed Margin Call")

    def perform_liquidity_management(self):
        """
        Continuation of St. Patrick Day's Algorithm for HF
        """
        super().perform_liquidity_management()
        # 5. HF raise liquidity to reach cash target
        A = self.get_ledger().get_asset_valuation()
        if A == 0:  # to make sure there is no divide-by-zero
            return
        uec = self.get_ue_cash()
        if uec / A < 0.9 * self.uec_fraction_initial:
            self.sell_assets_proportionally(self.uec_fraction_initial * A - uec)

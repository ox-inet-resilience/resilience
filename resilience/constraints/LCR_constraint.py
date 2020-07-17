import numpy as np
from ..contracts import AssetCollateral, Other, Loan, Repo


class LCR_Constraint(object):
    """
    An LCR constraint.
    LCR = (stock of high-quality liquid assets) / (total net cash outflows over the next T calendar days)
    For formula reference, see Basel III International framework for liquidity risk
    measurement, standards and monitoring, paragraph 1[1]

    [1] http://www.bis.org/publ/bcbs188.pdf
    """
    __slots__ = 'me',

    def __init__(self, me) -> None:
        self.me = me

    def is_below_buffer(self) -> bool:
        return self.get_LCR() < self.me.model.parameters.BANK_LCR_BUFFER

    def get_LCR_denominator_correction(self) -> float:
        # due to firesale and pullfunding
        ldg = self.me.get_ledger()
        lw_putforsale = sum(t.putForSale_ * t.price * t.get_LCR_weight() for t in ldg.get_assets_of_type(AssetCollateral))
        lw_funding_pulled = (
            sum(l.get_funding_already_pulled() * l.get_LCR_weight() for l in ldg.get_assets_of_type(Loan)) +
            sum(r.get_funding_already_pulled() * r.get_LCR_weight() for r in ldg.get_assets_of_type(Repo)))
        return lw_putforsale + lw_funding_pulled

    def get_inflows(self):
        return sum(a.get_valuation('A') * a.get_LCR_weight() for
                   a in self.me.get_ledger().get_all_assets())

    def get_outflows(self):
        ldg = self.me.get_ledger()
        outflows = sum(l.get_valuation('L') * l.get_LCR_weight() for
                       l in ldg.get_all_liabilities()
                       if not l.ctype == 'Other')
        outflows += ldg.get_liability_valuation_of(Other) * self.me.LCR_weight_other
        return outflows

    def get_LCR_denominator(self) -> float:
        """
        (Total net cash outflow over the next T calendar days) = outflows -
        Min{inflows, 75% of outflows}
        For reference, see paragraph 50 of [1].
        LCRweight of each contracts can be changed in Parameters
        """
        return self.me.LCR_den_initial
        BASELIII_CASH_OUTFLOW_CAP = 0.75
        # TODO check, all the assets are probably an instance of Asset
        inflows = self.get_inflows()
        inflows -= self.get_LCR_denominator_correction()

        outflows = self.get_outflows()
        return outflows - min(inflows, BASELIII_CASH_OUTFLOW_CAP * outflows)

    def get_gov_bonds(self):
        return sum(a.get_valuation('A') for a in self.me.get_tradable_of_type('govbonds'))

    def get_HQLA(self, cash_raised=0) -> float:
        """
        high-quality liquid assets (HQLA) = (unencumbered cash for now)

        Definition of HQLA can be found in section 3 of reference [1].
        HQLA = (level 1 assets) + 40% of (level 2 assets)
        """
        ue_cash = self.me.get_ue_cash()
        gb = self.get_gov_bonds()
        return ue_cash + gb + cash_raised  # + sum(self.me.getCashInflows()[:self.me.model.parameters.LIQUIDITY_HORIZON])

    def get_LCR(self, cash_raised=0) -> float:
        """
        Return HQLA / (total net cash outflows over the next T calendar days)
        T is specified at Parameters.LIQUIDITY_HORIZON
        """
        return self.get_HQLA(cash_raised) / self.get_LCR_denominator()

    def get_liquidity_to_raise(self) -> float:
        return max(self.get_LCR_denominator() * (self.me.model.parameters.BANK_LCR_TARGET - self.get_LCR()), 0.0)

    def get_HQLA_target(self, den=None) -> float:
        if den is None:
            den = self.get_LCR_denominator()
        return max(self.me.model.parameters.BANK_LCR_TARGET * den, 0)

    def get_cash_buffer(self) -> float:
        if not self.me.model.parameters.BANK_LCR_ON:
            return 0
        return max(self.me.model.parameters.BANK_LCR_BUFFER * self.get_LCR_denominator() - self.get_gov_bonds(), 0)

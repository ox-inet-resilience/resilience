import logging

from ..constraints import BankLeverageConstraint, LCR_Constraint, RWA_Constraint
from ..actions import PullFunding, SellAsset
from ..contracts import Loan, Repo, Other

from ..behaviours import perform_proportionally, pay_off_liabilities

from .Institution import Institution
from .DefaultException import DefaultException
from ..parameters import eps, isequal_float


class LeveragedInst(Institution):
    def __init__(self, name, model, isaBank=True):
        super().__init__(name, model)
        self.leverage_constraint = None
        self.isaBank = isaBank

    def get_leverage(self):
        """
        (Book Leverage Ratio) = (current Equity) / (current Asset)
        In `Bank`, this method will be overriden
        """
        A = self.get_ledger().get_asset_valuation()
        L = self.get_ledger().get_liability_valuation()
        if A == 0:  # prevents divide by 0
            return 0
        return (A - L) / A

    def pull_funding_proportionally(self, amount):
        """
        This is an action
        """

        if amount <= 0:
            # we are calling this function with argument 0
            return 0

        # First, pull funding proportionally from interbank loans.
        # Then if these are exhausted, pull funding proportionally from repo

        pullFundingActions = self.get_all_actions_of_type(PullFunding)
        interbank_pfas = []
        repo_pfas = []
        # separate out the actions into the unsecured loans and secured loans
        #
        for pfa in pullFundingActions:
            if pfa.loan.ctype == 'Repo':
                repo_pfas.append(pfa)
            else:
                interbank_pfas.append(pfa)

        # 1. interbank
        _amount = perform_proportionally(interbank_pfas, amount)
        is_enough = (amount <= 0) or isequal_float(_amount, amount)
        if is_enough:
            return amount, is_enough

        # We cannot pull enough funding from interbank loan. We pull the
        # greatest possible amount from interbank loan: `_amount`
        amount -= _amount

        # 2. secured loan / repo
        _amount_repo = perform_proportionally(repo_pfas, amount)
        is_enough = (amount <= 0) or isequal_float(_amount_repo, amount)
        return _amount + _amount_repo, is_enough

    def raise_liquidity_with_pecking_order(self, amount):
        """
        This is an action with pecking order of:
        1. pull funding
           1.1 interbank pf
           1.2 reverse-repo pf
        2. sell asset
        """
        # We must raise liquidity with pecking order now.
        assert amount > 0, amount

        firesales = 0.0
        fundingPulled = 0.0

        if self.model.parameters.PREDEFAULT_PULLFUNDING_CONTAGION:
            fundingPulled, is_enough = self.pull_funding_proportionally(amount)
            if is_enough:
                # While in principle enough liquidity has been raised, however
                # due to price impact, non-repayments, and other factors, the
                # actual liquidity raised later on may differ from the
                # calculated liquidity raised.  These factors are not taken
                # into account in order to simplify the calculation.
                return fundingPulled

        firesales = self.sell_assets_proportionally(amount - fundingPulled)

        if amount > fundingPulled + firesales:
            logging.debug("We could not raise enough liquidity.")

        return fundingPulled + firesales

    # methods after this line are merged from BankBehaviour
    def get_cash_buffer(self):
        pass

    def get_HQLA_target(self):
        pass

    def _analyze_expected_balance_sheet(self, balance, timeIndex, cashInflows, cashCommitments, rescue_action):
        # Note: rescue action is a function
        balance += cashInflows[timeIndex]
        balance -= cashCommitments[timeIndex]

        if balance < 0:
            # At time step of timeIndex + 1 from now, we will be short of liquidity
            # since our expected balance will drop below zero
            # so we perform rescue action
            balance += rescue_action(-balance)
        return balance

    def pay_matured_cash_commitments_or_default(self):
        maturedPullFunding = self.get_matured_obligations()
        if maturedPullFunding > 0:
            logging.debug("We have matured payment obligations for a total of %.2f" % maturedPullFunding)
            if (self.get_ue_cash() >= maturedPullFunding - eps):
                self.fulfil_matured_requests()
            else:
                logging.debug("A matured obligation was not fulfilled.\nDEFAULT DUE TO LACK OF LIQUIDITY")
                self.cause_of_default = 'liquidity'
                raise DefaultException(self, DefaultException.TypeOfDefault.LIQUIDITY)

    def print_liquidity(self):
        print("\nLiquidity management for this timestep")
        print("Current unencumbered cash -> ", self.get_ue_cash())
        print("LCR buffer -> ", self.get_cash_buffer())
        print("Needed to fulfil obligations -> ", sum(self.get_cash_commitments()))
        print("Expected cash inflows -> ", sum(self.get_cash_inflows()))

    def perform_liquidity_management(self):
        """
        i.e. St. Patrick Day's Algorithm
        """
        params = self.model.parameters
        use_LEVERAGE = params.BANK_LEVERAGE_ON

        balance = self.get_ue_cash()
        cashInflows = self.get_cash_inflows()
        cashCommitments = self.get_cash_commitments()
        minimumSpareBalanceInThePeriod = balance

        if params.PRINT_LIQUIDITY:
            self.print_liquidity()

        # 1. Firesell to meet more immediate matured requests
        # We look at timesteps between now and the time delay of PullFunding.
        for timeIndex in range(self.model.parameters.TIMESTEPS_TO_PAY):
            balance = self._analyze_expected_balance_sheet(
                balance, timeIndex, cashInflows, cashCommitments,
                self.sell_assets_proportionally)
            minimumSpareBalanceInThePeriod = min(minimumSpareBalanceInThePeriod, balance)
        if balance >= 0:
            logging.debug(
                f"We can meet our cash commitments in the next {params.TIMESTEPS_TO_PAY}"
                f" timesteps, and we will have a spare balance of {balance}\n"
                f"Our minimum spare balance in the period will be {minimumSpareBalanceInThePeriod}")

        # 1b HF meet future margin call obligations or default
        # This is only required when hfs are turned on
        if not self.isaBank:
            self.prepare_future_margin_call()

        # If CET1E becomes negative as a result of fulfiling obligation, do not do anything anymore
        # Bank-only
        if hasattr(self, 'get_CET1E'):
            CET1E = self.get_CET1E()
            if CET1E < 0:
                return CET1E
        else:
            CET1E = None

        # 2. Raise liquidity to meet less immediate matured requests
        for timeIndex in range(self.model.parameters.TIMESTEPS_TO_PAY, len(cashCommitments)):
            balance = self._analyze_expected_balance_sheet(
                balance, timeIndex, cashInflows, cashCommitments,
                self.raise_liquidity_with_pecking_order)
            minimumSpareBalanceInThePeriod = min(minimumSpareBalanceInThePeriod, balance)

        if use_LEVERAGE:
            # 3. Pay off liabilities to delever
            # accuracy note: step 1 and 2 do not affect CET1E except the decrease
            # caused by price loss. Taking into account of price loss would require a huge
            # change in the code beyond the features provided by economicsl.
            amountToDelever = self.leverage_constraint.get_amount_to_delever()
            deLever = min(
                minimumSpareBalanceInThePeriod,
                self.get_ue_cash() - self.get_cash_buffer(),
                amountToDelever)
            if deLever > 0:
                deLever = pay_off_liabilities(self, deLever)
                amountToDelever -= deLever
            balance -= deLever

            # 4. Raise liquidity to delever later
            # We will use up all our remaining liquidity to delever
            # in order to meet our long-term cash commitments and non-urgent liquidity needs
            if balance < amountToDelever:
                balance += self.raise_liquidity_with_pecking_order(amountToDelever - balance)

        # Each class that inherits from LeveragedInst will have a
        # follow-up to the SPDA. In particular, the Bank will have
        # 2 more steps, the HF will have 1 more step. The CET1E is
        # returned here for caching purpose.
        return CET1E

    def _get_decomposed_sellasset_actions(self):
        # This is used only in RWA targeting in raise_liquidity_with_pecking_order_on_RWA
        sa_actions = self.get_all_actions_of_type(SellAsset)
        cbas = []
        otas = []
        eqas = []
        _corpbonds = self.model.parameters.corpbonds_dict.values()
        _equities = self.model.parameters.equities_dict.values()
        _otradables = self.model.parameters.othertradables_dict.values()
        for saa in sa_actions:
            if saa.asset.assetType in _corpbonds:
                cbas.append(saa)
            elif saa.asset.assetType in _equities:
                eqas.append(saa)
            elif saa.asset.assetType in _otradables:
                otas.append(saa)
        return cbas, otas, eqas

    def raise_liquidity_with_pecking_order_on_RWA(self, CET1E, balance=0):
        """
        This is an action with pecking order of:
        1. pull funding
           1.1 interbank pf
           1.2 reverse-repo pf
        2. tradable
           2.1 corp bonds
           2.2 other tradable
           2.3 equities
        """
        # Pecking orders
        _raised = 0
        interbank_RWA_weight = self.RWA_weights['loan']
        repo_RWA_weight = self.RWA_weights['repo']
        corpbond_RWA_weight = self.RWA_weights['corpbonds']
        eq_RWA_weight = self.RWA_weights['equities']
        otradable_RWA_weight = self.RWA_weights['othertradables']
        rwa = self.rwa_constraint.get_RWA()
        assert CET1E >= 0, CET1E
        assert rwa >= 0, rwa

        def _perform_on_one_type(_rwa, weight, actions, __raised):
            assert _rwa > 0, _rwa
            if weight == 0:
                return _rwa, __raised, False
            _x = (_rwa - CET1E / self.RWCR_target) / weight
            # maybe _rwa is negative
            if -5 * eps < _x < 0:
                # negligible amount
                assert_rwa(_rwa)
                return _rwa, __raised, True
            assert _x >= 0, (_x, self.get_RWA_ratio(), self.RWCR_target)
            if _x > 0:
                amount = perform_proportionally(actions, _x)
                is_enough = (_x <= 0) or isequal_float(amount, _x)
                _rwa -= amount * weight
                if is_enough:
                    assert_rwa(_rwa)
                return _rwa, __raised + amount, is_enough

        def assert_rwa(rwa):
            # see equation 35 of the foundation paper
            rwcr = CET1E / rwa
            assert isequal_float(rwcr, self.RWCR_target), (rwcr, self.RWCR_target)

        weight_actions = []
        if self.model.parameters.PREDEFAULT_PULLFUNDING_CONTAGION:
            pf_actions = self.get_all_actions_of_type(PullFunding)
            interbank_pfas = []
            repo_pfas = []
            for pfa in pf_actions:
                if pfa.loan.ctype == 'Repo':
                    repo_pfas.append(pfa)
                else:
                    interbank_pfas.append(pfa)

            # 1. interbank asset
            # 2. reverse-repo
            weight_actions += [(interbank_RWA_weight, interbank_pfas), (repo_RWA_weight, repo_pfas)]

        # tradable assets
        # 3. corp bond
        # 4. other tradable
        # 5. equities
        cbas, otas, eqas = self._get_decomposed_sellasset_actions()
        weight_actions += [(corpbond_RWA_weight, cbas), (otradable_RWA_weight, otas), (eq_RWA_weight, eqas)]

        for w, a in weight_actions:
            rwa, _raised, is_enough = _perform_on_one_type(rwa, w, a, _raised)
            if is_enough:
                return _raised

        return _raised

    def act_fulfil_contractual_obligations(self):
        if not self.is_alive():
            logging.debug(f"{self.get_name()} cannot act. I'm crucified, dead and buried, and have descended into hell.")
            return

        try:
            # Pay matured cash commitments or default.
            self.pay_matured_cash_commitments_or_default()
        except DefaultException:
            self.handle_default()

    def choose_actions(self):
        if not self.isaBank:
            # only hedgefunds do this
            # see https://resilience.zulipchat.com/#narrow/stream/122180-SimulationsOrganised/subject/FF2/near/135901302
            self.fulfil_margin_calls_or_default()

        params = self.model.parameters
        PREDEFAULT_CONTAGION = params.PREDEFAULT_FIRESALE_CONTAGION or params.PREDEFAULT_PULLFUNDING_CONTAGION
        if PREDEFAULT_CONTAGION:
            # 1-6. ST PATRICK DAY'S ALGORITHM
            self.perform_liquidity_management()

# Every Bank has a BankBehaviour.
class Bank(LeveragedInst):
    def __init__(self, name, model):
        super().__init__(name, model)
        self.leverage_constraint = BankLeverageConstraint(self)
        self.lcr_constraint = LCR_Constraint(self)
        self._lcrAtDefault = 0.0
        self.rwa_constraint = RWA_Constraint(self)

    def init(self, assets, liabilities):
        super().init(assets, liabilities)

    def get_leverage(self, cached_equity=None):
        """
        Bank uses T1C (i.e. CET1E + AT1E) as its numerator instead of book equity,
        and leverage exposure instead of total asset
        """
        A = self.get_ledger().get_asset_valuation()
        lev_exposure = self.leverage_constraint.get_leverage_denominator(A)
        if cached_equity is None:
            L = self.get_ledger().get_liability_valuation()
            CET1E = self.get_CET1E(A - L)
        else:
            CET1E = self.get_CET1E(cached_equity)
        return (CET1E + self.AT1E) / lev_exposure

    def get_leverage_distance(self):
        """
        Return the distance between the current leverage and leverage minimum
        """
        return self.get_leverage() - self.model.parameters.BANK_LEVERAGE_MIN

    def get_RWA_ratio_distance(self):
        return self.get_RWA_ratio() - self.rwa_constraint.get_RWCR_min()

    def get_leverage_distance_to_action(self):
        """
        Return the distance between the current leverage and leverage buffer
        """
        return self.get_leverage() - self.model.parameters.BANK_LEVERAGE_BUFFER

    def get_CET1E(self, cached_equity=None):
        if cached_equity is None:
            E = self.get_equity_valuation()
        else:
            E = cached_equity
        return E - (self.AT1E + self.T2C) - self.DeltaE

    def get_cash_buffer(self):
        return self.lcr_constraint.get_cash_buffer()

    def get_HQLA_target(self, den=None):
        return self.lcr_constraint.get_HQLA_target(den)

    def get_LCR(self):
        return self.lcr_constraint.get_LCR() if self.is_alive() else self._lcrAtDefault

    def print_balance_sheet(self):
        super().print_balance_sheet()
        print("Risk Weighted Asset ratio: %.2f%%" % (self.rwa_constraint.get_RWA_ratio() * 100.0))
        print("LCR is: %.2f%%" % (self.get_LCR() * 100))

    def get_RWA_ratio(self, cached_equity=None):
        return self.rwa_constraint.get_RWA_ratio(cached_equity)

    def trigger_default(self):
        super().trigger_default()

        cash_raised = self.get_cash()
        # The ordering is loans liquidation, firesale, pullfunding (reverse
        # repo then interbank), but this ordering does not affect the result
        # in any way

        if self.model.parameters.POSTDEFAULT_FIRESALE_CONTAGION:
            amount_tobe_sold = self.sell_assets_proportionally()
            cash_raised += amount_tobe_sold

        if self.model.parameters.POSTDEFAULT_PULLFUNDING_CONTAGION:
            self.availableActions = self.get_available_actions()
            pf_actions = self.get_all_actions_of_type(PullFunding)

            amount_tobe_pulled = perform_proportionally(pf_actions)
            cash_raised += amount_tobe_pulled

        if self.model.parameters.ENDOGENOUS_LGD_ON:
            # calculating endogenous LGD
            print("Note: make sure N is sufficiently large (previous run requires it to be at least 100)")
            L = self.get_ledger().get_liability_valuation()
            self.endogenous_LGD = max(0, 1 - (cash_raised / L))

        logging.debug("Liquidate all loans (in the liability side).")
        loans = self.get_ledger().get_liabilities_of_type(Loan)
        repos = self.get_ledger().get_liabilities_of_type(Repo)
        others = self.get_ledger().get_liabilities_of_type(Other)
        for c in (loans + repos + others):
            c.liquidate()

    def is_insolvent(self):
        params = self.model.parameters
        E = self.get_equity_valuation()
        is_rwa_insolvent = params.BANK_RWA_ON and self.rwa_constraint.is_insolvent(E)
        is_lev_insolvent = params.BANK_LEVERAGE_ON and self.leverage_constraint.is_insolvent(E)
        return is_rwa_insolvent or is_lev_insolvent

    def choose_actions(self):
        params = self.model.parameters

        # If I'm insolvent, default.
        if params.LIQUIDATION_CONTAGION:
            if self.is_insolvent():
                logging.debug("DEFAULT DUE TO INSOLVENCY.")
                raise DefaultException(self, DefaultException.TypeOfDefault.SOLVENCY)

        super().choose_actions()

    def perform_liquidity_management(self):
        """
        Continuation of St. Patrick Day's Algorithm for bank
        """
        # CET1E is returned here in order to cache its
        # computation
        CET1E = super().perform_liquidity_management()
        if CET1E < 0:
            return

        params = self.model.parameters
        use_RWA = params.BANK_RWA_ON
        use_LCR = params.BANK_LCR_ON

        # 5. Raise liquidity to reach RWCR target
        cash_raised_RWA = 0
        if use_RWA and self.rwa_constraint.is_below_buffer():
            cash_raised_RWA = self.raise_liquidity_with_pecking_order_on_RWA(CET1E)

        # 6. Raise liquidity to reach LCR target
        if use_LCR:
            den = self.lcr_constraint.get_LCR_denominator()
            HQLA = self.lcr_constraint.get_HQLA(cash_raised_RWA)
            if HQLA / den < params.BANK_LCR_BUFFER:
                # We expect our HQLA
                # in the end to be below buffer level.
                # We will replenish to the target of
                # self.get_HQLA_target()
                liquidityToRaise = self.get_HQLA_target(den) - HQLA
                self.raise_liquidity_with_pecking_order(liquidityToRaise)

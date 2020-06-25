# cython: infer_types=True
import logging

from ..actions import PayLoan, PullFunding
from economicsl.contract import Contract
from ..parameters import eps


class Loan(Contract):
    __slots__ = 'principal', 'fundingAlreadyPulled', 'parameters', '_pullfunding', '_payloan'
    ctype = 'Loan'

    def __init__(self, assetParty, liabilityParty, principal):
        super().__init__(assetParty, liabilityParty)
        _model = (assetParty or liabilityParty).model
        self.parameters = _model.parameters
        self.principal = principal
        self.fundingAlreadyPulled = 0
        # PERF for caching purpose
        self._pullfunding = PullFunding(assetParty, self)
        self._payloan = PayLoan(liabilityParty, self)

    def get_LCR_weight(self):
        return self.parameters.INTERBANK_LCR

    def get_name(self):
        _from = "external node" if self.assetParty is None else self.assetParty.get_name()
        _to = "external node" if self.liabilityParty is None else self.liabilityParty.get_name()
        return f"Loan from {_from} to {_to}"

    def pay_loan(self, amount):
        # update the amount required to be paid because it could have decreased due to bail-in
        amount = min(amount, self.get_notional())

        if self.liabilityParty is not None:
            self.liabilityParty.pay_liability(amount, self)
            self.liabilityParty.get_ledger().subtract_cash(amount)
            if self.assetParty is not None:
                # TODO fix accounting where assetParty does pull_funding
                self.liabilityParty.send_cash(self.assetParty, amount)
        #if self.assetParty is not None:
        elif self.assetParty is not None:
            # the case when external node pays back to asset party, which
            # happens instantaneously
            self.assetParty.get_ledger().pull_funding(amount, self)
            self.assetParty.get_ledger().add_cash(amount)
        self.reduce_principal(amount)

    def reduce_principal(self, amount):
        notional = self.get_notional()
        assert (notional - amount) >= -eps, (notional, amount)
        self.principal -= amount
        self.principal = abs(self.principal)  # round off floating error

        if self.principal < 0.01:
            logging.debug("This loan between " + (self.assetParty.get_name() if self.assetParty else 'None') + ' and ' + (self.liabilityParty.get_name() if self.liabilityParty else 'None') + " has been fully repaid.")
            # TODO: Destroy the loan

    def get_action(self, me):
        if self.assetParty == me:
            return self._pullfunding
        elif self.liabilityParty == me:
            return self._payloan

    def is_eligible(self, me):
        notional = self.get_notional()
        asset_alive = self.assetParty is None or self.assetParty.alive
        liability_alive = self.liabilityParty is None or self.liabilityParty.alive
        return (notional > 0) and (notional > self.get_funding_already_pulled()) and asset_alive and liability_alive

    def get_notional(self):
        return self.principal

    def get_valuation(self, side):
        # In general, the valuation of a contract may differ from its
        # notional depending on whether it is computed from the asset side or
        # liability side
        return self.get_notional()

    def liquidate(self):
        if self.assetParty is None:
            return
        if self.parameters.ENDOGENOUS_LGD_ON:
            LGD = self.liabilityParty.endogenous_LGD
        else:
            LGD = self.parameters.INTERBANK_LOSS_GIVEN_DEFAULT
        notional = self.get_notional()
        # TODO uncomment this for correct accounting
        # NOTE: the ledger keeps track of valuation, not
        # notional!
        # self.assetParty.get_ledger().devalue_asset(self, notional)
        self.assetParty.add_cash(notional * (1.0 - LGD))
        # TODO uncomment this for correct accounting
        # NOTE: the ledger keeps track of valuation, not
        # notional!
        # self.liabilityParty.get_ledger().devalue_liability(self, notional)
        self.fundingAlreadyPulled = 0
        self.principal = 0.0

    def increase_funding_pulled(self, fundingPulled):
        self.fundingAlreadyPulled += fundingPulled

    def reduce_funding_pulled(self, amount):
        self.fundingAlreadyPulled -= amount
        self.fundingAlreadyPulled = max(0, self.fundingAlreadyPulled)

    def get_funding_already_pulled(self):
        return self.fundingAlreadyPulled

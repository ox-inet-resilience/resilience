import pytest
from economicsl import Simulation

from resilience.agents import Bank
from resilience.contracts import Deposit
from resilience.markets import AssetMarket
from resilience.parameters import Parameters, enum

Parameters.AssetType = enum(GOV_BONDS1=1, CORPORATE_BONDS1=2, EQUITIES1=3, OTHERTRADABLE1=4, EXTERNAL1=5, EXTERNAL2=6, EXTERNAL3=7)
Parameters.PRICE_IMPACTS = None
Parameters.INITIAL_HAIRCUTS = {}
Parameters.RWA_WEIGHTS_GROUPED = {
    'corpbonds': 1.00,
    'govbonds': 0.00,
    'equities': 0.75,
    'othertradables': 1.00,  # same as corpbonds
    'loan': 0.4,
    'repo': 0.1,
    'external': 0.35,
    'other': 0,
}
Parameters.govbonds_dict = {'GOV_BONDS1': 1}
Parameters.corpbonds_dict = {'CORP_BONDS1': 2}
Parameters.equities_dict = {'EQUITIES1': 3}
Parameters.othertradables_dict = {'OTHERTRADABLE1': 4}

def set_constraints(rwa=False, lev=False, lcr=False):
    Parameters.PREDEFAULT_FIRESALE_CONTAGION = True
    Parameters.BANK_RWA_ON = rwa
    Parameters.BANK_LEVERAGE_ON = lev
    Parameters.BANK_LCR_ON = lcr

class SimpleModel:
    def __init__(self):
        self.simulation = Simulation()
        self.parameters = Parameters
        self.assetMarket = AssetMarket(self)

@pytest.fixture
def bank():
    model = SimpleModel()
    b = Bank('test bank', model)
    _tradable_array = [2]
    # TODO remove long term unsecured
    b.init(
        assets=(1, _tradable_array, _tradable_array, _tradable_array, _tradable_array, 2),
        liabilities=(10.2, 0)
    )
    b.DeltaA = 0
    b.AT1E = 0
    b.T2C = 0
    b.DeltaE = 0
    b.RWA_weights = dict(Parameters.RWA_WEIGHTS_GROUPED)
    return b

@pytest.mark.usefixtures("bank")
class TestBank:
    def test_get_leverage(self, bank):
        assert bank.get_leverage() == pytest.approx(0.07272727272727272727)

    def test_get_RWA_ratio(self, bank):
        assert bank.get_RWA_ratio() == pytest.approx(0.14545454545454558374)

    def test_get_LCR(self, bank):
        bank.LCR_den_initial = bank.lcr_constraint.get_HQLA() / 1.2
        assert bank.get_LCR() == pytest.approx(1.2)

    def check_ratios(self, bank, rwa=None, lev=None, lcr=None):
        if rwa:
            assert bank.get_RWA_ratio() == pytest.approx(rwa)
        if lev:
            assert bank.get_leverage() == pytest.approx(lev)
        if lcr:
            assert bank.get_LCR() == pytest.approx(lcr)

    def apply_shock(self, bank):
        # apply shock to deposit
        bank.get_ledger().get_liabilities_of_type(Deposit)[0].principal = 10.5
        assert bank.get_leverage() == pytest.approx(0.0454545454545454545)
        assert bank.get_RWA_ratio() == pytest.approx(0.09090909090909090909)

    def test_act_lev_only(self, bank):
        set_constraints(0, 1, 0)

        self.apply_shock(bank)

        # act
        bank.act()
        self.check_ratios(bank, lev=0.05)

    def test_act_rwa_only(self, bank):
        set_constraints(1, 0, 0)

        bank.RWCR_buffer = 0.1
        bank.RWCR_target = 0.145

        self.apply_shock(bank)

        # act
        bank.act()
        # make sure that RWCR target is reached
        self.check_ratios(bank, rwa=bank.RWCR_target, lev=0.045454545454545454547)

    def test_act_lcr_only(self, bank):
        set_constraints(0, 0, 1)
        # set LCR parameters
        bank.LCR_den_initial = bank.lcr_constraint.get_HQLA() / 1.2

        self.apply_shock(bank)
        # TODO
        # apply shock to gov bond

        # act
        bank.act()
        self.check_ratios(bank, rwa=0.09090909090909090909, lev=0.045454545454545454547, lcr=1.2)

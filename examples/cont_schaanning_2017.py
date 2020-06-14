import random
from collections import defaultdict

from economicsl import Simulation
from resilience.markets import AssetMarket
from resilience.agents import Bank
from resilience.contracts import Deposit, Other, AssetCollateral
from resilience.parameters import Parameters as defaultparam

NBANKS = 48
def get_extent_of_systemic_event(out):
    # See Gai-Kapadia 2010
    eose = sum(out) / NBANKS
    if eose < 0.05:
        return 0
    return eose

class AssetType:
    GOV_BONDS1 = 1
    CORPORATE_BONDS1 = 2
    EXTERNAL1 = 422
    EXTERNAL2 = 423
    EXTERNAL3 = 424

N_GOV_BONDS = 1
N_CORP_BONDS = 1
govbonds_dict = {f'GOV_BONDS{i}': i for i in range(1, N_GOV_BONDS + 1)}
corpbonds_dict = {f'CORPORATE_BONDS{i}': (N_GOV_BONDS + i) for i in range(1, N_CORP_BONDS + 1)}
class Parameters(defaultparam):
    INITIAL_SHOCK = 0.4
    BANK_LEVERAGE_MIN = 0.03
    BANK_LEVERAGE_BUFFER = 0.04
    BANK_LEVERAGE_TARGET = 0.05
    ASSET_TO_SHOCK = AssetType.GOV_BONDS1
    SIMULATION_TIMESTEPS = 6
    PRICE_IMPACTS = defaultdict(lambda: 0.05)
    BANK_RWA_EXCESS_TARGET = 0.01

    INITIAL_HAIRCUTS = {
        **{k: 0.04 for k in corpbonds_dict.values()},
        **{k: 0.02 for k in govbonds_dict.values()},
    }
    AssetType = AssetType

    govbonds_dict = govbonds_dict
    corpbonds_dict = corpbonds_dict
    equities_dict = {}
    othertradables_dict = {}

    # Resilience parameters
    FUNDING_CONTAGION_INTERBANK = True
    PREDEFAULT_FIRESALE_CONTAGION = True
    PREDEFAULT_PULLFUNDING_CONTAGION = True
    POSTDEFAULT_FIRESALE_CONTAGION = True
    POSTDEFAULT_PULLFUNDING_CONTAGION = True

class Model:
    def __init__(self):
        self.simulation = None
        self.parameters = Parameters

    def get_time(self):
        return self.simulation.get_time()

    def apply_initial_shock(self, assetType, fraction):
        """ creates an initial shock, by decreasing
            the prices on the asset market
        """
        new_price = self.assetMarket.get_price(assetType) * (1.0 - fraction)
        self.assetMarket.set_price(assetType, new_price)
        for agent in self.allAgents:
            for asset in agent.get_ledger().get_assets_of_type(AssetCollateral):
                if asset.get_asset_type() == assetType:
                    asset.update_price()

    def devalueCommonAsset(self, assetType, priceLost):
        """ devaluates a common asset for all agents """
        for agent in self.allAgents:
            agent.devalue_asset_collateral_of_type(assetType, priceLost)

    def initialize(self):
        self.simulation = Simulation()
        self.allAgents = []
        self.assetMarket = AssetMarket(self)
        with open('EBA_2018.csv', 'r') as data:
            self.bank_balancesheets = data.read().strip().split('\n')[1:]
        for bs in self.bank_balancesheets:
            row = bs.split(' ')
            bank_name, CET1E, leverage, debt_sec, gov_bonds = row
            bank = Bank(bank_name, self)
            debt_sec = float(debt_sec)
            gov_bonds = eval(gov_bonds)
            CET1E = float(CET1E)
            corp_bonds = debt_sec - gov_bonds
            asset = CET1E / (float(leverage) / 100)
            cash = 0.05 * asset
            liability = asset - CET1E
            other_asset = asset - debt_sec - cash
            loan = other_liability = liability / 2
            longTerm = 0
            bank.init(
                assets=(cash, [], [corp_bonds], [gov_bonds], [], other_asset),
                liabilities=(0, longTerm))
            # Other liability and Deposit are separated from init because
            # sometimes they are replaced with their bailin-enabled equivalent.
            bank.add(Other(None, bank, other_liability))
            bank.add(Deposit(None, bank, loan))
            bank.AT1E = 0
            bank.T2C = 0
            bank.DeltaE = 0
            bank.RWA_weights = {
                'corpbonds': 1.00,
                'govbonds': 0.00,
                'equities': 0.75,
                'othertradables': 1.00,  # same as corpbonds
                'loan': 0.4,
                'repo': 0.1,
                'external': 0.35,
                'other': 0.01,
            }
            RHO_M = 0.045
            # This is calculated from average of each bank's data rho_CB. The
            # average is used to simplify this demonstration code.
            rho_CB = 0.039375
            bank.RWCR_buffer = RHO_M + 0.5 * rho_CB
            bank.RWCR_target = bank.RWCR_buffer + Parameters.BANK_RWA_EXCESS_TARGET
            self.assetMarket.total_quantities[AssetType.GOV_BONDS1] += gov_bonds
            self.assetMarket.total_quantities[AssetType.CORPORATE_BONDS1] += corp_bonds
            self.allAgents.append(bank)

    def run_simulation(self):
        self.apply_initial_shock(
            Parameters.ASSET_TO_SHOCK,
            Parameters.INITIAL_SHOCK)
        defaults = [0]
        total_sold = []
        while self.get_time() < Parameters.SIMULATION_TIMESTEPS:
            self.simulation.advance_time()
            self.simulation.bank_defaults_this_round = 0
            # this is an extra safeguard to ensure order independence
            random.shuffle(self.allAgents)
            self.simulation.process_postbox()
            # In most agent-based models, there is only step().  We
            # split it into step() and act() phases to ensure order
            # independence in some conditions. In the full model,
            # trigger_default() may contain a behavioural unit that
            # does pull funding.
            for agent in self.allAgents:
                agent.step()
            self.assetMarket.clear_the_market()
            for agent in self.allAgents:
                agent.act()
            defaults.append(self.simulation.bank_defaults_this_round)
            total_sold.append(
                sum(self.assetMarket.cumulative_quantities_sold.values()) /
                sum(self.assetMarket.total_quantities.values()))
        return defaults, total_sold

eu = Model()
eu.initialize()
defaults, total_sold = eu.run_simulation()
# defaults and total_sold output are for each simulation timesteps
print("Result:")
print("1. Defaults", defaults)
print("2. Total sold", total_sold)

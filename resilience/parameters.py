eps = 8e-9

def enum(**enums):
    return type('Enum', (), enums)

def isequal_float(a, b, _eps=None):
    if _eps is None:
        _eps = eps
    return abs(a - b) < _eps

class Parameters:
    # Contagion Channels
    HAIRCUT_CONTAGION = False
    INVESTOR_REDEMPTION = True
    # BANKS
    FUNDING_CONTAGION_INTERBANK = True
    PREDEFAULT_FIRESALE_CONTAGION = False
    PREDEFAULT_PULLFUNDING_CONTAGION = False
    POSTDEFAULT_FIRESALE_CONTAGION = True
    POSTDEFAULT_PULLFUNDING_CONTAGION = False

    LIQUIDATION_CONTAGION = True
    CASH_PROVIDER_RUNS = True

    TRADABLE_ASSETS_ON = False
    COMMON_ASSET_NETWORK = True

    # Printing out results
    PRINT_BALANCE_SHEETS = False
    PRINT_LIQUIDITY = False
    PRINT_MAILBOX = False

    # INTERBANK liquidity hoarding threshold
    MARGIN_CALL_ON = False
    INTERBANK_LOSS_GIVEN_DEFAULT = 1.00
    ENDOGENOUS_LGD_ON = False

    # Cash Provider
    HAIRCUT_SLOPE = 100  # 0.2
    LCR_THRESHOLD_TO_RUN = -3.0
    LEVERAGE_THRESHOLD_TO_RUN = 0.0075
    CP_FRACTION_TO_RUN = 0.3
    TRIAL_PERIOD = 5

    # Hedgefund parameters
    HF_CASH_BUFFER_AS_FRACTION_OF_ASSETS = 0.04
    HF_CASH_TARGET_AS_FRACTION_OF_ASSETS = 0.08
    HF_USE_FUNDAMENTALIST_STRATEGY = False
    # See specification of simulations for foundations of SWST write-up
    # p43 for the value of HF_LEVERAGE_TARGET
    HF_LEVERAGE_TARGET = 1 / 2.3

    # Investor
    REDEMPTIONS_C1 = 20
    REDEMPTIONS_C2 = 2
    REDEMPTIONS_FRACTION = 0.25

    # Asset-specific
    TIMESTEPS_TO_PAY = 2
    LIQUIDITY_HORIZON = 5

    TIMESTEPS_TO_REDEEM_SHARES = 2

    # LCR Weights:
    # inflows:
    # Y 0.5
    # T 0
    # I 1
    # R 1
    # O from data
    # outflows:
    # D 0.05
    # tilde-I 1
    # tilde-R 1

    # inflows
    EXTERNAL_LCR = 0.50

    # inflows/outflows
    REPO_LCR = 1.00
    INTERBANK_LCR = 1.00

    # outflows
    DEPOSITS_LCR = 0.05
    OTHER_LCR = 0.50

    BANK_LCR_BUFFER = 0.5
    BANK_LCR_EXCESS_TARGET = 0.05
    BANK_LCR_TARGET = BANK_LCR_BUFFER + BANK_LCR_EXCESS_TARGET

    BANK_RWA_ON = True  # whether to check for insolvency using RWA ratio or not
    BANK_LEVERAGE_ON = False  # whether to check for insolvency using leverage ratio or not
    BANK_LCR_ON = False
    # from Basel III leverage ratio framework paragraph 7 [1]
    # http://www.bis.org/publ/bcbs270.pdf
    # this will be set at 0.03
    #BANK_LEVERAGE_MIN = 0.00
    BANK_LEVERAGE_MIN = 0.03
    BANK_LEVERAGE_REGULATORY_MIN = 0.03
    BANK_LEVERAGE_BUFFER = 0.05
    BANK_LEVERAGE_EXCESS_TARGET = 0.01
    BANK_LEVERAGE_TARGET = BANK_LEVERAGE_BUFFER + BANK_LEVERAGE_EXCESS_TARGET
    RWCR_FLTF = 0.045  # TODO which data source and whether this is bank-only

    # CACHING
    DONOT_CACHE_NETWORK = False
    NETWORK_USE_POISSON = False

    DO_SANITY_CHECK = True

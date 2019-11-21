# 4.1 Financial Institutions

note: For simplicity of notation, the _i subscript will be ommitted unlike in the paper, unless when there are 2 indices.
TODO: sphinx this

## Balance sheet access of all institutions

- A: inst.get_ledger().get_asset_valuation()
- L: inst.get_ledger().get_liability_valuation()
- E: inst.get_equity_valuation()
- C: inst.get_cash()
- T: inst.get_asset_valuation_of(AssetCollateral)
  encumbered value: sum(a.get_encumbered_valuation() for a in inst.get_ledger().get_assets_of_type(AssetCollateral))
- T_{ia}: AssetCollateral (with AssetType MBS, EQUITIES, CORPORATE_BONDS, GOV_BONDS)

- R: inst.get_asset_valuation_of(Repo)
- R_{ij}: [r.get_valuation('A') for r in inst.get_ledger().get_assets_of_type(Repo) if r.get_liability_party() == fi_j]
- \\bar{R}: inst.get_liability_valuation_of(Repo)
- O: inst.get_asset_valuation_of(Other)
- \\bar{O}: inst.get_liability_valuation_of(Other)
- Y: inst.get_asset_valuation_of(Asset, AssetType.EXTERNAL1)

## 4.1.1 Bank only contracts
- I_i: inst.get_asset_valuation_of(Loan)
- I_{ij}: [l.get_valuation('A') for l in inst.get_ledger().get_assets_of_type(Loan) if l.get_liability_party() == bank_j]
- \\bar{I}_i: inst.get_liability_valuation_of(Loan)
- D_i: inst.get_asset_valuation_of(Deposit)

## 4.1.2 AM only
- \\eta: inst.get_net_asset_valuation()  # this is defined as A/N instead of (A-L)/N
- N: inst.getnShares()
- \\sigma_{ij}: [s.getnShares() for s in inst.get_ledger().get_assets_of_type(Shares) if s.get_liability_party() == AM_i]
- \\tilde{S_i}: \\eta * sum(\\sigma_{ij})

The following equations hold (these will just be set as the initial condition of the FIs):

Banks:
- A = C + T + I + R + Y + O (eqn 1)
- L = D + \\bar{I} + \\bar{R} + \\bar{O} (eqn 2)

Hedge Funds:
- HF A = C + T + R + O
- HF L = \\bar{R}

Asset Manager:
- A_i = C_i + T_i + O_i
- L_i = 0
- E_i = \\tilde{S_{ij}}  # see the definition of this above

Asset Manager Investor:
- AM-investor A_i = S_i
- AM-investor L_i = 0

Cash Provider:
- CP A_i = R_i

# Resilience

[![CircleCI branch](https://github.com/ox-inet-resilience/resilience/workflows/build/badge.svg)](https://github.com/ox-inet-resilience/resilience/actions/workflows/ci.yml)  
This is a library containing building blocks used in Foundations of System-Wide Stress Testing (SWST).
For the news announcement, see https://www.inet.ox.ac.uk/news/foundations-of-system-wide-financial-stress-testing-with-heterogeneous-institutions/.
For access to the working paper, see https://www.bankofengland.co.uk/working-paper/2020/foundations-of-system-wide-financial-stress-testing-with-heterogeneous-institutions.

# Usage

Requires Python 3. It is recommended to run everything within a virtualenv.
Install the library by running the following commands
```python
pip install git+https://github.com/ox-inet-resilience/resilience
```

Or if you want to reproduce the SWST paper's result, you have to install from `v0.8`
```python
pip install git+https://github.com/ox-inet-resilience/resilience@v0.8
```

Alternatively, you could `git clone` the repo and run `pip install .`.

For a self-contained introduction to the model in fewer than 1k lines of code, see https://github.com/ox-inet-resilience/firesale_stresstest.
The `firesale_stresstest` repository implements all of its building block from scratch instead of using the Resilience library.
It reproduces the result of Cont-Schaanning 2017.

For a similar implementation of `firesale_stresstest` but instead built using the Resilience building blocks, see `examples/cont_schaanning_2017.py`.

# Components

A static financial system can be represented by a multi-layered network.
The first two building blocks, financial institutions and contracts, create this.
The evolution of the financial system driven by its endogenous dynamics can be expressed by the simulation of the multi-layered network.
The latter three building blocks: constraints, markets and behaviours, come into play here.
Together these form the foundation for system-wide stress testing.

### 1. Institutions

Three types of institutions have been implemented: `Bank`, `Hedgefund`, and `AssetManager`.
The balance sheet of each of them is as follows.

Bank:
- asset: cash, tradable assets, interbank assets, reverse repos, external assets, other assets
- liability: deposits, interbank liabilities, repos, other liabilities

Hedgefund:
- asset: cash, tradable assets, other assets
- liability: repos

AssetManager:
- asset: cash, tradable assets, other assets
- liability: other liabilities

### 2. Contracts

Loan
- action: pull funding or pay loan

Deposit
- inherits from Loan
- we do not explicitly model deposits, as these are typically held between a bank and a player in the real economy.

Repo
- is a securitized loan, and inherits from Loan

TradableAsset
- action: sell asset

AssetCollateral
- inherits from TradableAsset

### 3. Constraints

- Bank leverage constraint
  - λ := CET1E / (A - DeltaA)  
    DeltaA is a constant that is the difference between initial book asset and leverage exposure as given from the data
  - Delever if `λ < λ^buffer`
  - Delever to λ^target
  - Default if `λ < λ^min`  
    When this happens, all tradable assets of a defaulted bank are liquidated.
- LCR constraint
  - Λ := HQLA / (Total net cash outflow over the next T calendar days)
- RWA constraint
  - ρ := CET1E / (Risk-weighted asset)
  - Delever if `ρ < ρ^buffer`
  - Delever to ρ^target
  - Default if `ρ < ρ^min`
- Hedge fund leverage constraint

### 4. Markets

The price of each tradable asset p_m is determined using a price impact function.
The price is a function of the net cumulative number of asset sales.
Each asset has its own price impact parameter, which determines the market liquidity of the asset.

### 5. Behaviours


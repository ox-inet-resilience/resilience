# Library containing building blocks used in Foundations of System-Wide Stress Testing

[![CircleCI branch](https://img.shields.io/circleci/project/github/ox-inet-resilience/resilience/master.svg)](https://circleci.com/gh/ox-inet-resilience/resilience)

# Usage

Requires Python 3. It is recommended to run everything within a virtualenv.
Install the library by running the following commands
```python
pip install Cython
pip install git+https://github.com/ox-inet-resilience/resilience
```

Or if you want to reproduce the paper's result, you have to install from `v0.2`
```python
pip install Cython
pip install git+https://github.com/ox-inet-resilience/resilience@v0.2
```

Alternatively, you could `git clone` the repo and run `pip install .`.

# Components

### 1. Institutions

Banks:
- asset: cash, tradable assets, interbank assets, reverse repos, external assets, other assets
- liability: deposits, interbank liabilities, repos, other liabilities

Hedge funds:
- asset: cash, tradable assets, other assets
- liability: repos

Asset managers:
- asset: cash, tradable assets, other assets
- liability: other liabilities

### 2. Contracts

### 3. Constraints

- Bank leverage constraint
- LCR constraint
- RWA constraint
- Hedge fund leverage constraint

### 4. Markets

### 5. Behaviours


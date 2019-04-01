# Library containing building blocks used in Foundations of System-Wide Stress Testing

# Usage

Requires Python 3.
Install the library by running on the root repository
```python
# Run the `git checkout` step only if you want the version used in the paper
# Otherwise, just use the latest version
git checkout tags/v0.2
python setup.py install
```

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


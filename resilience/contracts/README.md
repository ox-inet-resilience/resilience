# 4.2 Financial Contracts

4.1 Cash
- C_i (self.get_cash()) = C_i^e (self.get_encumbered_cash()) + C_i^u (self.get_ue_cash())
- C_{ij}^e = [r.cash_collateral for r in self.get_liabilities_of_type(Repo)]

4.2 Tradable Assets
- (equation 15) already in the definition of T_i
- (equation 16) T_{ia} = v_{ia}p_a
- (equation 17) T_i = T_i^e + T_i^u  # TODO

4.3 Interbank Assets and Loans
- (equation 23) TODO
- (equation 24) TODO
# See note on equation 19/20
- (equation 27 and 28) TODO same as previous equation
3.4 Repurchase Agreements
- (equation 29) reverse repo: self.get_asset_valuation_of(Repo)
- (equation 30) self.get_liability_valuation_of(Repo)
- (equation 31 and 32) TODO this is FinInst.put_more_collateral

/-! 各 claim の命題。値は引数で受ける。値を渡すのは Theorems.lean（parse_claims.py が生成する）。 -/
namespace Claims

abbrev R01_c2 (observedSha256 dataSha256 : String) : Prop := observedSha256 = dataSha256
abbrev R01_c3 (dataSha256 literatureSha256 : String) : Prop := dataSha256 = literatureSha256
abbrev R01_c1 (observedSha256 dataSha256 literatureSha256 : String) : Prop :=
  R01_c2 observedSha256 dataSha256 ∧ R01_c3 dataSha256 literatureSha256

/-- 報告値 reported が、値 value を unit の桁に四捨五入したものである。 -/
abbrev roundsTo (value reported unit : Rat) : Prop :=
  reported - unit / 2 ≤ value ∧ value < reported + unit / 2

abbrev R22_c1 (testR2 trainR2 margin : Rat) : Prop := testR2 + margin ≤ trainR2
abbrev R22_c2 (trainR2 : Rat) : Prop := roundsTo trainR2 ((554 : Rat) / 1000) ((1 : Rat) / 1000)
abbrev R22_c3 (marginAtCommit runAtCommit : Nat) : Prop := marginAtCommit < runAtCommit

end Claims

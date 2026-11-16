import Values
/-! 各 claim の命題。変数は Values.lean の値。 -/
namespace Claims
open Values

abbrev R01_c2 : Prop := observedSha256 = dataSha256
abbrev R01_c3 : Prop := dataSha256 = literatureSha256
abbrev R01_c1 : Prop := R01_c2 ∧ R01_c3

/-- 報告値 reported が、値 value を unit の桁に四捨五入したものである。 -/
abbrev roundsTo (value reported unit : Rat) : Prop :=
  reported - unit / 2 ≤ value ∧ value < reported + unit / 2

abbrev R22_c1 (margin : Rat) : Prop := testR2 + margin ≤ trainR2
abbrev R22_c2 : Prop := roundsTo trainR2 ((554 : Rat) / 1000) ((1 : Rat) / 1000)
abbrev R22_c3 : Prop := marginAtCommit < runAtCommit

end Claims

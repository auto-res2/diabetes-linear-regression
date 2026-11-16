import Values
/-! 各 claim の命題。変数は Values.lean の値。 -/
namespace Claims
open Values

abbrev R01_c2 : Prop := observedSha256 = dataSha256
abbrev R01_c3 : Prop := dataSha256 = literatureSha256
abbrev R01_c1 : Prop := R01_c2 ∧ R01_c3

end Claims

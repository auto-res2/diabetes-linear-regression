"""パーサー。claims.json を読み、検証器を呼び、Lean の値と定理のファイルを書く。"""
import json
from fractions import Fraction
from pathlib import Path

from verifiers import QUERIES

REPOSITORY = "auto-res2/diabetes-linear-regression"
FORMAL = Path(__file__).parent
LEAN_TYPE = {str: "String", bool: "Bool", int: "Nat", Fraction: "Rat"}


def lean_literal(value) -> str:
    if isinstance(value, Fraction):
        return f"(({value.numerator} : Rat) / {value.denominator})"
    return json.dumps(value) if isinstance(value, str) else str(value).lower()


def lean_proposition(formalization: dict) -> str:
    """命題名に、補完で置いた前提の値を引数として付ける。"""
    arguments = formalization.get("arguments", {})
    return " ".join([formalization["proposition_name"]]
                    + [f"({name} := {lean_literal(Fraction(value))})" for name, value in arguments.items()])


def main() -> None:
    claims = json.loads((FORMAL / "claims.json").read_text(encoding="utf-8"))
    values, answered = {}, {}
    for claim in claims:
        for name, source in claim["values"].items():
            question = json.dumps(source, sort_keys=True)
            if question not in answered:
                query = QUERIES[source["verifier"]][source["query"]]
                answered[question] = query(REPOSITORY, **source["args"])
                print(f"{source['verifier']}.{source['query']} -> {answered[question]!r}")
            if values.setdefault(name, answered[question]) != answered[question]:
                raise ValueError(f"{name} の出どころが claim によって違う値を返した")

    lines = ["/-! 検証器が返した値。parse_claims.py が生成する。手で編集しない。 -/", "namespace Values"]
    lines += [f"def {name} : {LEAN_TYPE[type(value)]} := {lean_literal(value)}" for name, value in values.items()]
    (FORMAL / "lean" / "Values.lean").write_text("\n".join(lines + ["end Values", ""]), encoding="utf-8")

    theorems = [(claim["id"], lean_proposition(claim["formalization"])) for claim in claims]
    lines = ["import Claims", "/-! 各命題を定理として閉じる。parse_claims.py が生成する。 -/", "open Claims"]
    # 有理数の比較は decide では簡約が止まるので、kernel に評価させる
    lines += [f"theorem {name}_holds : {proposition} := by decide +kernel" for name, proposition in theorems]
    lines += [f"#print axioms {name}_holds" for name, _ in theorems]
    (FORMAL / "lean" / "Theorems.lean").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

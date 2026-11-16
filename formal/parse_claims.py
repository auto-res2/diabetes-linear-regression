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


def lean_proposition(claim: dict) -> str:
    """命題名に、検証器の値（Values.lean の名前）と、補完で置いた前提の値を、引数として付ける。"""
    arguments = [f"({name} := Values.{name})" for name in claim["values"]]
    arguments += [f"({name} := {lean_literal(Fraction(value))})"
                  for name, value in claim["formalization"].get("arguments", {}).items()]
    return " ".join([claim["formalization"]["proposition_name"]] + arguments)


HEADER = ["import Values", "import Claims", "open Claims"]


def theorem(name: str, proposition: str, holds: bool) -> str:
    """命題が真である定理、または偽である（否定の）定理。有理数の比較は decide では簡約が止まるので、kernel に評価させる。"""
    statement = proposition if holds else f"¬ ({proposition})"
    return f"theorem {name}_{'holds' if holds else 'fails'} : {statement} := by decide +kernel"


def write_values() -> list[tuple[str, str]]:
    """検証器を呼んで Values.lean を書き、(claim の id, 値を入れた命題) の一覧を返す。"""
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
    return [(claim["id"], lean_proposition(claim)) for claim in claims]


def write_theorems(judged: list[tuple[str, str, bool]]) -> None:
    """判定が付いた命題を、真なら定理、偽なら否定の定理として Theorems.lean に書く。"""
    lines = HEADER + ["/-! 各命題の判定。parse_claims.py が生成する。 -/"]
    lines += [theorem(name, proposition, holds) for name, proposition, holds in judged]
    lines += [f"#print axioms {name}_{'holds' if holds else 'fails'}" for name, _, holds in judged]
    (FORMAL / "lean" / "Theorems.lean").write_text("\n".join(lines) + "\n", encoding="utf-8")

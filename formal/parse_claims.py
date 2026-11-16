"""パーサー。claims.json を読み、検証器を呼び、Lean の値と定理のファイルを書く。"""
import json
from pathlib import Path

from verifiers import QUERIES

REPOSITORY = "auto-res2/diabetes-linear-regression"
FORMAL = Path(__file__).parent
LEAN_TYPE = {str: "String", bool: "Bool", int: "Nat"}


def lean_literal(value) -> str:
    return json.dumps(value) if isinstance(value, str) else str(value).lower()


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

    names = [claim["formalization"]["proposition_name"] for claim in claims]
    lines = ["import Claims", "/-! 各命題を定理として閉じる。parse_claims.py が生成する。 -/", "open Claims"]
    lines += [f"theorem {name}_holds : {name} := by decide" for name in names]
    lines += [f"#print axioms {name}_holds" for name in names]
    (FORMAL / "lean" / "Theorems.lean").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

"""ワークフローが呼ぶ入口。宣言ファイルと claims を読んで実行する。

  python formal/cli.py run     宣言された実験を実行し、成果物にするものを run-output/ に集める
  python formal/cli.py verify  claims の値を検証器から取り、Lean で各命題を判定する
"""
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

FORMAL = Path(__file__).parent
RUN_OUTPUT = Path("run-output")


def run() -> None:
    declaration = json.loads((FORMAL / "declaration.json").read_text(encoding="utf-8"))
    subprocess.run(declaration["command"], check=True)
    # 実験の出力は outputs/ の下に写す。取得の記録と同じ場所に書かせない
    shutil.rmtree(RUN_OUTPUT, ignore_errors=True)
    for path in declaration["outputs"]:
        target = RUN_OUTPUT / "outputs" / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
    # 取得の記録は実験の後に、実験コードとは別に書く
    fetched = {url: hashlib.sha256(urllib.request.urlopen(url).read()).hexdigest()
               for url in declaration["fetch_urls"]}
    (RUN_OUTPUT / "fetched_urls.json").write_text(json.dumps(fetched, indent=2) + "\n", encoding="utf-8")


def verify() -> None:
    import parse_claims
    lean = FORMAL / "lean"
    propositions = parse_claims.write_values()
    subprocess.run(["lake", "build", "Values", "Claims"], cwd=lean, check=True)

    def proves(name: str, proposition: str, holds: bool) -> bool:
        with tempfile.NamedTemporaryFile("w", suffix=".lean", encoding="utf-8") as file:
            file.write("\n".join(parse_claims.HEADER + [parse_claims.theorem(name, proposition, holds)]) + "\n")
            file.flush()
            return subprocess.run(["lake", "env", "lean", file.name], cwd=lean, capture_output=True).returncode == 0

    # claim ごとに、真の定理を試し、通らなければ偽（否定）の定理を試す。どちらも通らなければ判定できず
    verdicts = {name: True if proves(name, proposition, True) else False if proves(name, proposition, False) else None
                for name, proposition in propositions}
    parse_claims.write_theorems([(name, proposition, verdicts[name]) for name, proposition in propositions
                                 if verdicts[name] is not None])
    subprocess.run(["lake", "build"], cwd=lean, check=True)
    for name, verdict in verdicts.items():
        print(name + ": " + {True: "真", False: "偽", None: "判定できず"}[verdict])
    # 真か偽かは研究の結果。検証として失敗なのは、判定できなかった命題があるときだけ
    if None in verdicts.values():
        sys.exit(1)


if __name__ == "__main__":
    {"run": run, "verify": verify}[sys.argv[1]]()

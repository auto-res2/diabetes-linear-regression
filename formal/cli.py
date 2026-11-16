"""ワークフローが呼ぶ入口。宣言ファイルと claims を読んで実行する。

  python formal/cli.py run     宣言された実験を実行し、成果物にするものを run-output/ に集める
  python formal/cli.py verify  claims の値を検証器から取り、Lean で各命題を判定する
"""
import hashlib
import json
import shutil
import subprocess
import sys
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
    parse_claims.main()
    subprocess.run(["lake", "build"], cwd=FORMAL / "lean", check=True)


if __name__ == "__main__":
    {"run": run, "verify": verify}[sys.argv[1]]()

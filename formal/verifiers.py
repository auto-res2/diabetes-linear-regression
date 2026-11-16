"""検証器。識別子を受け取り、値を返す。claims の形は知らない。"""
import hashlib
import io
import json
from fractions import Fraction
import re
import subprocess
import zipfile


EXPERIMENT_WORKFLOW = ".github/workflows/run_experiment.yml"


def _gh(*args: str) -> str:
    return subprocess.run(["gh", *args], check=True, capture_output=True, text=True).stdout


def _verified_run(repository: str, run: int) -> dict:
    """run が成功していて、実験のワークフローの run であることを確かめ、その記録を返す。"""
    record = json.loads(_gh("api", f"repos/{repository}/actions/runs/{run}"))
    if record["conclusion"] != "success":
        raise ValueError(f"run {run} は成功していない: {record['conclusion']}")
    if record["path"] != EXPERIMENT_WORKFLOW:
        raise ValueError(f"run {run} は実験のワークフローの run ではない: {record['path']}")
    return record


def _artifact_file(repository: str, run: int, artifact: str, path: str) -> bytes:
    """成果物がその run のもので、中身が GitHub の記録した digest と一致することを確かめ、中のファイルを返す。"""
    _verified_run(repository, run)
    artifacts = json.loads(_gh("api", f"repos/{repository}/actions/runs/{run}/artifacts"))["artifacts"]
    matches = [a for a in artifacts if a["name"] == artifact and not a["expired"]]
    if len(matches) != 1:
        raise ValueError(f"run {run} に成果物 {artifact!r} が {len(matches)} 個ある")
    archive = subprocess.run(["gh", "api", f"repos/{repository}/actions/artifacts/{matches[0]['id']}/zip"],
                             check=True, capture_output=True).stdout
    if "sha256:" + hashlib.sha256(archive).hexdigest() != matches[0]["digest"]:
        raise ValueError(f"成果物 {artifact!r} の中身が、GitHub の記録した digest と一致しない")
    return zipfile.ZipFile(io.BytesIO(archive)).read(path)


def artifact_file_sha256(repository: str, run: int, artifact: str, path: str) -> str:
    """その run の成果物にあるファイルの SHA-256。"""
    return hashlib.sha256(_artifact_file(repository, run, artifact, path)).hexdigest()


def artifact_json(repository: str, run: int, artifact: str, path: str, key: str | list[str]):
    """その run の成果物にある JSON の、キーの値。key がリストなら入れ子を順に辿る。小数は書かれた桁のままの有理数で返す。"""
    value = json.loads(_artifact_file(repository, run, artifact, path), parse_float=Fraction)
    for part in [key] if isinstance(key, str) else key:
        value = value[part]
    return value


def run_source_text(repository: str, run: int, path: str, pattern: str) -> str:
    """その run が実行した commit のファイルから、正規表現で取り出した文字列。"""
    commit = _verified_run(repository, run)["head_sha"]
    source = _gh("api", f"repos/{repository}/contents/{path}?ref={commit}",
                 "-H", "Accept: application/vnd.github.raw")
    matches = re.findall(pattern, source)
    if len(matches) != 1:
        raise ValueError(f"{path}@{commit}: {pattern!r} が {len(matches)} 箇所に一致した")
    return matches[0]


def _commit_position(repository: str, commit: str) -> int:
    """その commit までの履歴にある commit の数。履歴が一本なら、小さいほど前。"""
    headers = _gh("api", "-i", f"repos/{repository}/commits?sha={commit}&per_page=1")
    last_page = re.search(r'[?&]page=(\d+)>; rel="last"', headers)
    return int(last_page.group(1)) if last_page else 1


def run_commit_position(repository: str, run: int) -> int:
    """その run が実行した commit の、履歴の中での位置。"""
    commit = _verified_run(repository, run)["head_sha"]
    return _commit_position(repository, commit)


def json_value_commit_position(repository: str, branch: str, path: str, key: str | list) -> int:
    """その branch の JSON ファイルで、キーの値が今の値になった commit の、履歴の中での位置。"""
    commits = _gh("api", f"repos/{repository}/commits?path={path}&sha={branch}&per_page=100", "--jq", ".[].sha").split()

    def value_at(commit: str):
        value = json.loads(_gh("api", f"repos/{repository}/contents/{path}?ref={commit}",
                               "-H", "Accept: application/vnd.github.raw"))
        try:
            for part in [key] if isinstance(key, str) else key:
                value = value[part]
        except (KeyError, IndexError):
            return None
        return value

    current, declared = value_at(commits[0]), commits[0]
    for commit in commits[1:]:  # 新しい順。値が変わったところで止める
        if value_at(commit) != current:
            break
        declared = commit
    return _commit_position(repository, declared)


QUERIES = {"GitHub": {f.__name__: f for f in (artifact_file_sha256, artifact_json, run_source_text,
                                               run_commit_position, json_value_commit_position)}}

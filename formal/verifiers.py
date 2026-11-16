"""検証器。識別子を受け取り、値を返す。claims の形は知らない。"""
import hashlib
import json
from fractions import Fraction
import re
import subprocess
import tempfile
from pathlib import Path


def _gh(*args: str) -> str:
    return subprocess.run(["gh", *args], check=True, capture_output=True, text=True).stdout


def _artifact_file(repository: str, run: int, artifact: str, path: str) -> bytes:
    with tempfile.TemporaryDirectory() as directory:
        _gh("run", "download", str(run), "-R", repository, "-n", artifact, "-D", directory)
        return (Path(directory) / path).read_bytes()


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
    commit = _gh("api", f"repos/{repository}/actions/runs/{run}", "--jq", ".head_sha").strip()
    source = _gh("api", f"repos/{repository}/contents/{path}?ref={commit}",
                 "-H", "Accept: application/vnd.github.raw")
    matches = re.findall(pattern, source)
    if len(matches) != 1:
        raise ValueError(f"{path}@{commit}: {pattern!r} が {len(matches)} 箇所に一致した")
    return matches[0]


QUERIES = {"GitHub": {f.__name__: f for f in (artifact_file_sha256, artifact_json, run_source_text)}}

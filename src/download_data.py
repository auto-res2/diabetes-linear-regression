"""糖尿病データセットを取得し、sha256 が固定値と一致することを確かめる。"""
import hashlib
import sys
import urllib.request
from pathlib import Path

DATA_URL = "https://www4.stat.ncsu.edu/~boos/var.select/diabetes.tab.txt"
DATA_SHA256 = "4733febee697862c22139cdac87478a300ce0d101593deb07ed6c0f3328a99cd"
DATA_PATH = Path("data/diabetes.tab.txt")


def download_data() -> Path:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not DATA_PATH.exists():
        urllib.request.urlretrieve(DATA_URL, DATA_PATH)
    actual = hashlib.sha256(DATA_PATH.read_bytes()).hexdigest()
    if actual != DATA_SHA256:
        sys.exit(f"sha256 が一致しない: {actual}")
    return DATA_PATH


if __name__ == "__main__":
    print(download_data())

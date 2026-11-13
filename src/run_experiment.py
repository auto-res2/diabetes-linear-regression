"""糖尿病データセットに線形回帰を当てはめ、指標を results/metrics.json に書く。"""
import json
from pathlib import Path

import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

from download_data import DATA_SHA256, DATA_URL, download_data

TEST_SIZE = 0.2
SEED = 0
RESULTS_PATH = Path("results/metrics.json")


def metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    mse = float(mean_squared_error(y_true, y_pred))
    return {
        "mse": mse,
        "rmse": mse**0.5,
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "r2": float(r2_score(y_true, y_pred)),
    }


def main() -> None:
    table = np.loadtxt(download_data(), skiprows=1)
    features, target = table[:, :-1], table[:, -1]
    x_train, x_test, y_train, y_test = train_test_split(
        features, target, test_size=TEST_SIZE, random_state=SEED
    )
    model = LinearRegression().fit(x_train, y_train)
    result = {
        "data": {"url": DATA_URL, "sha256": DATA_SHA256,
                 "n_samples": int(len(target)), "n_features": int(features.shape[1])},
        "split": {"test_size": TEST_SIZE, "seed": SEED,
                  "n_train": int(len(y_train)), "n_test": int(len(y_test))},
        "target": {"mean": float(target.mean()), "std": float(target.std())},
        "train": metrics(y_train, model.predict(x_train)),
        "test": metrics(y_test, model.predict(x_test)),
    }
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

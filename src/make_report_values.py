"""results/metrics.json の値を、レポートが読み込む LaTeX のマクロに書き出す。"""
import json
from pathlib import Path

result = json.loads(Path("results/metrics.json").read_text())
lines = [
    f"\\newcommand{{\\NSamples}}{{{result['data']['n_samples']}}}",
    f"\\newcommand{{\\NFeatures}}{{{result['data']['n_features']}}}",
    f"\\newcommand{{\\NTrain}}{{{result['split']['n_train']}}}",
    f"\\newcommand{{\\NTest}}{{{result['split']['n_test']}}}",
    f"\\newcommand{{\\Seed}}{{{result['split']['seed']}}}",
    f"\\newcommand{{\\TargetMean}}{{{result['target']['mean']:.1f}}}",
    f"\\newcommand{{\\TargetStd}}{{{result['target']['std']:.1f}}}",
]
for split, name in (("train", "Train"), ("test", "Test")):
    m = result[split]
    lines += [
        f"\\newcommand{{\\{name}Mse}}{{{m['mse']:.1f}}}",
        f"\\newcommand{{\\{name}Rmse}}{{{m['rmse']:.1f}}}",
        f"\\newcommand{{\\{name}Mae}}{{{m['mae']:.1f}}}",
        f"\\newcommand{{\\{name}Rsq}}{{{m['r2']:.3f}}}",
    ]
env = result["environment"]
lines += [
    f"\\newcommand{{\\CpuModel}}{{{env['cpu_model'].replace('(R)', '').replace('(TM)', '').replace('CPU @ ', '')}}}",
    f"\\newcommand{{\\CpuCores}}{{{env['cpu_logical_cores']}}}",
    f"\\newcommand{{\\MemoryGib}}{{{env['memory_gib']}}}",
    f"\\newcommand{{\\PythonVersion}}{{{env['python']}}}",
    f"\\newcommand{{\\NumpyVersion}}{{{env['numpy']}}}",
    f"\\newcommand{{\\SklearnVersion}}{{{env['scikit_learn']}}}",
]
Path("report/values.tex").write_text("\n".join(lines) + "\n")

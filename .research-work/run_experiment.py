from __future__ import annotations

import json
import platform
import time
from collections import defaultdict
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
from lime.lime_tabular import LimeTabularExplainer
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, average_precision_score, confusion_matrix, f1_score,
    precision_recall_curve, precision_score, recall_score, roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from xgboost import XGBClassifier


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
OUT = ROOT / "experiment-output"
OUT.mkdir(parents=True, exist_ok=True)
SEED = 42
CAT = ["proto", "service", "state"]
DROP = ["id", "attack_cat", "label"]


def load_data():
    train = pd.read_csv(DATA / "UNSW_NB15_training-set.csv")
    test = pd.read_csv(DATA / "UNSW_NB15_testing-set.csv")
    features = [c for c in train.columns if c not in DROP]
    numeric = [c for c in features if c not in CAT]
    return train, test, features, numeric


def build_preprocessor(numeric):
    return ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=True), CAT),
        ("num", "passthrough", numeric),
    ], sparse_threshold=1.0)


def select_model(name, X_fit, y_fit, X_val, y_val, numeric):
    if name == "Random Forest":
        candidates = [
            dict(n_estimators=220, max_depth=None, min_samples_leaf=1),
            dict(n_estimators=220, max_depth=24, min_samples_leaf=1),
            dict(n_estimators=220, max_depth=None, min_samples_leaf=2),
        ]
    else:
        candidates = [
            dict(n_estimators=260, max_depth=4, learning_rate=0.08),
            dict(n_estimators=260, max_depth=6, learning_rate=0.08),
            dict(n_estimators=360, max_depth=4, learning_rate=0.05),
        ]
    scores = []
    for params in candidates:
        prep = build_preprocessor(numeric)
        if name == "Random Forest":
            clf = RandomForestClassifier(
                **params, class_weight="balanced_subsample", max_features="sqrt",
                n_jobs=-1, random_state=SEED,
            )
        else:
            clf = XGBClassifier(
                **params, subsample=0.85, colsample_bytree=0.85,
                min_child_weight=1, reg_lambda=1.0, objective="binary:logistic",
                eval_metric="logloss", n_jobs=-1, random_state=SEED,
            )
        pipe = Pipeline([("prep", prep), ("model", clf)])
        t0 = time.perf_counter()
        pipe.fit(X_fit, y_fit)
        prob = pipe.predict_proba(X_val)[:, 1]
        fit_seconds = time.perf_counter() - t0
        best = None
        for threshold in np.linspace(0.20, 0.80, 121):
            score = f1_score(y_val, prob >= threshold)
            if best is None or score > best[0]:
                best = (float(score), float(threshold))
        scores.append({"params": params, "val_f1": best[0], "threshold": best[1], "fit_seconds": fit_seconds})
    scores.sort(key=lambda x: (x["val_f1"], -abs(x["threshold"] - 0.5)), reverse=True)
    return scores[0], scores


def metric_row(y, prob, threshold):
    pred = (prob >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, pred).ravel()
    return {
        "accuracy": accuracy_score(y, pred),
        "precision": precision_score(y, pred, zero_division=0),
        "recall": recall_score(y, pred, zero_division=0),
        "f1": f1_score(y, pred, zero_division=0),
        "fpr": fp / (fp + tn),
        "roc_auc": roc_auc_score(y, prob),
        "pr_auc": average_precision_score(y, prob),
        "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp),
        "threshold": threshold,
    }, pred


def original_feature_map(prep, numeric):
    enc = prep.named_transformers_["cat"]
    mapping = []
    for col, categories in zip(CAT, enc.categories_):
        mapping.extend([col] * len(categories))
    mapping.extend(numeric)
    return mapping, list(prep.get_feature_names_out())


def shap_matrix(explainer, X):
    values = explainer.shap_values(X, check_additivity=False, approximate=True)
    if isinstance(values, list):
        values = values[1]
    values = np.asarray(values)
    if values.ndim == 3:
        values = values[:, :, 1]
    return values


def aggregate_shap(values, mapping, original_features):
    out = np.zeros((values.shape[0], len(original_features)), dtype=float)
    idx = {f: i for i, f in enumerate(original_features)}
    for j, feature in enumerate(mapping):
        out[:, idx[feature]] += values[:, j]
    return out


def outcome_indices(y, pred, per_group=15):
    rng = np.random.default_rng(SEED)
    masks = {
        "TP": (y == 1) & (pred == 1), "TN": (y == 0) & (pred == 0),
        "FP": (y == 0) & (pred == 1), "FN": (y == 1) & (pred == 0),
    }
    selected = {}
    for key, mask in masks.items():
        ids = np.flatnonzero(np.asarray(mask))
        n = min(per_group, len(ids))
        selected[key] = np.sort(rng.choice(ids, n, replace=False)) if n else np.array([], dtype=int)
    return selected


def lime_components(train_X, features):
    matrix = train_X.copy()
    cat_names = {}
    decode = {}
    for col in CAT:
        cats = sorted(train_X[col].astype(str).unique())
        code = {v: i for i, v in enumerate(cats)}
        j = features.index(col)
        matrix[col] = train_X[col].astype(str).map(code).astype(int)
        cat_names[j] = cats
        decode[col] = cats
    matrix = matrix[features].astype(float).to_numpy()
    cat_idx = [features.index(c) for c in CAT]
    return matrix, cat_idx, cat_names, decode


def predictor_from_lime(pipe, features, decode):
    def predict(arr):
        frame = pd.DataFrame(arr, columns=features)
        for col in CAT:
            vals = np.rint(frame[col].to_numpy()).astype(int)
            names = decode[col]
            vals = np.clip(vals, 0, len(names) - 1)
            frame[col] = [names[v] for v in vals]
        for col in features:
            if col not in CAT:
                frame[col] = pd.to_numeric(frame[col], errors="coerce").fillna(0)
        return pipe.predict_proba(frame)
    return predict


def top_set(weights, features, k=5):
    order = np.argsort(np.abs(weights))[::-1][:k]
    return {features[i] for i in order}, {features[i]: float(np.sign(weights[i])) for i in order}


def jaccard(a, b):
    return len(a & b) / len(a | b) if a | b else 1.0


def run_explanations(name, pipe, train_X, test_X, y_test, pred, numeric):
    prep, model = pipe.named_steps["prep"], pipe.named_steps["model"]
    mapping, transformed_names = original_feature_map(prep, numeric)
    features = list(test_X.columns)
    chosen = outcome_indices(y_test, pred, per_group=15)
    all_ids = np.unique(np.concatenate([v for v in chosen.values() if len(v)]))
    X_trans = prep.transform(test_X.iloc[all_ids])
    if hasattr(X_trans, "toarray"):
        X_trans = X_trans.toarray()

    # TreeSHAP without a reference sample gives deterministic tree-path attributions.
    t0 = time.perf_counter()
    tree = shap.TreeExplainer(model)
    shap_values = shap_matrix(tree, X_trans)
    shap_seconds = time.perf_counter() - t0
    shap_agg = aggregate_shap(shap_values, mapping, features)
    id_to_pos = {int(v): i for i, v in enumerate(all_ids)}

    lime_train, cat_idx, cat_names, decode = lime_components(train_X, features)
    predict_fn = predictor_from_lime(pipe, features, decode)
    lime_test = test_X.copy()
    for col in CAT:
        code = {v: i for i, v in enumerate(decode[col])}
        lime_test[col] = lime_test[col].astype(str).map(code).fillna(0).astype(int)
    lime_test = lime_test[features].astype(float).to_numpy()

    result_rows, local_examples = [], []
    main_lime_explainer = LimeTabularExplainer(
        lime_train, feature_names=features, class_names=["Benign", "Attack"],
        categorical_features=cat_idx, categorical_names=cat_names,
        discretize_continuous=True, random_state=SEED,
    )
    for outcome, ids in chosen.items():
        agreement, directional, lime_times, fidelities = [], [], [], []
        for idx in ids:
            sw = shap_agg[id_to_pos[int(idx)]]
            sset, ssign = top_set(sw, features)
            t1 = time.perf_counter()
            exp = main_lime_explainer.explain_instance(lime_test[idx], predict_fn, labels=(1,), num_features=10, num_samples=1500)
            lime_times.append(time.perf_counter() - t1)
            lweights = np.zeros(len(features))
            for fidx, weight in exp.as_map()[1]:
                lweights[fidx] = weight
            lset, lsign = top_set(lweights, features)
            agreement.append(jaccard(sset, lset))
            shared = sset & lset
            directional.append(np.mean([ssign[f] == lsign[f] for f in shared]) if shared else 0.0)
            fidelities.append(float(exp.score))
            if len(local_examples) < 8:
                local_examples.append({
                    "outcome": outcome, "row": int(idx), "true": int(y_test.iloc[idx]),
                    "pred": int(pred[idx]), "probability": float(pipe.predict_proba(test_X.iloc[[idx]])[0, 1]),
                    "shap_top": sorted(((f, float(sw[features.index(f)])) for f in sset), key=lambda x: abs(x[1]), reverse=True),
                    "lime_top": sorted(((f, float(lweights[features.index(f)])) for f in lset), key=lambda x: abs(x[1]), reverse=True),
                    "lime_fidelity": float(exp.score),
                })

        # LIME stability for up to five records: three independently seeded explanations.
        stability_vals = []
        for idx in ids[:5]:
            sets = []
            for seed in [42, 142, 242]:
                ex = LimeTabularExplainer(
                    lime_train, feature_names=features, class_names=["Benign", "Attack"],
                    categorical_features=cat_idx, categorical_names=cat_names,
                    discretize_continuous=True, random_state=seed,
                ).explain_instance(lime_test[idx], predict_fn, labels=(1,), num_features=10, num_samples=1500)
                w = np.zeros(len(features))
                for fidx, weight in ex.as_map()[1]: w[fidx] = weight
                sets.append(top_set(w, features)[0])
            stability_vals.extend([jaccard(sets[0], sets[1]), jaccard(sets[0], sets[2]), jaccard(sets[1], sets[2])])

        result_rows.append({
            "model": name, "outcome": outcome, "n": int(len(ids)),
            "agreement_jaccard": float(np.median(agreement)) if agreement else None,
            "directional_agreement": float(np.median(directional)) if directional else None,
            "lime_fidelity_r2": float(np.median(fidelities)) if fidelities else None,
            "lime_stability_jaccard": float(np.median(stability_vals)) if stability_vals else None,
            "lime_median_ms": float(1000 * np.median(lime_times)) if lime_times else None,
            "shap_median_ms": float(1000 * shap_seconds / len(all_ids)) if len(all_ids) else None,
            "shap_repeatability": 1.0,
        })

    global_rank = []
    for j, f in enumerate(features):
        global_rank.append((f, float(np.mean(np.abs(shap_agg[:, j])))))
    global_rank.sort(key=lambda x: x[1], reverse=True)
    return result_rows, global_rank, local_examples


def plot_performance(all_metrics, curves):
    fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.0))
    for name, c in curves.items():
        axes[0].plot(c["fpr"], c["tpr"], label=f"{name} ({all_metrics[name]['roc_auc']:.3f})")
        axes[1].plot(c["recall_curve"], c["precision_curve"], label=f"{name} ({all_metrics[name]['pr_auc']:.3f})")
    axes[0].plot([0, 1], [0, 1], "k--", lw=.7)
    axes[0].set(xlabel="False-positive rate", ylabel="True-positive rate", title="ROC curve")
    axes[1].set(xlabel="Recall", ylabel="Precision", title="Precision-recall curve")
    axes[0].legend(fontsize=7); axes[1].legend(fontsize=7)
    labels = list(all_metrics)
    vals = [[all_metrics[n][k] for n in labels] for k in ["precision", "recall", "f1"]]
    x = np.arange(len(labels)); width = .22
    for i, (key, v) in enumerate(zip(["Precision", "Recall", "F1"], vals)):
        axes[2].bar(x + (i-1)*width, v, width, label=key)
    axes[2].set_xticks(x, ["RF", "XGB"]); axes[2].set_ylim(.7, 1.0); axes[2].set_title("Test performance"); axes[2].legend(fontsize=7)
    fig.tight_layout(); fig.savefig(OUT / "performance.png", dpi=220, bbox_inches="tight"); plt.close(fig)


def plot_global(ranks):
    fig, axes = plt.subplots(1, 2, figsize=(8.8, 3.2))
    for ax, (name, ranking) in zip(axes, ranks.items()):
        top = ranking[:10][::-1]
        ax.barh([x[0] for x in top], [x[1] for x in top], color="#35699A")
        ax.set_title(name); ax.set_xlabel("Mean |SHAP value|")
    fig.tight_layout(); fig.savefig(OUT / "global_shap.png", dpi=220, bbox_inches="tight"); plt.close(fig)


def main():
    np.random.seed(SEED)
    train, test, features, numeric = load_data()
    X, y = train[features], train["label"].astype(int)
    X_test, y_test = test[features], test["label"].astype(int)
    X_fit, X_val, y_fit, y_val = train_test_split(X, y, test_size=.20, stratify=y, random_state=SEED)
    all_metrics, curves, tuning, pipes, predictions = {}, {}, {}, {}, {}
    for name in ["Random Forest", "XGBoost"]:
        model_path = OUT / ("rf.joblib" if name == "Random Forest" else "xgb.joblib")
        if model_path.exists():
            pipe = joblib.load(model_path)
            train_s = None
            tuning[name] = [{"selected_parameters": pipe.named_steps["model"].get_params()}]
        else:
            best, trials = select_model(name, X_fit, y_fit, X_val, y_val, numeric)
            tuning[name] = trials
            prep = build_preprocessor(numeric)
            if name == "Random Forest":
                clf = RandomForestClassifier(**best["params"], class_weight="balanced_subsample", max_features="sqrt", n_jobs=-1, random_state=SEED)
            else:
                clf = XGBClassifier(**best["params"], subsample=.85, colsample_bytree=.85, min_child_weight=1, reg_lambda=1.0, objective="binary:logistic", eval_metric="logloss", n_jobs=-1, random_state=SEED)
            pipe = Pipeline([("prep", prep), ("model", clf)])
            t0 = time.perf_counter(); pipe.fit(X, y); train_s = time.perf_counter()-t0
            joblib.dump(pipe, model_path, compress=3)
        t0 = time.perf_counter(); prob = pipe.predict_proba(X_test)[:, 1]; pred_s = time.perf_counter()-t0
        metrics, pred = metric_row(y_test, prob, 0.5)
        metrics.update({"train_seconds": train_s, "prediction_seconds": pred_s, "test_n": len(test)})
        all_metrics[name] = metrics; pipes[name] = pipe; predictions[name] = pred
        fpr, tpr, _ = roc_curve(y_test, prob); pc, rc, _ = precision_recall_curve(y_test, prob)
        curves[name] = {"fpr": fpr.tolist(), "tpr": tpr.tolist(), "precision_curve": pc.tolist(), "recall_curve": rc.tolist()}
    explanation_rows, ranks, examples = [], {}, {}
    for name, pipe in pipes.items():
        rows, rank, local = run_explanations(name, pipe, X, X_test, y_test, predictions[name], numeric)
        explanation_rows.extend(rows); ranks[name] = rank; examples[name] = local
    plot_performance(all_metrics, curves); plot_global(ranks)
    pd.DataFrame(explanation_rows).to_csv(OUT / "explanation_metrics.csv", index=False)
    pd.DataFrame([
        {"model": m, "rank": i+1, "feature": f, "mean_abs_shap": v}
        for m, ranking in ranks.items() for i, (f, v) in enumerate(ranking)
    ]).to_csv(OUT / "global_shap_rankings.csv", index=False)
    report = {
        "protocol": {"seed": SEED, "training_rows": len(train), "test_rows": len(test), "features": len(features), "categorical_features": CAT, "validation_fraction": .2, "decision_threshold": .5, "lime_samples": 1500, "shap_mode": "TreeSHAP approximate"},
        "environment": {"python": platform.python_version(), "platform": platform.platform(), "sklearn": __import__('sklearn').__version__, "xgboost": __import__('xgboost').__version__, "shap": shap.__version__},
        "tuning": tuning, "metrics": all_metrics, "local_examples": examples,
    }
    (OUT / "results.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"metrics": all_metrics, "explanations": explanation_rows, "top_features": {k:v[:10] for k,v in ranks.items()}}, indent=2))


if __name__ == "__main__":
    main()

from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
from lime.lime_tabular import LimeTabularExplainer

from run_experiment import (
    CAT, DATA, DROP, OUT, SEED, aggregate_shap, lime_components,
    original_feature_map, predictor_from_lime, shap_matrix,
)

ROW = 4254  # seeded Random Forest true-positive case retained in results.json
train = pd.read_csv(DATA / "UNSW_NB15_training-set.csv")
test = pd.read_csv(DATA / "UNSW_NB15_testing-set.csv")
features = [c for c in train.columns if c not in DROP]
numeric = [c for c in features if c not in CAT]
pipe = joblib.load(OUT / "rf.joblib")
prep, model = pipe.named_steps["prep"], pipe.named_steps["model"]

prob = float(pipe.predict_proba(test.iloc[[ROW]][features])[0, 1])
pred = int(prob >= .5)
true = int(test.iloc[ROW].label)
assert (true, pred) == (1, 1)

# Real approximate TreeSHAP explanation, aggregated from one-hot columns to original attributes.
Xt = prep.transform(test.iloc[[ROW]][features])
if hasattr(Xt, "toarray"):
    Xt = Xt.toarray()
mapping, _ = original_feature_map(prep, numeric)
sv = shap_matrix(shap.TreeExplainer(model), Xt)
agg = aggregate_shap(sv, mapping, features)[0]
expected = shap.TreeExplainer(model).expected_value
base = float(np.asarray(expected).reshape(-1)[1])
explanation = shap.Explanation(values=agg, base_values=base, feature_names=features)
plt.figure(figsize=(7.2, 4.6))
shap.plots.waterfall(explanation, max_display=10, show=False)
plt.gcf().suptitle(f"Random Forest local SHAP explanation: test row {ROW}, attack score {prob:.3f}", fontsize=10, y=.995)
plt.tight_layout()
plt.savefig(OUT / "local_shap_waterfall.png", dpi=220, bbox_inches="tight")
plt.close("all")

# Real LIME explanation for the same row and fitted pipeline.
lime_train, cat_idx, cat_names, decode = lime_components(train[features], features)
predict_fn = predictor_from_lime(pipe, features, decode)
lime_test = test[features].copy()
for col in CAT:
    code = {v: i for i, v in enumerate(decode[col])}
    lime_test[col] = lime_test[col].astype(str).map(code).fillna(0).astype(int)
lime_row = lime_test.astype(float).to_numpy()[ROW]
lime = LimeTabularExplainer(
    lime_train, feature_names=features, class_names=["Benign", "Attack"],
    categorical_features=cat_idx, categorical_names=cat_names,
    discretize_continuous=True, random_state=SEED,
)
exp = lime.explain_instance(lime_row, predict_fn, labels=(1,), num_features=10, num_samples=1500)
fig = exp.as_pyplot_figure(label=1)
fig.set_size_inches(7.2, 4.5)
fig.suptitle(f"LIME explanation for the same prediction: test row {ROW}, attack score {prob:.3f}", fontsize=10, y=.995)
fig.tight_layout()
fig.savefig(OUT / "local_lime_explanation.png", dpi=220, bbox_inches="tight")
plt.close(fig)

shap_top = sorted(zip(features, agg), key=lambda x: abs(x[1]), reverse=True)[:5]
lime_top = [(features[i], float(w)) for i, w in sorted(exp.as_map()[1], key=lambda x: abs(x[1]), reverse=True)[:5]]
summary = {
    "row": ROW, "true": true, "pred": pred, "attack_score": prob,
    "shap_top": shap_top, "lime_top": lime_top, "lime_fidelity": float(exp.score),
}
(OUT / "local_case_summary.json").write_text(__import__('json').dumps(summary, indent=2), encoding="utf-8")
print(__import__('json').dumps(summary, indent=2))

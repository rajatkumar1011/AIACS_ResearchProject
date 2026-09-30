import json
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
from scipy.stats import spearmanr

from run_experiment import DATA, OUT, DROP, SEED, aggregate_shap, original_feature_map, shap_matrix

train = pd.read_csv(DATA / "UNSW_NB15_training-set.csv")
test = pd.read_csv(DATA / "UNSW_NB15_testing-set.csv")
features = [c for c in train.columns if c not in DROP]
numeric = [c for c in features if c not in ["proto", "service", "state"]]
rng = np.random.default_rng(SEED)

# A label-stratified, 1,000-record test sample for global model reliance.
global_ids = []
for label in [0, 1]:
    ids = np.flatnonzero(test.label.to_numpy() == label)
    global_ids.extend(rng.choice(ids, 500, replace=False))
global_ids = np.sort(global_ids)

ranks = {}
error_rows = []
for name, fn in [("Random Forest", "rf.joblib"), ("XGBoost", "xgb.joblib")]:
    pipe = joblib.load(OUT / fn)
    prep, model = pipe.named_steps["prep"], pipe.named_steps["model"]
    Xt = prep.transform(test.iloc[global_ids][features])
    if hasattr(Xt, "toarray"): Xt = Xt.toarray()
    values = shap_matrix(shap.TreeExplainer(model), Xt)
    mapping, _ = original_feature_map(prep, numeric)
    agg = aggregate_shap(values, mapping, features)
    ranking = sorted([(f, float(np.mean(np.abs(agg[:, j])))) for j, f in enumerate(features)], key=lambda x: x[1], reverse=True)
    ranks[name] = ranking

    prob = pipe.predict_proba(test[features])[:, 1]
    pred = (prob >= .5).astype(int)
    fn_mask = (test.label.to_numpy() == 1) & (pred == 0)
    fp_mask = (test.label.to_numpy() == 0) & (pred == 1)
    for category, count in test.loc[fn_mask, "attack_cat"].value_counts().items():
        total = int((test.attack_cat == category).sum())
        error_rows.append({"model": name, "error": "FN", "category": category, "count": int(count), "category_total": total, "miss_rate": count/total})
    benign_total = int((test.label == 0).sum())
    error_rows.append({"model": name, "error": "FP", "category": "Normal", "count": int(fp_mask.sum()), "category_total": benign_total, "miss_rate": float(fp_mask.sum() / benign_total)})

pd.DataFrame([{"model":m,"rank":i+1,"feature":f,"mean_abs_shap":v} for m,rr in ranks.items() for i,(f,v) in enumerate(rr)]).to_csv(OUT/"global_shap_rankings.csv",index=False)
pd.DataFrame(error_rows).to_csv(OUT/"error_by_attack_category.csv",index=False)

fig, axes = plt.subplots(1,2,figsize=(8.8,3.2))
for ax,(name,ranking) in zip(axes,ranks.items()):
    top=ranking[:10][::-1]
    ax.barh([x[0] for x in top],[x[1] for x in top],color="#35699A")
    ax.set_title(name); ax.set_xlabel("Mean |SHAP value|")
fig.tight_layout(); fig.savefig(OUT/"global_shap.png",dpi=220,bbox_inches="tight"); plt.close(fig)

rf_order={f:i for i,(f,_) in enumerate(ranks['Random Forest'])}
xgb_order={f:i for i,(f,_) in enumerate(ranks['XGBoost'])}
rho=float(spearmanr([rf_order[f] for f in features],[xgb_order[f] for f in features]).statistic)
top10_rf={f for f,_ in ranks['Random Forest'][:10]}; top10_xgb={f for f,_ in ranks['XGBoost'][:10]}
summary={"global_sample_n":1000,"global_sample_per_class":500,"rank_spearman":rho,"top10_jaccard":len(top10_rf&top10_xgb)/len(top10_rf|top10_xgb),"top10_shared":sorted(top10_rf&top10_xgb),"top_features":{k:v[:10] for k,v in ranks.items()}}
(OUT/"supplement.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
print(json.dumps(summary,indent=2))
print(pd.DataFrame(error_rows).to_string(index=False))

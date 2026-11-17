"""MUHU v3 preregistered CPU-only supervised text baseline.

Never trains Khipu or a clinical/genomic model. Uses only original
synthetic methodology prompts. No pickle/untrusted model code.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
from math import sqrt
from pathlib import Path
import argparse
import json
import os
import sys

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import FeatureUnion
from sklearn.linear_model import LogisticRegression
import sklearn

from research.muhu_v3.curriculum import TARGETS, canon, digest, generated, verify
from research.muhu_v3.artifact import normalize_vocabulary

ACCEPTANCE = {
    "macro_f1_min": 0.85,
    "minimum_class_recall": 0.70,
    "false_reviewable_max_rate": 0.02,
    "selective_coverage_min": 0.85,
    "internal_stress_accuracy_min": 0.75,
    "max_incomplete_ood_reviewable": 0,
}
MARGIN = 0.20
STRESS_SHA = "4e6128419199ec7af0b0973411d369162808c81ca13f9f1e79f97699e61793e3"

def vectorizer():
    return FeatureUnion([
        ("word", TfidfVectorizer(lowercase=True, analyzer="word",
            token_pattern=r"(?u)\b[\w-]+\b", ngram_range=(1, 2),
            min_df=2, max_features=20000, sublinear_tf=True)),
        ("char", TfidfVectorizer(lowercase=True, analyzer="char",
            ngram_range=(3, 5), min_df=2, max_features=20000, sublinear_tf=True))
    ])

def classify_probs(class_names, matrix):
    import numpy as np
    result=[]
    for probabilities in matrix:
        ranked=sorted(zip(class_names,probabilities),key=lambda q:(-q[1],q[0]))
        first,second=ranked[:2]
        margin=float(first[1]-second[1])
        result.append({
            "raw_guess":str(first[0]),
            "accepted_guess":str(first[0]) if margin>=MARGIN else "ABSTAIN",
            "margin":round(margin,6),
            "uncalibrated_top_probability":round(float(first[1]),6)
        })
    return result

def wilson(k,n):
    if n==0:return None
    z=1.96
    p=k/n;d=1+z*z/n
    delta=z*sqrt(p*(1-p)/n+z*z/(4*n*n))
    return [round((p+z*z/(2*n)-delta)/d,6),round((p+z*z/(2*n)+delta)/d,6)]

def evaluate(rows,predictions):
    if len(rows)!=len(predictions):raise ValueError("PREDICTION_COUNT_MISMATCH")
    n=len(rows)
    confusion={c:{v:0 for v in (*TARGETS,"ABSTAIN")} for c in TARGETS}
    majority_count=Counter(x["target_state"] for x in rows)
    raw_correct=0
    accepted_correct=0
    covered=0
    for row,p in zip(rows,predictions):
        actual=row["target_state"]
        guess=p["accepted_guess"]
        confusion[actual][guess]+=1
        raw_correct+=int(actual==p["raw_guess"])
        if guess!="ABSTAIN":
            covered+=1;accepted_correct+=int(actual==guess)
    measures={}
    for c in TARGETS:
        tp=confusion[c][c]
        n_actual=sum(confusion[c].values())
        fp=sum(confusion[t][c] for t in TARGETS if t!=c)
        fn=n_actual-tp
        precision=tp/(tp+fp) if tp+fp else 0.0
        recall=tp/n_actual if n_actual else 0.0
        f1=2*precision*recall/(precision+recall) if precision+recall else 0.0
        measures[c]={"support":n_actual,"tp":tp,"fp":fp,"fn":fn,
                     "precision":round(precision,6),"recall":round(recall,6),
                     "f1":round(f1,6)}
    false_reviewable=sum(confusion[t]["REVIEWABLE"] for t in TARGETS if t!="REVIEWABLE")
    other_support=n-majority_count["REVIEWABLE"]
    base=max(TARGETS,key=lambda c:(majority_count[c],-TARGETS.index(c)))
    return {
        "total":n,
        "raw_argmax_accuracy":round(raw_correct/n,6),
        "raw_accuracy_wilson95":wilson(raw_correct,n),
        "selective_coverage":round(covered/n,6),
        "selective_accuracy":round(accepted_correct/covered,6) if covered else None,
        "abstentions":n-covered,
        "macro_f1_with_abstentions_as_misses":round(sum(measures[c]["f1"] for c in TARGETS)/len(TARGETS),6),
        "minimum_class_recall":min(measures[c]["recall"] for c in TARGETS),
        "false_reviewable":false_reviewable,
        "false_reviewable_denominator":other_support,
        "false_reviewable_rate":round(false_reviewable/other_support,6),
        "majority_accuracy":round(majority_count[base]/n,6),
        "majority_label_on_this_partition":base,
        "per_class":measures,
        "confusion":confusion
    }

def load_jsonl(path):
    return [json.loads(s) for s in path.read_text(encoding="utf-8").splitlines() if s.strip()]

def strict_readback(public:Path,private:Path,stress:Path):
    manifest=json.loads((public/"manifest.json").read_text("utf-8"))
    if manifest.get("schema")!="szl.muhu.methodology-manifest.v3" or manifest.get("flagship_admitted") is not False:
        raise ValueError("DATA_ADMISSION_OR_SCHEMA_CHANGED")
    expected=manifest["sha256"]
    records={}
    for split in ("train","validation","test"):
        p=(public if split=="train" else private)/(split+".jsonl")
        if digest(p.read_bytes())!=expected[split]:
            raise ValueError("PARTITION_HASH_MISMATCH_"+split)
        records[split]=load_jsonl(p)
        if len(records[split])!=manifest["row_counts"][split]:
            raise ValueError("COUNT_MISMATCH_"+split)
    if digest(stress.read_bytes())!=STRESS_SHA:
        raise ValueError("PRESEALED_ADVERSARIAL_HASH_DRIFT")
    adversarial=load_jsonl(stress)
    from research.muhu_v3.curriculum import status_of
    for row in adversarial:
        if row["expected"]!="ABSTAIN_UNOBSERVED" and status_of(row["oracle_inputs"])!=row["expected"]:
            raise ValueError("STRESS_ORACLE_INCONSISTENT")
    # regeneration checks group disjointness and deterministic corpus integrity
    replay,_=generated()
    verify(replay)
    for split in replay:
        if records[split]!=replay[split]:raise ValueError("DETERMINISTIC_REPLAY_CHANGED_"+split)
    return manifest,records,adversarial

def exclusive(path:Path,raw:bytes)->str:
    with path.open("xb") as o:
        o.write(raw);o.flush();os.fsync(o.fileno())
    if path.read_bytes()!=raw:raise RuntimeError("READBACK_FAIL")
    return sha256(raw).hexdigest()

def run(public:Path,private:Path,stress:Path,out:Path):
    if out.exists():raise RuntimeError("REFUSE_EXISTING_MODEL_OUTPUT")
    manifest,records,adversarial=strict_readback(public,private,stress)
    # No group IDs, oracle input, or labels in features. Fitting only on train.
    texts=[row["input"] for row in records["train"]]
    y=[row["target_state"] for row in records["train"]]
    features=vectorizer()
    x=features.fit_transform(texts)
    estimator=LogisticRegression(C=1.0,class_weight="balanced",random_state=42,
                                  max_iter=2000,solver="lbfgs")
    estimator.fit(x,y)
    classes=[str(c) for c in estimator.classes_]
    if set(classes)!=set(TARGETS):raise ValueError("MISSING_CLASS")
    def predictions(prompts):
        return classify_probs(classes,estimator.predict_proba(features.transform(prompts)))
    results={}
    for split in ("validation","test"):
        result=predictions([r["input"] for r in records[split]])
        results[split]=evaluate(records[split],result)
    stress_normal=[r for r in adversarial if r["expected"]!="ABSTAIN_UNOBSERVED"]
    stress_unknown=[r for r in adversarial if r["expected"]=="ABSTAIN_UNOBSERVED"]
    stressed=predictions([r["prompt"] for r in stress_normal])
    stress_correct=sum(p["accepted_guess"]==row["expected"] for row,p in zip(stress_normal,stressed))
    missing_preds=predictions([r["prompt"] for r in stress_unknown])
    dangerous=sum(p["accepted_guess"]=="REVIEWABLE" for p in missing_preds)
    stress_summary={"n":len(stress_normal),"correct":stress_correct,
        "accuracy":round(stress_correct/len(stress_normal),6),
        "abstained":sum(p["accepted_guess"]=="ABSTAIN" for p in stressed),
        "ood_missing_data_n":len(stress_unknown),
        "ood_predicted_reviewable":dangerous,
        "ood_abstained":sum(p["accepted_guess"]=="ABSTAIN" for p in missing_preds),
        "stress_fixture_sha256":STRESS_SHA,
        "limitation":"Internal author-created, prespecified synthetic phrasing; not independently human-adjudicated"}
    tested=results["test"]
    gates={
      "macro_f1":tested["macro_f1_with_abstentions_as_misses"]>=ACCEPTANCE["macro_f1_min"],
      "minimum_recall":tested["minimum_class_recall"]>=ACCEPTANCE["minimum_class_recall"],
      "no_false_reviewable":tested["false_reviewable_rate"]<=ACCEPTANCE["false_reviewable_max_rate"],
      "coverage":tested["selective_coverage"]>=ACCEPTANCE["selective_coverage_min"],
      "stress_accuracy":stress_summary["accuracy"]>=ACCEPTANCE["internal_stress_accuracy_min"],
      "ood_guard":dangerous<=ACCEPTANCE["max_incomplete_ood_reviewable"],
    }
    complete=all(gates.values())
    report={
      "schema":"szl.muhu.v3.cpu_text_baseline.v1",
      "observed_utc":datetime.now(timezone.utc).isoformat(),
      "training_format":"synthetic free-text, not a language-model adapter",
      "source_manifest_sha256":sha256((public/"manifest.json").read_bytes()).hexdigest(),
      "input_train_sha256":manifest["sha256"]["train"],
      "validation_sha256":manifest["sha256"]["validation"],
      "test_sha256":manifest["sha256"]["test"],
      "training_count":len(records["train"]),
      "config":"TfidfVectorizer word (1-2) and character (3-5) + LogisticRegression lbfgs C=1, balanced, random_state=42, max_iter=2000",
      "tokenizer_feature_count":x.shape[1],
      "classes":classes,"numpy_version":np.__version__,"sklearn_version":sklearn.__version__,
      "validation":results["validation"],"test":tested,
      "internal_stress":stress_summary,
      "predeclared_acceptance":ACCEPTANCE,"gates":gates,
      "synthetic_research_gates_passed":complete,
      "flagship_training_admitted":False,"khipu_model_trained":False,
      "scientific_and_clinical_quality":"NOT_MEASURED",
      "separate_human_independent_test":"NOT_PERFORMED",
      "publication":"PRIVATE_OWNER_ONLY",
      "no_paid_hardware_used":True,
      "known_limitations":"Generator code public; group disjointness not external blindness; deterministic rules not real biology."
    }
    # Save safe, non-pickle numeric weights + vocabulary/IDF.
    out.mkdir(parents=True)
    weights=out/"numeric_weights.npz"
    np.savez_compressed(weights,coef=estimator.coef_,intercept=estimator.intercept_,
                        classes=np.array(classes,dtype="U20"),
                        idf_word=features.transformer_list[0][1].idf_,
                        idf_char=features.transformer_list[1][1].idf_)
    word=features.transformer_list[0][1]
    char=features.transformer_list[1][1]
    vocabulary={"word":normalize_vocabulary(word.vocabulary_),
                "char":normalize_vocabulary(char.vocabulary_),
                "word_spec":{"ngram_range":[1,2],"max_features":20000,
                             "min_df":2,"sublinear_tf":True},
                "char_spec":{"ngram_range":[3,5],"max_features":20000,
                             "min_df":2,"sublinear_tf":True},
                "weights_format":"numpy NPZ, allow_pickle=False",
                "clinical_use":"DENIED"}
    source_commitment={
        "model_weights_sha256":sha256(weights.read_bytes()).hexdigest(),
        "vocabulary_sha256":exclusive(out/"vocabulary.json",canon(vocabulary)),
        "report_sha256":exclusive(out/"evaluation.json",canon(report))
    }
    print(json.dumps({"state":"CPU_TEXT_BASELINE_COMPLETE_NO_FLAGSHIP_TRAINING",
        "heldout":{k:{"n":v["total"],"macro_f1":v["macro_f1_with_abstentions_as_misses"],
                     "min_recall":v["minimum_class_recall"],"false_reviewable":v["false_reviewable"],
                     "coverage":v["selective_coverage"],"majority":v["majority_accuracy"],
                     "raw_accuracy":v["raw_argmax_accuracy"]} for k,v in results.items()},
        "stress":stress_summary,"gates":gates,"quality_pass":complete,
        "output_private":str(out),"sha256":source_commitment},sort_keys=True))

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--public",type=Path,required=True)
    p.add_argument("--private",type=Path,required=True)
    p.add_argument("--stress",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    run(a.public,a.private,a.stress,a.out)

if __name__=="__main__":main()

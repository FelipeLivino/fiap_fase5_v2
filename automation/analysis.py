import hashlib
import json
import math
from sklearn.ensemble import IsolationForest

FEATURES=('systolic','diastolic','heart_rate','adherence')


def features(row):
    values=[row[k] for k in FEATURES]
    if any(not isinstance(v,(int,float)) or isinstance(v,bool) or not math.isfinite(v) for v in values):
        return None
    if any(v<=0 for v in values[:3]) or not 0<=values[3]<=1:
        return None
    return values


def train(rows):
    values=[features(row) for row in rows]
    values=[v for v in values if v is not None]
    if len(values)<30:
        raise ValueError('São necessárias pelo menos 30 amostras de treinamento válidas.')
    spec={'algorithm':'IsolationForest','n_estimators':100,'contamination':0.08,'random_state':42,
          'features':FEATURES,'training':values,'implementation':'1'}
    version=hashlib.sha256(json.dumps(spec,sort_keys=True).encode()).hexdigest()[:16]
    model=IsolationForest(n_estimators=100,contamination=0.08,random_state=42).fit(values)
    return model, version

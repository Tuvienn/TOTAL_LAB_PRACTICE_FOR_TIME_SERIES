import copy
import csv
import hashlib
import io
import json
import pytest
from practice_4.analysis.walk_forward import walk_forward, validate_evaluation, MODELS


def run(values):
    gate = {'predicted': False}
    def predict(history):
        gate['predicted'] = True
        return history[-1] if history[-1] is not None else 0
    def target(value):
        def reveal():
            assert gate['predicted']
            gate['predicted'] = False
            return value
        return reveal
    return walk_forward([1], [target(v) for v in values], predict, lambda h: True, lambda: 'fixed')


def test_prediction_precedes_reveal_and_future_mutation():
    a, b = run([2, 3, 4]), run([2, 3, 99])
    assert a['predictions'] == b['predictions'] == [1, 2, 3]
    assert run([None, 3])['history'] == [1, None, 3]
    assert run([None, 3])['metrics']['n_missing_excluded'] == 1


def test_invalid_history_and_fixed_state_and_failure():
    result = walk_forward([0], [lambda: 2, lambda: None, lambda: 3, lambda: 4], lambda h: 5, lambda h: h[-1] is not None and h[-1] != 0, lambda: 1)
    assert result['metrics']['n_input_excluded'] == 2 and result['metrics']['n_missing_excluded'] == 1 and result['metrics']['n_scored'] == 1
    with pytest.raises(ValueError): walk_forward([1], [lambda: 2], lambda h: float('nan'), lambda h: True, lambda: 1)
    state = [0]
    def mutate(h):
        state[0] += 1
        return 1
    with pytest.raises(ValueError, match='state changed'): walk_forward([1], [lambda: 2], mutate, lambda h: True, lambda: state)
    with pytest.raises(RuntimeError): walk_forward([1], [lambda: 2], lambda h: (_ for _ in ()).throw(RuntimeError()), lambda h: True, lambda: 1)


def artifacts():
    stream = io.StringIO(newline=''); fields=['schema_version','model','origin','target_timestamp','y_true_mw','y_pred_mw','split','run_id']; writer=csv.DictWriter(stream,fieldnames=fields); writer.writeheader()
    for model in MODELS: writer.writerow(dict(schema_version='1',model=model,origin='2020-01-01T00:00:00Z',target_timestamp='2020-01-01T01:00:00Z',y_true_mw='2',y_pred_mw='1',split='test',run_id='synthetic'))
    data=stream.getvalue().encode(); hashes={k:'a'*64 for k in ['canonical_sha256','split_sha256','config_sha256','preprocessor_sha256','eligibility_sha256','source_manifest_sha256']}
    m=dict(schema_version='1',run_id='synthetic',stage_id='H01',prediction_file=dict(path='outputs/results/predictions.csv',sha256=hashlib.sha256(data).hexdigest()),input_hashes=hashes,model_hashes={k:'b'*64 for k in MODELS},approval_refs={k:'synthetic approval' for k in ['evaluation_contract','model_locks','test_opening']},counts=dict(n_considered=1,n_scored=1,n_zero_excluded=0,n_missing_excluded=0,n_input_excluded=0),metrics={k:dict(mae_mw=1,rmse_mw=1,mape_percent=50,mape_null_reason=None) for k in MODELS},protocol=dict(forecast_horizon_hours=1,weights='fixed',transformations='train_fitted_fixed',update_order='predict_score_reveal'),created_at_utc='2020-01-01T00:00:00Z',limitations=[])
    return m,data


def validate(m,data,approved=True): return validate_evaluation(json.dumps(m).encode(),data,approved)


def test_schema_rejections():
    m,data=artifacts(); validate(m,data)
    with pytest.raises(ValueError): validate(m,data,False)
    for key,value in [('schema_version','2'),('counts',{}),('protocol',{}),('metrics',{}),('input_hashes',{})]:
        changed=copy.deepcopy(m); changed[key]=value
        with pytest.raises(ValueError): validate(changed,data)
    with pytest.raises(ValueError): validate(m,data+b'x')
    with pytest.raises(ValueError): validate_evaluation(b'{"schema_version":"1","schema_version":"1"}',data,True)
    changed=copy.deepcopy(m); changed['metrics']['VAR']['mape_percent']=None
    with pytest.raises(ValueError): validate(changed,data)
    lines=data.decode().splitlines(); duplicate=('\n'.join(lines+[lines[1]])+'\n').encode(); changed=copy.deepcopy(m); changed['prediction_file']['sha256']=hashlib.sha256(duplicate).hexdigest()
    with pytest.raises(ValueError): validate(changed,duplicate)
    lines[1]=lines[1].replace(',2,1,',',3,1,'); altered=('\n'.join(lines)+'\n').encode(); changed['prediction_file']['sha256']=hashlib.sha256(altered).hexdigest()
    with pytest.raises(ValueError): validate(changed,altered)



def test_schema_null_rules_header_and_versions():
    m,data=artifacts()
    for change in (lambda x: x.pop('run_id'), lambda x: x.update({'unknown': 1}), lambda x: x['counts'].update(n_scored='1')):
        bad=copy.deepcopy(m); change(bad)
        with pytest.raises(ValueError): validate(bad,data)
    altered=data.replace(b',2,1,',b',0,1,')
    m['prediction_file']['sha256']=hashlib.sha256(altered).hexdigest()
    m['counts']['n_zero_excluded']=1
    for v in m['metrics'].values(): v.update(mape_percent=None,mape_null_reason='all scored truths are zero')
    validate(m,altered)
    m['metrics']['VAR']['mape_null_reason']=None
    with pytest.raises(ValueError): validate(m,altered)
    bad=data.replace(b'schema_version,', b'schema_version,schema_version,',1)
    m,data0=artifacts(); m['prediction_file']['sha256']=hashlib.sha256(bad).hexdigest()
    with pytest.raises(ValueError): validate(m,bad)

from __future__ import annotations
import argparse,hashlib,json,sys
from pathlib import Path
from collections import Counter,defaultdict
from .core import Dataset,read_jsonl,write_json,write_jsonl,summarize,serialize
from .tokenizer import Encoder

ROOT=Path(__file__).resolve().parents[1]

def validate(d):
    errors=[];checks=Counter();scope_rows=[]
    for qid,q in d.queries.items():
        g=d.gold[qid];err=[]
        qsha=hashlib.sha256(json.dumps(q,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        if qsha!=g['binding']['query_sha256']:err.append('query subject binding mismatch')
        es={e['evidence_id']:e for e in g['evidence_units']};required={c['claim_id'] for c in g['source_claims']}
        if len(es)!=len(g['evidence_units']):err.append('duplicate evidence ID')
        for e in list(es.values())+g['related_but_not_answer_inventory']:
            try:d.check_injection(q,e['spans'])
            except Exception as ex:err.append('source '+str(ex))
            for s in e['spans']:
                checks['source_spans']+=1
                if hashlib.sha256(s['text'].encode()).hexdigest()!=s['text_sha256']:err.append('source hash mismatch')
                if d.message_round.get(s['message_id'])!=s['round_id']:err.append('round reference mismatch')
                if d.messages[s['message_id']]['conversation_id']!=s['conversation_id']:err.append('conversation mismatch')
        if g['expected_behavior']=='RETRIEVE':
            if not required or not g['sufficient_sets']:err.append('missing positive Gold')
            for p in g['sufficient_sets']:
                ids=p['evidence_ids'];checks['sufficient_sets']+=1
                if any(i not in es for i in ids):err.append('missing evidence unit');continue
                claims={c for eid in ids for c in es[eid]['claim_ids']}
                if claims!=required:err.append('incomplete/extra source requirements')
                for removed in ids:
                    checks['unit_deletions']+=1
                    left={c for eid in ids if eid!=removed for c in es[eid]['claim_ids']}
                    if required<=left:err.append('nonminimal unit set')
        elif es or g['sufficient_sets'] or required:err.append('nonretrieval task carries positive answer Gold')
        for w in g['interpretation_witnesses']:
            try:d.check_injection(q,[w]);checks['interpretation_witnesses']+=1
            except Exception as ex:err.append('witness '+str(ex))
        scope_rows.append({'query_id':qid,'source_integrity':not err,'errors':sorted(set(err))})
        if err:errors.append({'query_id':qid,'errors':sorted(set(err))})
    for key,field in [('environments','environment_id')]:
        groups=defaultdict(set)
        for g in d.gold.values():groups[g[field]].add(g['split'])
        if any(len(v)!=1 for v in groups.values()):errors.append({'split_error':key})
    counts=Counter(g['split'] for g in d.gold.values())
    return {'valid_within_structural_scope':not errors,'queries':len(d.queries),'gold':len(d.gold),'messages':len(d.messages),'rounds':len(d.rounds),
            'splits':dict(counts),'checks':dict(checks),'errors':errors,'scope_rows':scope_rows,
            'independent_semantic_reviews':0,'semantic_alternative_exhaustiveness':'not_certified','uses_author_gold':True}


def main():
    p=argparse.ArgumentParser(description='R2 v0.5.2 deterministic author-Gold evaluator')
    p.add_argument('--root',type=Path,default=ROOT)
    sub=p.add_subparsers(dest='command',required=True)
    v=sub.add_parser('validate');v.add_argument('--output',type=Path,default=ROOT/'reports/validation.json')
    s=sub.add_parser('score');s.add_argument('--predictions',type=Path,required=True);s.add_argument('--output',type=Path,required=True)
    s.add_argument('--split',choices=['all','train','dev','test'],default='all');s.add_argument('--budget',type=int,default=None)
    s.add_argument('--skip-reference-cost',action='store_true');s.add_argument('--no-bootstrap',action='store_true')
    a=p.parse_args();d=Dataset(a.root)
    validation=validate(d)
    if a.command=='validate':
        write_json(a.output,validation);print(json.dumps({k:v for k,v in validation.items() if k!='scope_rows'},ensure_ascii=False));return
    if a.budget is not None and a.budget<=0:p.error('budget must be positive, or omitted for no imposed limit')
    bad={x.get('query_id') for x in validation['errors'] if x.get('query_id')}
    if any('split_error' in x for x in validation['errors']):raise ValueError('split association is broken')
    predictions=read_jsonl(a.predictions);pm={}
    for x in predictions:
        qid=x.get('query_id')
        if not isinstance(qid,str) or qid not in d.queries:raise ValueError('unknown or missing query_id')
        if qid in pm:raise ValueError('duplicate query_id, no overwrite allowed')
        if any(k.startswith('_') for k in x):raise ValueError('reserved prediction key')
        pm[qid]=x
    qs=[qid for qid in sorted(d.queries) if a.split=='all' or d.gold[qid]['split']==a.split]
    enc=Encoder();refs={}
    if not a.skip_reference_cost:
        for qid in qs:
            g=d.gold[qid]
            if qid not in bad and 'final_injection' in pm.get(qid,{}) and g['expected_behavior']=='RETRIEVE':
                refs[qid]=min(enc.count(serialize(d.reference_items(g,s),d.messages)) for s in g['sufficient_sets'])
    rows=[]
    for qid in qs:
        if qid in bad:continue
        pred=pm.get(qid,{'query_id':qid,'action':None,'candidate_results':[],'final_injection':[],'_missing_output':True})
        rows.append(d.score_one(pred,enc,a.budget,refs.get(qid)))
    output=a.output;output.mkdir(parents=True,exist_ok=True)
    summary={'version':'R2-v0.5.2-author-reconstruction','evaluation_contract':'native-no-external-cap-v052','author_gold':True,
             'requested_queries':len(qs),'scored_queries':len(rows),'excluded_queries':len(set(qs)&bad),'explicit_token_budget':a.budget,
             'input_prediction_sha256':hashlib.sha256(a.predictions.read_bytes()).hexdigest(),
             'public_queries_sha256':hashlib.sha256((a.root/'public/queries.jsonl').read_bytes()).hexdigest(),
             'published_gold_sha256':hashlib.sha256((a.root/'gold/gold.jsonl').read_bytes()).hexdigest(),
             'tokenizer':enc.audit,'overall':summarize(rows,not a.no_bootstrap),'groups':{}}
    for field in ('split','recall_family','expected_behavior','legacy_content_type','difficulty'):
        summary['groups'][field]={value:summarize([r for r in rows if r[field]==value],False) for value in sorted({r[field] for r in rows})}
    failures=[]
    for r in rows:
        reasons=[]
        if r['expected_behavior']!='RETRIEVE' and not r['ActionAccuracy']:reasons.append('wrong_clarification_or_missing_field_decision')
        if r['candidate'] is not None and not r['candidate']['all']['SufficiencySuccess']:reasons.append('candidate_inventory_incomplete')
        if r['injection'] is not None and not r['injection']['SufficiencySuccess']:reasons.append('final_injection_incomplete')
        if r['missing_output']:reasons.append('missing_output')
        if r['errors']:reasons+=r['errors']
        if reasons:failures.append({'query_id':r['query_id'],'reasons':reasons})
    write_jsonl(output/'per_query.jsonl',rows);write_json(output/'summary.json',summary);write_jsonl(output/'failures.jsonl',failures)
    write_jsonl(output/'excluded_queries.jsonl',[x for x in validation['errors'] if x.get('query_id') in qs]);print(json.dumps({'output':str(output),'scored':len(rows),'failures':len(failures)},ensure_ascii=False))

if __name__=='__main__':main()

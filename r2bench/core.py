"""Deterministic source-position evidence scoring, with separately nullable layers."""
from __future__ import annotations
import hashlib, json, math, random
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from fractions import Fraction
from .serialize import serialize


def read_jsonl(path):
    out=[]
    with Path(path).open(encoding='utf-8') as f:
        for n,line in enumerate(f,1):
            if line.strip():
                x=json.loads(line)
                if not isinstance(x,dict):raise ValueError(f'{path}:{n}: expected object')
                out.append(x)
    return out


def write_json(path,obj):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    Path(path).write_text(json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def write_jsonl(path,rows):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    Path(path).write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True,allow_nan=False)+'\n' for x in rows),encoding='utf-8')


def instant(s):
    x=datetime.fromisoformat(s.replace('Z','+00:00'))
    if x.tzinfo is None:raise ValueError('timezone missing')
    return x


def merge(intervals):
    result=[]
    for a,b in sorted(intervals):
        if result and a<=result[-1][1]:result[-1]=(result[-1][0],max(b,result[-1][1]))
        else:result.append((a,b))
    return result


def contains(intervals,a,b):
    return any(x<=a and b<=y for x,y in intervals)


def overlap(intervals,a,b):
    return sum(max(0,min(y,b)-max(x,a)) for x,y in intervals)


def frac(a,b):return Fraction(a,b) if b else Fraction(0)


def exact(metrics):
    return {k:[v.numerator,v.denominator] for k,v in metrics.items() if isinstance(v,Fraction)}


class Dataset:
    def __init__(self,root):
        self.root=Path(root);self.queries={x['query_id']:x for x in read_jsonl(self.root/'public/queries.jsonl')}
        self.gold={x['query_id']:x for x in read_jsonl(self.root/'gold/gold.jsonl')}
        self.rounds={x['round_id']:x for x in read_jsonl(self.root/'public/rounds.jsonl')}
        self.messages={};self.order={};self.message_round={}
        for frame in read_jsonl(self.root/'public/histories.jsonl'):
            for m in frame['messages']:
                self.order[m['turn_id']]=len(self.order);self.messages[m['turn_id']]=m
        for rid,r in self.rounds.items():
            for mid in r['message_ids']:self.message_round[mid]=rid
        if set(self.queries)!=set(self.gold):raise ValueError('query/Gold identity mismatch')
        self.scope_cache={}

    def scope(self,q):
        key=q['query_id']
        if key not in self.scope_cache:
            allowed=set(q['allowed_frame_ids']);now=instant(q['query_at'])
            self.scope_cache[key]={mid for mid,m in self.messages.items() if m['conversation_id'] in allowed and instant(m['timestamp'])<=now}
        return self.scope_cache[key]

    def whole_round(self,rid):
        return [{'message_id':mid,'start':0,'end':len(self.messages[mid]['content']),'text':self.messages[mid]['content']} for mid in self.rounds[rid]['message_ids']]

    def quality(self,g,items):
        cov=defaultdict(list)
        for x in items:cov[x['message_id']].append((x['start'],x['end']))
        cov={k:merge(v) for k,v in cov.items()}
        injected_rounds={self.message_round[x['message_id']] for x in items if x['end']>x['start']}
        evidence={e['evidence_id']:e for e in g['evidence_units']}
        hit_units={eid for eid,e in evidence.items() if all(contains(cov.get(s['message_id'],[]),s['start'],s['end']) for s in e['spans'])}
        relevant_rounds={s['round_id'] for e in evidence.values() for s in e['spans']}
        p=frac(len(injected_rounds&relevant_rounds),len(injected_rounds));r=frac(len(injected_rounds&relevant_rounds),len(relevant_rounds))
        pathsets=[set(s['evidence_ids']) for s in g['sufficient_sets']]
        path_rounds=[{s['round_id'] for eid in path for s in evidence[eid]['spans']} for path in pathsets]
        pathrec=max((frac(len(injected_rounds&pr),len(pr)) for pr in path_rounds),default=Fraction(0))
        hit_claims={c for eid in hit_units for c in evidence[eid]['claim_ids']}
        relsp=defaultdict(list)
        for e in evidence.values():
            for s in e['spans']:relsp[s['message_id']].append((s['start'],s['end']))
        relsp={k:merge(v) for k,v in relsp.items()}
        denom=sum(x['end']-x['start'] for x in items)
        num=sum(overlap(relsp.get(x['message_id'],[]),x['start'],x['end']) for x in items)
        unique=sum(b-a for v in cov.values() for a,b in v)
        out={'RelevantRoundPrecision':p,'RelevantRoundRecall':r,'RelevantRoundF1':2*p*r/(p+r) if p+r else Fraction(0),
             'BestPathRoundRecall':pathrec,'SufficiencySuccess':Fraction(int(any(s<=hit_units for s in pathsets))),
             'SourceClaimRecall':frac(len(hit_claims),len(g['source_claims'])),'SpanPurity':frac(num,denom),
             'PathCoverageRate':frac(sum(s<=hit_units for s in pathsets),len(pathsets)),
             'InjectedDistinctRounds':len(injected_rounds),'InjectedCodepoints':denom,'DuplicateCodepoints':denom-unique}
        return out

    def check_candidates(self,q,raw):
        if not isinstance(raw,list):raise ValueError('candidate_results must be a list')
        ids=[];scope=self.scope(q)
        for i,x in enumerate(raw):
            if isinstance(x,str):rid=x
            elif isinstance(x,dict):
                rid=x.get('round_id')
                if 'rank' in x and (type(x['rank']) is not int or x['rank']!=i+1):raise ValueError('ranks must match list order, starting at 1')
            else:raise ValueError('invalid candidate entry')
            if rid not in self.rounds or not set(self.rounds[rid]['message_ids'])<=scope:raise ValueError('candidate outside source scope')
            ids.append(rid)
        if len(ids)!=len(set(ids)):raise ValueError('duplicate candidates')
        return ids

    def check_injection(self,q,raw):
        if not isinstance(raw,list):raise ValueError('final_injection must be a list; omit when not measured')
        out=[];scope=self.scope(q)
        for x in raw:
            if not isinstance(x,dict):raise ValueError('invalid injection item')
            mid=x.get('message_id');a=x.get('start');b=x.get('end')
            if mid not in scope:raise ValueError('injection outside source scope')
            if type(a) is not int or type(b) is not int or not 0<=a<b<=len(self.messages[mid]['content']):raise ValueError('invalid Unicode interval')
            if x.get('text')!=self.messages[mid]['content'][a:b]:raise ValueError('injection text differs from original source')
            out.append({'message_id':mid,'start':a,'end':b,'text':x['text']})
        return out

    def reference_items(self,g,path):
        es={e['evidence_id']:e for e in g['evidence_units']};cov=defaultdict(list)
        for eid in path['evidence_ids']:
            for s in es[eid]['spans']:cov[s['message_id']].append((s['start'],s['end']))
        return [{'message_id':mid,'start':a,'end':b,'text':self.messages[mid]['content'][a:b]}
                for mid in sorted(cov,key=self.order.get) for a,b in merge(cov[mid])]

    def score_one(self,pred,encoder=None,budget=None,min_reference=None):
        qid=pred['query_id'];q=self.queries[qid];g=self.gold[qid]
        out={k:g[k] for k in ('query_id','environment_id','split','recall_family','expected_behavior','legacy_content_type','difficulty')}
        out.update({'missing_output':pred.get('_missing_output',False),'evaluation_scope':'author_reconstructed_Gold','errors':[],'candidate':None,'injection':None,
                    'action':pred.get('action'),'ActionAccuracy':int(pred.get('action')==g['expected_behavior'])})
        for k in ('confidence','latency_ms'):
            value=pred.get(k)
            if value is not None and (type(value) not in (float,int) or not math.isfinite(value) or value<0 or (k=='confidence' and value>1)):
                out['errors'].append(k+': invalid optional measurement');value=None
            out[k]=value
        if pred.get('action') not in ('RETRIEVE','CLARIFY','ABSTAIN',None):out['errors'].append('unknown action')
        ids=[];cok=True
        if 'candidate_results' in pred:
            try:ids=self.check_candidates(q,pred['candidate_results'])
            except (ValueError,TypeError,KeyError) as e:out['errors'].append('candidate: '+str(e));cok=False
            if g['expected_behavior']=='RETRIEVE':
                cd={'valid':cok,'returned':len(ids),'at':{}}
                for k in (1,3,5,10,20,50):
                    items=[x for rid in ids[:k] for x in self.whole_round(rid)]
                    a=self.quality(g,items); names=('RelevantRoundPrecision','RelevantRoundRecall','RelevantRoundF1','BestPathRoundRecall','SufficiencySuccess')
                    cd['at'][str(k)]={n:float(a[n]) for n in names};cd['at'][str(k)]['exact']=exact({n:a[n] for n in names})
                allq=self.quality(g,[x for rid in ids for x in self.whole_round(rid)])
                cd['all']={n:float(allq[n]) for n in names};cd['all']['exact']=exact({n:allq[n] for n in names})
                out['candidate']=cd
            else:out['candidate_protocol']={'valid':cok,'returned':len(ids),'quality_applicable':False}
        if 'final_injection' in pred:
            iok=True;items=[]
            try:items=self.check_injection(q,pred['final_injection'])
            except (ValueError,TypeError,KeyError) as e:out['errors'].append('injection: '+str(e));iok=False
            tokens=None if not iok or encoder is None else encoder.count(serialize(items,self.messages))
            if iok and budget is not None and tokens is not None and tokens>budget:
                iok=False;out['errors'].append('injection: explicit appendix token budget exceeded')
            if g['expected_behavior']=='RETRIEVE':
                iq=self.quality(g,items if iok else [])
                out['injection']={n:float(v) if isinstance(v,Fraction) else v for n,v in iq.items()}
                out['injection'].update({'exact':exact(iq),'valid':iok,'InjectionTokens':tokens,'MinRegisteredSufficientTokens':min_reference,
                    'RelativeOverhead': (tokens/min_reference-1) if iq['SufficiencySuccess']==1 and tokens is not None and min_reference else None,
                    'payload_sha256':hashlib.sha256(serialize(items,self.messages).encode()).hexdigest() if iok else None})
            else:out['injection_protocol']={'valid':iok,'InjectionTokens':tokens,'quality_applicable':False,'items':len(items)}
        return out


def nearest(values,p):
    if not values:return None
    return sorted(values)[max(0,math.ceil(p*len(values))-1)]


def mean_counts(values):
    v=[x for x in values if x is not None]
    return {'mean':sum(v)/len(v) if v else None,'denominator':len(v)}


def summarize(rows,bootstrap=True):
    out={'queries':len(rows),'missing_outputs':sum(x['missing_output'] for x in rows),'rows_with_errors':sum(bool(x['errors']) for x in rows),
         'actions':mean_counts([r['ActionAccuracy'] for r in rows]),'injection':{},'candidate':{},
         'latency_ms':{'n':sum(r['latency_ms'] is not None for r in rows),'P50':nearest([r['latency_ms'] for r in rows if r['latency_ms'] is not None],.5),'P95':nearest([r['latency_ms'] for r in rows if r['latency_ms'] is not None],.95)}}
    ir=[r for r in rows if r['injection'] is not None]
    for k in ('RelevantRoundPrecision','RelevantRoundRecall','RelevantRoundF1','BestPathRoundRecall','SufficiencySuccess','SourceClaimRecall','SpanPurity','InjectionTokens','RelativeOverhead'):
        out['injection'][k]=mean_counts([r['injection'].get(k) for r in ir])
    cr=[r for r in rows if r['candidate'] is not None]
    for k in ('1','3','5','10','20','50','all'):
        out['candidate'][k]={}
        for n in ('RelevantRoundPrecision','RelevantRoundRecall','RelevantRoundF1','BestPathRoundRecall','SufficiencySuccess'):
            out['candidate'][k][n]=mean_counts([(r['candidate']['all'] if k=='all' else r['candidate']['at'][k])[n] for r in cr])
    if bootstrap:
        out['ci_method']={'method':'environment-cluster percentile bootstrap','repetitions':1000,'seed':20261019,'note':'conditional on author Gold, not a semantic-correctness interval'}
        for name,select in [('injection_sufficiency',lambda r:r['injection']['SufficiencySuccess'] if r['injection'] is not None else None),('candidate_sufficiency_at3',lambda r:r['candidate']['at']['3']['SufficiencySuccess'] if r['candidate'] is not None else None)]:
            groups=defaultdict(list)
            for r in rows:
                v=select(r)
                if v is not None:groups[r['environment_id']].append(v)
            entries=[(sum(v),len(v)) for k,v in sorted(groups.items())];vals=[];rng=random.Random(20261019)
            if entries:
                for _ in range(1000):
                    sample=[entries[rng.randrange(len(entries))] for _ in entries]
                    vals.append(sum(a for a,b in sample)/sum(b for a,b in sample))
            out[name+'_CI95']={'low':nearest(vals,.025),'high':nearest(vals,.975),'clusters':len(entries)}
    return out

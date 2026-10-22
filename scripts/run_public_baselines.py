#!/usr/bin/env python3
"""Baseline runner reads ONLY public history/query/round structure. No Gold imports.
Ranking methods omit final_injection. bm25_first_frame explicitly injects a frame.
"""
from __future__ import annotations
import argparse,hashlib,json,math,platform,random,re,time
from collections import Counter
from datetime import datetime
from pathlib import Path

def jl(p):return [json.loads(x) for x in Path(p).read_text(encoding='utf-8').splitlines() if x.strip()]
def write(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
def terms(text):
    t=''.join(re.findall(r'[\w]+',text.lower(),flags=re.UNICODE))
    return [t[i:i+2] for i in range(max(0,len(t)-1))]
def tm(t):return datetime.fromisoformat(t.replace('Z','+00:00'))

def main():
    p=argparse.ArgumentParser();p.add_argument('--public',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--methods',default='random,earliest,latest,bm25,tfidf,bm25_first_frame');p.add_argument('--seed',type=int,default=20261019)
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    frames=jl(a.public/'histories.jsonl');rounds=jl(a.public/'rounds.jsonl');queries=jl(a.public/'queries.jsonl')
    messages={m['turn_id']:m for f in frames for m in f['messages']};byframe={f['conversation_id']:f for f in frames}
    docs={r['round_id']:Counter(terms('\n'.join(messages[mid]['content'] for mid in r['message_ids']))) for r in rounds}
    roundidx={r['round_id']:r for r in rounds};pools={};start=time.perf_counter();methods=a.methods.split(',');callcounts={}
    for method in methods:
        if method not in {'random','earliest','latest','bm25','tfidf','bm25_first_frame'}:raise ValueError('unknown method')
        outfile=a.output/(method+'.jsonl');count=0
        with outfile.open('w',encoding='utf-8') as out:
            for q in queries:
                t0=time.perf_counter_ns();allowed=set(q['allowed_frame_ids']);cutoff=tm(q['query_at']);key=(tuple(sorted(allowed)),q['query_at'])
                if key not in pools:
                    pool=[r for r in rounds if r['conversation_id'] in allowed and all(tm(messages[mid]['timestamp'])<=cutoff for mid in r['message_ids'])]
                    pool.sort(key=lambda r:(tm(r['timestamp']),r['round_id']));freq=Counter()
                    for r in pool:freq.update(docs[r['round_id']].keys())
                    pools[key]=(pool,freq,sum(sum(docs[r['round_id']].values()) for r in pool)/len(pool))
                pool,df,avdl=pools[key];n=len(pool)
                qc=Counter(terms('\n'.join(x['content'] for x in q['current_context'])+'\n'+q['query_text']))
                if method=='earliest':rank=list(pool)
                elif method=='latest':rank=list(reversed(pool))
                elif method=='random':
                    rank=list(pool);seed=int.from_bytes(hashlib.sha256((str(a.seed)+q['query_id']).encode()).digest()[:8],'big');random.Random(seed).shuffle(rank)
                else:
                    scores={}
                    if method in {'bm25','bm25_first_frame'}:
                        for r in pool:
                            c=docs[r['round_id']];dl=sum(c.values());val=0.0
                            for t,qt in qc.items():
                                if not c[t]:continue
                                idf=math.log(1+(n-df[t]+.5)/(df[t]+.5));den=c[t]+1.2*(1-.75+.75*dl/avdl)
                                val+=qt*idf*c[t]*2.2/den
                            scores[r['round_id']]=val
                    else:
                        idf={t:math.log((1+n)/(1+df[t]))+1 for t in set(df)|set(qc)}
                        qv={t:tf*idf[t] for t,tf in qc.items()};qn=math.sqrt(sum(v*v for v in qv.values()))
                        for r in pool:
                            v={t:tf*idf[t] for t,tf in docs[r['round_id']].items()};norm=math.sqrt(sum(x*x for x in v.values()))
                            scores[r['round_id']]=sum(qv[t]*v.get(t,0) for t in qv)/(qn*norm) if qn*norm else 0.0
                    rank=sorted(pool,key=lambda r:(-scores[r['round_id']],tm(r['timestamp']),r['round_id']))
                pred={'query_id':q['query_id'],'action':'RETRIEVE','candidate_results':[r['round_id'] for r in rank]}
                if method=='bm25_first_frame':
                    f=byframe[rank[0]['conversation_id']] if rank else None
                    pred['final_injection']=[{'message_id':m['turn_id'],'start':0,'end':len(m['content']),'text':m['content']} for m in f['messages']] if f else []
                pred['latency_ms']=(time.perf_counter_ns()-t0)/1e6
                out.write(json.dumps(pred,ensure_ascii=False,sort_keys=True)+'\n');count+=1
        callcounts[method]=count
    write(a.output/'runtime.json',{'platform':platform.platform(),'python':platform.python_version(),'methods':callcounts,'actual_predictions':sum(callcounts.values()),
      'seed':a.seed,'query_source':'current_context plus current query','candidate_scope':'all allowed frames before query time',
      'cache':'round term counts precomputed; legal pools cached; no query result or Gold cache','cold_indexing_in_query_latency':False,
      'measurement':'one actual in-process call/query/method; not network or five independent repetitions','total_runner_seconds':time.perf_counter()-start,
      'token_budget':None,'round_cap':None,'API_calls':0,'external_model':'none','total_construction_cost':None,'parameters':{'bm25_k1':1.2,'bm25_b':.75,'terms':'Unicode word characters concatenated; overlapping character bigrams'},
      'read_isolation':'runner code reads only three files in supplied Public; no OS sandbox asserted',
      'inputs_sha256':{name:hashlib.sha256((a.public/name).read_bytes()).hexdigest() for name in ['queries.jsonl','histories.jsonl','rounds.jsonl']}})
    print(json.dumps(callcounts))
if __name__=='__main__':main()

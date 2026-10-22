import copy,unittest
from fractions import Fraction
from r2bench.core import Dataset,merge,contains,overlap,serialize

class Chars:
    def count(self,t):return len(t)


def fixture():
    d=object.__new__(Dataset);d.root=None;d.scope_cache={}
    d.messages={f'm{i}':{'turn_id':f'm{i}','content':text,'role':'assistant','conversation_id':f'f{i}',
      'timestamp':'2026-01-01T00:00:00+00:00'} for i,text in enumerate(['ABCD','EFGH','IJKL','MNOP'],1)}
    d.order={m:i for i,m in enumerate(d.messages)};d.message_round={f'm{i}':f'r{i}' for i in range(1,5)}
    d.rounds={f'r{i}':{'round_id':f'r{i}','conversation_id':f'f{i}','message_ids':[f'm{i}']} for i in range(1,5)}
    q={'query_id':'q','query_at':'2026-01-02T00:00:00+00:00','allowed_frame_ids':['f1','f2','f3','f4']}
    d.queries={'q':q}
    def unit(eid,mid,a,b,c):return {'evidence_id':eid,'claim_ids':[c], 'spans':[{'message_id':mid,'start':a,'end':b,'text':d.messages[mid]['content'][a:b],'round_id':d.message_round[mid]}]}
    g={'query_id':'q','environment_id':'env','split':'test','recall_family':'implicit_structure','expected_behavior':'RETRIEVE','legacy_content_type':'T04','difficulty':'UNDEFINED',
       'source_claims':[{'claim_id':'c1'},{'claim_id':'c2'}],
       'evidence_units':[unit('e1','m1',0,2,'c1'),unit('e2','m2',0,2,'c2')],
       'sufficient_sets':[{'evidence_ids':['e1','e2']} ]}
    d.gold={'q':g};return d,g

class Tests(unittest.TestCase):
    def setUp(self):self.d,self.g=fixture()
    def piece(self,mid,a=0,b=2):return {'message_id':mid,'start':a,'end':b,'text':self.d.messages[mid]['content'][a:b]}
    def score(self,**p):return self.d.score_one({'query_id':'q','action':'RETRIEVE',**p},Chars())
    def test_01_single_complete(self):
        self.g['source_claims']=self.g['source_claims'][:1];self.g['evidence_units']=self.g['evidence_units'][:1];self.g['sufficient_sets']=[{'evidence_ids':['e1']}]
        x=self.score(final_injection=[self.piece('m1')])['injection'];self.assertEqual(x['SufficiencySuccess'],1);self.assertEqual(x['SpanPurity'],1)
    def test_02_complete_extra(self):
        x=self.score(final_injection=[self.piece('m1'),self.piece('m2'),self.piece('m3')])['injection'];self.assertEqual(x['exact']['RelevantRoundPrecision'],[2,3]);self.assertEqual(x['SufficiencySuccess'],1)
    def test_03_only_one_necessary(self):
        x=self.score(final_injection=[self.piece('m1')])['injection'];self.assertEqual(x['BestPathRoundRecall'],.5);self.assertEqual(x['SufficiencySuccess'],0)
    def test_04_alternative_single(self):
        self.g['evidence_units'].append({'evidence_id':'e3','claim_ids':['c1','c2'],'spans':[dict(self.piece('m3'),round_id='r3')]})
        self.g['sufficient_sets'].append({'evidence_ids':['e3']})
        x=self.score(final_injection=[self.piece('m3')])['injection'];self.assertEqual(x['SufficiencySuccess'],1);self.assertEqual(x['exact']['RelevantRoundRecall'],[1,3])
    def test_05_round_hit_missing_span(self):
        x=self.score(final_injection=[self.piece('m1',2,4),self.piece('m2')])['injection'];self.assertEqual(x['BestPathRoundRecall'],1);self.assertEqual(x['SufficiencySuccess'],0)
    def test_06_duplicate_cost_coverage(self):
        a=self.score(final_injection=[self.piece('m1'),self.piece('m2')])['injection']
        b=self.score(final_injection=[self.piece('m1'),self.piece('m2'),self.piece('m1')])['injection'];self.assertGreater(b['InjectionTokens'],a['InjectionTokens']);self.assertEqual(b['DuplicateCodepoints'],2);self.assertEqual(a['SufficiencySuccess'],b['SufficiencySuccess'])
    def test_07_cross_frame_noncontinuous(self):
        self.g['evidence_units'][1]['spans']=[dict(self.piece('m4'),round_id='r4')]
        self.assertEqual(self.score(final_injection=[self.piece('m1'),self.piece('m4')])['injection']['SufficiencySuccess'],1)
    def test_08_empty(self):self.assertEqual(self.score(final_injection=[])['injection']['SufficiencySuccess'],0)
    def test_09_unmeasured_vs_empty(self):self.assertIsNone(self.score()['injection']);self.assertIsNotNone(self.score(final_injection=[])['injection'])
    def test_10_wrong_text_preserves_candidates(self):
        bad=self.piece('m1');bad['text']='ZZ';x=self.score(candidate_results=['r1','r2'],final_injection=[bad]);self.assertEqual(x['candidate']['all']['SufficiencySuccess'],1);self.assertFalse(x['injection']['valid'])
    def test_11_wrong_candidate_preserves_injection(self):
        x=self.score(candidate_results=['r1','r1'],final_injection=[self.piece('m1'),self.piece('m2')]);self.assertFalse(x['candidate']['valid']);self.assertEqual(x['injection']['SufficiencySuccess'],1)
    def test_12_future_source(self):
        self.d.messages['m1']['timestamp']='2027-01-01T00:00:00+00:00';self.assertFalse(self.score(final_injection=[self.piece('m1')])['injection']['valid'])
    def test_13_outside_allowed(self):
        self.d.queries['q']['allowed_frame_ids']=['f2'];self.assertFalse(self.score(candidate_results=['r1'])['candidate']['valid'])
    def test_14_adjacent_join(self):
        x=self.score(final_injection=[self.piece('m1',0,1),self.piece('m1',1,2),self.piece('m2')]);self.assertEqual(x['injection']['SufficiencySuccess'],1)
    def test_15_clarify(self):
        self.g['expected_behavior']='CLARIFY';self.g['evidence_units']=[];self.g['sufficient_sets']=[];self.g['source_claims']=[]
        x=self.score(action='CLARIFY',candidate_results=[],final_injection=[]);self.assertEqual(x['ActionAccuracy'],1);self.assertIsNone(x['injection']);self.assertIsNone(x['candidate'])
    def test_16_missing_field(self):
        self.g['expected_behavior']='ABSTAIN';x=self.score(action='ABSTAIN',final_injection=[]);self.assertEqual(x['ActionAccuracy'],1);self.assertIsNone(x['injection'])
    def test_17_explicit_budget(self):
        p={'query_id':'q','candidate_results':['r1','r2'],'final_injection':[self.piece('m1'),self.piece('m2')]}
        x=self.d.score_one(p,Chars(),budget=1);self.assertEqual(x['candidate']['all']['SufficiencySuccess'],1);self.assertFalse(x['injection']['valid'])
    def test_18_role_and_id_invariance(self):
        items=[self.piece('m1'),self.piece('m2')];before=serialize(items,self.d.messages)
        renamed=[dict(x,message_id='long_changed_source_'+x['message_id']) for x in items]
        msgs={'long_changed_source_'+k:v for k,v in self.d.messages.items()};self.assertEqual(before,serialize(renamed,msgs))
    def test_19_optional_measurement_nan(self):
        x=self.score(latency_ms=float('nan'),confidence=2);self.assertIsNone(x['latency_ms']);self.assertIsNone(x['confidence']);self.assertEqual(len(x['errors']),2)
    def test_20_and_multi_span(self):
        self.g['evidence_units'][0]['spans'].append(dict(self.piece('m3'),round_id='r3'))
        x=self.score(final_injection=[self.piece('m1'),self.piece('m2')]);self.assertEqual(x['injection']['SufficiencySuccess'],0)
    def test_21_rank_order_matters_not_injection(self):
        a=self.score(candidate_results=['r1','r2','r3'],final_injection=[self.piece('m1'),self.piece('m2')]);b=self.score(candidate_results=['r3','r1','r2'],final_injection=[self.piece('m1'),self.piece('m2')]);self.assertEqual(a['injection'],b['injection']);self.assertNotEqual(a['candidate']['at']['1'],b['candidate']['at']['1'])
    def test_22_bool_offset_invalid(self):
        s=self.piece('m1');s['start']=False;self.assertFalse(self.score(final_injection=[s])['injection']['valid'])
    def test_23_merge_reference(self):
        self.assertEqual(merge([(1,2),(2,4),(8,9),(3,6)]),[(1,6),(8,9)]);self.assertTrue(contains([(1,6)],2,6));self.assertEqual(overlap([(1,6),(8,9)],5,9),2)
    def test_24_repeated_identical_input(self):
        p={'candidate_results':['r1','r2'],'final_injection':[self.piece('m1'),self.piece('m2')]};self.assertEqual(self.score(**p),self.score(**p))

if __name__=='__main__':unittest.main()

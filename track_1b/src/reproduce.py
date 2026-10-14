"""Recompute submitted results from frozen answers, judgments and adjudications."""
from pathlib import Path
import csv, hashlib, json
import scoring as bewertung

ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'docs/evidence'
OUT=ROOT/'results'

def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def write(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def main():
    for name,digest in read(E/'manifest.json').items():
        if hashlib.sha256((E/name).read_bytes()).hexdigest()!=digest:
            raise ValueError('Input changed: '+name)
    _,items=bewertung.load_items(E/'items.json')
    responses=bewertung.load_responses(E/'responses.json',items)
    result=bewertung.evaluate(responses,items,sorted((E/'judgments').glob('*.json')),
        gold_path=E/'human_labels.json',adjudications_path=E/'adjudications.json')
    for row in result['rows']:
        a=row.get('adjudication') or {}
        row['final_content_score_percent']=a.get('adjudicated_content_score_percent',row['score_percent'])
        row['final_criteria']=a.get('adjudicated_criteria',row['criteria'])
        row['final_reason']=a.get('reason',row['reason'])
    counts={label:sum(r['final_label']==label for r in result['rows']) for label in ['correct','incorrect','not_attempted']}
    assert len(result['rows'])==300 and len({r['item_id'] for r in result['rows']})==300
    assert all(r['final_label'] is not None and r['finish_reason']=='stop' for r in result['rows'])
    assert counts==read(E/'expected_results.json')['counts'],counts
    # Reconstruct the initial independent comparison, before all adjudications.
    initial_items=dict(items)
    previous=read(E/'audit/original_agr003.json')
    initial_items['agr_003']=previous['item']
    initial_responses=[previous['response'] if r['item_id']=='agr_003' else r for r in responses]
    initial_judgments=[]
    for path in sorted((E/'judgments').glob('*.json')):
        for j in read(path)['judgments']:
            if j['item_id']!='agr_003':initial_judgments.append(j)
    initial_judgments.append(previous['judgment'])
    initial_byid={r['response_id']:r for r in initial_responses}
    human={h['response_id']:h for h in read(E/'audit/original_human_60.json')}
    assert len(human)==60
    pairs=[]
    for j in initial_judgments:
        r=initial_byid[j['response_id']]
        scored=bewertung.score_judgment(j,r,initial_items[r['item_id']])
        if r['response_id'] in human and scored['judge_label'] is not None:
            pairs.append((scored['judge_label'],human[r['response_id']]['human_label']))
    agreement={'original_human_sample':60,'comparable':len(pairs),'agreed':sum(a==b for a,b in pairs)}
    assert agreement=={'original_human_sample':60,'comparable':57,'agreed':42},agreement
    agreement['rate']=agreement['agreed']/agreement['comparable']
    OUT.mkdir(exist_ok=True)
    write(OUT/'evaluation.json',result)
    summary={'n':300,'counts':counts,'accuracy':counts['correct']/300,'original_independent_agreement':agreement,
             'note':'299 original answers plus one revised question and fresh answer. Human agreement precedes adjudication.'}
    write(OUT/'summary.json',summary)
    fields=['response_id','item_id','model_id','model_response','score_percent','final_content_score_percent','judge_label','human_label','final_label','label_source','final_reason']
    with (OUT/'model_response_dataset.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');writer.writeheader();writer.writerows(result['rows'])
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__':main()

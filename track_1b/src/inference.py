"""Optional fresh inference through an OpenAI-compatible API. No judging calls."""
from pathlib import Path
from datetime import datetime,timezone
import json,os,time,urllib.request,urllib.error,uuid

ROOT=Path(__file__).resolve().parents[1]

def main():
    token=os.environ.get('LLM_API_KEY')
    if not token:raise SystemExit('Set LLM_API_KEY. It is never written to disk.')
    model=os.environ.get('LLM_NAME','swiss-ai/Apertus-v1.5-70B:featherless-ai')
    base=os.environ.get('LLM_BASE_URL','https://router.huggingface.co/v1').rstrip('/')
    items=json.loads((ROOT/'docs/evidence/items.json').read_text())['items']
    prompt=(ROOT/'src/answer_prompt.txt').read_text().strip()
    OUT=ROOT/'results';OUT.mkdir(exist_ok=True)
    path=OUT/'new_inference.json'
    state=json.loads(path.read_text()) if path.exists() else {'run_id':datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:6],'model':model,'base_url':base,'responses':[]}
    assert state['model']==model and state['base_url']==base,'Use a separate results folder for another model.'
    byid={r['item_id']:r for r in state['responses']}
    for n,item in enumerate(items,1):
        if item['id'] in byid:continue
        text=prompt+'\n\n'+item['question']
        payload={'model':model,'messages':[{'role':'user','content':text}],'temperature':0,'max_tokens':1200}
        for attempt in range(5):
            try:
                req=urllib.request.Request(base+'/chat/completions',data=json.dumps(payload).encode(),headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'})
                with urllib.request.urlopen(req,timeout=120) as reply:completion=json.load(reply)
                choice=completion['choices'][0]
                if not choice['message'].get('content'):raise ValueError('Empty response')
                break
            except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError,json.JSONDecodeError,ValueError) as error:
                if isinstance(error,urllib.error.HTTPError) and error.code not in (408,409,429) and error.code<500:raise
                if attempt==4:raise
                time.sleep([2,5,10,20][attempt])
        record={'response_id':item['id']+'_'+state['run_id'],'item_id':item['id'],'model_id':model,'model_response':choice['message']['content'],'prompt':text,'finish_reason':choice['finish_reason'],'usage':completion.get('usage'),'settings':{'temperature':0,'max_tokens':1200}}
        state['responses'].append(record);byid[item['id']]=record
        tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(state,ensure_ascii=False,indent=2));tmp.replace(path)
        print(f'{n}/300 {item["id"]}: {choice["finish_reason"]}',flush=True)
    print('Fresh model answers:',path)
    print('These answers require new independent judgments. They do not inherit submitted labels.')

if __name__=='__main__':main()

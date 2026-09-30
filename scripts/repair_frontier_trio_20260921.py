#!/usr/bin/env python3
"""One technical retry at unchanged settings; preserve all original failures."""
import json,shutil
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import run_freeflow_multi as runner
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'logs/2026-09-21-frontier-trio'
ARCHIVE=ROOT/'discarded/2026-09-21-frontier-trio-first-pass'
def main():
    import os
    report=[]
    for cell,model,pin in [('grok-4-7-or-pin-xai','x-ai/grok-4.7','xAI'),('glm-5-3-flashx-or-pin-zai','z-ai/glm-5.3-flashx','Z.AI')]:
        jobs=[];os.environ['OR_PROVIDER']=pin
        for p in sorted((ROOT/'data/traces_freeflow'/('freeflow_'+cell)).glob('*.json')):
            d=json.loads(p.read_text());choice=(d.get('raw',{}).get('choices') or [{}])[0]
            if choice.get('finish_reason')=='stop':continue
            backup=ARCHIVE/cell/p.name
            if backup.exists():raise RuntimeError(f'Retry already attempted for {cell}/{p.name}; inspect, do not reroll')
            backup.parent.mkdir(parents=True,exist_ok=True);shutil.move(p,backup)
            cond,idx=p.stem.rsplit('_',1)
            jobs.append(('openrouter',model,cell,cond,dict(runner.CONDITIONS)[cond],int(idx),16000))
            report.append(dict(cell=cell,sample=p.stem,original_finish=choice.get('finish_reason'),original=str(backup.relative_to(ROOT)),max_tokens=16000))
        (OUT/'technical_retry_manifest.json').write_text(json.dumps(report,indent=2)+'\n')
        with ThreadPoolExecutor(max_workers=3) as pool:
            for result in pool.map(lambda args:runner.run_one(*args),jobs): print(result[:3],flush=True)
    print('Single technical retry pass finished; strict audit still required',flush=True)
if __name__=='__main__':main()

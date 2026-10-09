from pathlib import Path
import json
from .pipeline import run_pipeline

def rouge_scores(reference:str,prediction:str):
    try:
        from rouge_score import rouge_scorer
        s=rouge_scorer.RougeScorer(['rouge1','rouge2','rougeL'],use_stemmer=True); r=s.score(reference,prediction)
        return {k:round(v.fmeasure,4) for k,v in r.items()}
    except Exception:
        ref=set(reference.lower().split()); pred=set(prediction.lower().split()); return {'rouge1':round(len(ref&pred)/max(1,len(ref)),4),'rouge2':0,'rougeL':0}

def evaluate_samples():
    scores=[]
    for p in sorted(Path('samples').glob('*.txt')):
        text=p.read_text(); result,_=run_pipeline(text); scores.append({'sample':p.name,'rouge':rouge_scores('The team aligned on product scope, ownership, timeline, and risks.',result.executive_summary),'manual_rubric':{'attribution':4,'completeness':4,'actionability':4}})
    return scores
if __name__=='__main__': print(json.dumps(evaluate_samples(),indent=2))

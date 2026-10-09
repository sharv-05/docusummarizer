import json, os, re
from .models import MeetingExtraction
from .prompts import SYSTEM_PROMPT

class TokenLedger:
    def __init__(self): self.rows=[]
    def add(self,step,input_tokens,output_tokens,model='mock',input_rate=None,output_rate=None):
        ir=float(input_rate if input_rate is not None else os.getenv('COST_PER_1K_INPUT','0.00015')); orate=float(output_rate if output_rate is not None else os.getenv('COST_PER_1K_OUTPUT','0.0006'))
        self.rows.append({'step':step,'input_tokens':input_tokens,'output_tokens':output_tokens,'estimated_cost_usd':round(input_tokens/1000*ir+output_tokens/1000*orate,6),'model':model})
    @property
    def total_tokens(self): return sum(r['input_tokens']+r['output_tokens'] for r in self.rows)
    @property
    def total_cost(self): return round(sum(r['estimated_cost_usd'] for r in self.rows),6)

def _mock_extract(text:str)->dict:
    lines=[x.strip() for x in text.splitlines() if x.strip()]
    speakers=[]
    for line in lines:
        if ':' in line:
            s=line.split(':',1)[0].strip()
            if len(s)<40 and s not in speakers: speakers.append(s)
    sentences=re.split(r'(?<=[.!?])\s+',text)
    decisions=[]; actions=[]; risks=[]; topics=[]
    for s in sentences:
        low=s.lower()
        speaker=s.split(':',1)[0].strip() if ':' in s else 'Unknown'
        if any(k in low for k in ['decide','agreed','approved','will use','chosen','go with']): decisions.append({'decision':s,'speaker':speaker,'context':'Extracted from transcript','confidence':0.86})
        if any(k in low for k in ['action','todo','will ','owner','follow up','send ','prepare ','schedule ']):
            owner='Unassigned'
            m=re.search(r'(?:owner|by|for)\s+([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)?)',s)
            if m: owner=m.group(1)
            actions.append({'task':s,'owner':owner,'deadline':'Not specified','status':'open','confidence':0.78})
        if any(k in low for k in ['risk','blocked','concern','delay','issue','dependency','uncertain']): risks.append({'risk':s,'severity':'high' if any(k in low for k in ['critical','blocked','security']) else 'medium','owner':'Unassigned','mitigation':'Review and assign a mitigation owner'})
    keyword_groups={'Product':['product','feature','customer','user'],'Engineering':['api','model','data','deploy','system'],'Planning':['timeline','launch','milestone','budget']}
    for topic,keys in keyword_groups.items():
        count=sum(text.lower().count(k) for k in keys)
        if count: topics.append({'topic':topic,'summary':f'{topic} was discussed across the transcript.','mentions':count})
    summary=' '.join(sentences[:3])[:900] or text[:900]
    return {'title':'Meeting intelligence brief','date':'Not specified','executive_summary':summary,'decisions':decisions[:12],'action_items':actions[:20],'risks':risks[:12],'topics':topics,'speakers':speakers,'model':'mock'}

def extract_structured(source_text:str, context:str, ledger:TokenLedger, model='mock')->MeetingExtraction:
    provider=os.getenv('LLM_PROVIDER','mock').lower()
    if provider=='openai' and os.getenv('OPENAI_API_KEY'):
        try:
            from langchain_openai import ChatOpenAI
            from langchain_core.messages import SystemMessage,HumanMessage
            llm=ChatOpenAI(model=os.getenv('OPENAI_MODEL','gpt-4o-mini'),temperature=0)
            structured=llm.with_structured_output(MeetingExtraction)
            result=structured.invoke([SystemMessage(content=SYSTEM_PROMPT),HumanMessage(content=context)])
            ledger.add('structured_extraction',len(context.split())*4,len(result.model_dump_json().split())*4,model=os.getenv('OPENAI_MODEL','gpt-4o-mini'))
            return result.model_copy(update={'source_words':len(source_text.split()),'model':os.getenv('OPENAI_MODEL','gpt-4o-mini')})
        except Exception:
            pass
    data=_mock_extract(source_text); ledger.add('structured_extraction',len(context.split())*4,350,model='mock')
    return MeetingExtraction.model_validate(data).model_copy(update={'source_words':len(source_text.split()),'model':'mock'})

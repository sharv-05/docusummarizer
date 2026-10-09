import os
from .chunking import chunk_transcript
from .ingestion import validate_word_limit,detect_speakers
from .llm import TokenLedger,extract_structured
from .models import MeetingExtraction

def run_pipeline(text:str,chunk_size:int=1400,overlap:int=180)->tuple[MeetingExtraction,TokenLedger]:
    words=validate_word_limit(text,int(os.getenv('MAX_WORDS','50000')))
    chunks=chunk_transcript(text,chunk_size,overlap)
    ledger=TokenLedger()
    summaries=[]
    for c in chunks:
        # A lightweight extractive chunk summary keeps mock mode free and bounded.
        summary=' '.join(c.text.split())[:650]
        summaries.append(summary); ledger.add(f'chunk_summary_{c.index+1}',c.estimated_tokens,min(180,max(30,len(summary.split()))),model='mock')
    context='\n\n'.join(summaries)
    result=extract_structured(text,context,ledger)
    result=result.model_copy(update={'chunks':len(chunks),'source_words':words,'speakers':detect_speakers(text) or result.speakers})
    return result,ledger

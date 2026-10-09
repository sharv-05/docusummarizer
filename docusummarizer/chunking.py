import re
from dataclasses import dataclass
try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except Exception:
    RecursiveCharacterTextSplitter=None
@dataclass
class Chunk:
    index:int
    text:str
    words:int
    estimated_tokens:int

def _speaker_boundaries(text:str):
    return re.sub(r'(?m)^(?=[A-Za-z][A-Za-z ._-]{1,40}:)', '\n', text)

def chunk_transcript(text:str, chunk_size:int=1400, overlap:int=180)->list[Chunk]:
    # Keep speaker labels intact by treating line breaks as high-priority separators.
    prepared=_speaker_boundaries(text)
    if RecursiveCharacterTextSplitter:
        splitter=RecursiveCharacterTextSplitter(chunk_size=chunk_size,chunk_overlap=overlap,separators=['\n\n','\n','. ','? ','! ',' '])
        parts=splitter.split_text(prepared)
    else:
        parts=[]; start=0
        while start<len(prepared):
            end=min(len(prepared),start+chunk_size); parts.append(prepared[start:end]); start=max(end-overlap,end)
    return [Chunk(i,p.strip(),len(p.split()),max(1,len(p.split())*4//3)) for i,p in enumerate(parts) if p.strip()]

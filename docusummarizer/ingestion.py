from io import BytesIO
from pathlib import Path
import re

def clean_text(text: str) -> str:
    text=text.replace('\r\n','\n').replace('\r','\n')
    text=re.sub(r'[ \t]+',' ',text)
    text=re.sub(r'\n{3,}','\n\n',text)
    return text.strip()

def parse_upload(name: str, data: bytes) -> str:
    ext=Path(name).suffix.lower()
    if ext in {'.txt','.md'}: return clean_text(data.decode('utf-8',errors='replace'))
    if ext=='.docx':
        from docx import Document
        doc=Document(BytesIO(data)); return clean_text('\n'.join(p.text for p in doc.paragraphs if p.text.strip()))
    if ext=='.pdf':
        import fitz
        doc=fitz.open(stream=data,filetype='pdf'); return clean_text('\n'.join(page.get_text() for page in doc))
    raise ValueError('Unsupported file type. Use .txt, .docx, or .pdf.')

def validate_word_limit(text:str, max_words:int=50000):
    words=len(text.split())
    if words>max_words: raise ValueError(f'Transcript has {words:,} words; the limit is {max_words:,}.')
    if words<5: raise ValueError('Transcript is too short to summarize.')
    return words

def detect_speakers(text:str)->list[str]:
    names=[]
    for line in text.splitlines():
        m=re.match(r'^\s*([A-Za-z][A-Za-z ._-]{1,40}):',line)
        if m and m.group(1).strip() not in names: names.append(m.group(1).strip())
    return names

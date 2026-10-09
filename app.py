import os,streamlit as st
from dotenv import load_dotenv
load_dotenv()
from docusummarizer.ingestion import parse_upload
from docusummarizer.pipeline import run_pipeline
from docusummarizer.export import extraction_json,extraction_pdf
st.set_page_config(page_title='DocuSummarizer',page_icon='◆',layout='wide')
st.markdown("""<style>body{background:#f7f9fb}.block-container{max-width:1200px;padding-top:2rem}.hero{background:linear-gradient(135deg,#14243a,#203d5d);color:white;padding:2.2rem;border-radius:18px;margin-bottom:1.4rem}.hero h1{font-size:2.6rem;margin:.2rem 0;color:white}.hero p{color:#b5c7d8;max-width:650px}.metric{background:white;border:1px solid #dde5ed;border-radius:12px;padding:1rem}.section{background:white;border:1px solid #e0e7ee;border-radius:12px;padding:1rem 1.2rem;margin-bottom:1rem}.risk-high{border-left:5px solid #d95868}.risk-medium{border-left:5px solid #dfa24d}.chip{display:inline-block;padding:.25rem .5rem;background:#e7f5f1;border-radius:20px;margin:.15rem;font-size:.8rem}</style>""",unsafe_allow_html=True)
st.markdown('<div class="hero"><div style="letter-spacing:.15em;font-size:.75rem;color:#8ee1cf">MEETING INTELLIGENCE / STRUCTURED NOTES</div><h1>Make every meeting<br/>more <span style="color:#8ee1cf">actionable.</span></h1><p>Upload a transcript and turn scattered conversation into a clear evidence trail of decisions, owners, risks, and next steps.</p></div>',unsafe_allow_html=True)
with st.sidebar:
    st.header('DocuSummarizer')
    st.caption(f"Provider: {os.getenv('LLM_PROVIDER','mock')}")
    st.divider(); st.subheader('Input')
    upload=st.file_uploader('Upload transcript',type=['txt','docx','pdf'])
    sample=st.button('Load sample transcript',use_container_width=True)
    chunk_size=st.slider('Chunk size (characters)',800,2400,1400,100)
    overlap=st.slider('Chunk overlap',50,400,180,10)
text=None
if sample:
    text=open('samples/product-strategy.txt').read(); st.session_state['text']=text
if upload:
    try: st.session_state['text']=parse_upload(upload.name,upload.getvalue()); st.session_state['filename']=upload.name
    except Exception as e: st.error(str(e))
text=st.session_state.get('text')
if not text:
    st.info('Upload a transcript or select Load sample transcript to begin.')
    st.stop()
st.caption(f"{len(text.split()):,} words · {len(text):,} characters")
if st.button('Analyze transcript',type='primary',use_container_width=True):
    with st.status('Running structured extraction pipeline…',expanded=True) as status:
        try:
            result,ledger=run_pipeline(text,chunk_size,overlap); st.session_state['result']=result; st.session_state['ledger']=ledger; status.update(label='Analysis complete',state='complete')
        except Exception as e: status.update(label='Analysis failed',state='error'); st.exception(e)
result=st.session_state.get('result'); ledger=st.session_state.get('ledger')
if not result: st.warning('Click Analyze transcript to generate the intelligence packet.'); st.stop()
metrics=st.columns(4)
for col,label,value in zip(metrics,['Source words','Chunks','Token estimate','Est. API cost'],[f'{result.source_words:,}',result.chunks,f'{ledger.total_tokens:,}',f'${ledger.total_cost:.4f}']):
    col.markdown(f'<div class="metric"><small>{label}</small><h2 style="margin:.3rem 0">{value}</h2></div>',unsafe_allow_html=True)
st.write('')
tabs=st.tabs(['Executive summary','Decisions','Action items','Risks & topics','Token ledger'])
with tabs[0]:
    st.subheader(result.title); st.write(result.executive_summary); st.caption('Speakers: '+(', '.join(result.speakers) or 'No speaker labels detected'))
with tabs[1]:
    for d in result.decisions: st.markdown(f'**{d.speaker}** — {d.decision}  \n`confidence {d.confidence:.0%}`')
    if not result.decisions: st.info('No explicit decisions detected.')
with tabs[2]:
    st.dataframe([a.model_dump() for a in result.action_items],use_container_width=True,hide_index=True)
with tabs[3]:
    st.subheader('Risk flags')
    for r in result.risks: st.markdown(f'<div class="section risk-{r.severity}"><b>{r.severity.upper()}</b> · {r.risk}<br/><small>Owner: {r.owner} · Mitigation: {r.mitigation}</small></div>',unsafe_allow_html=True)
    st.subheader('Topic clusters'); st.dataframe([t.model_dump() for t in result.topics],use_container_width=True,hide_index=True)
with tabs[4]:
    st.dataframe(ledger.rows,use_container_width=True,hide_index=True); st.caption('Cost is an estimate based on configured per-1K-token rates; provider billing may differ.')
st.divider(); st.subheader('Export')
c1,c2=st.columns(2); c1.download_button('Download JSON',extraction_json(result,ledger),'docusummarizer-report.json','application/json',use_container_width=True); c2.download_button('Download PDF',extraction_pdf(result,ledger),'docusummarizer-report.pdf','application/pdf',use_container_width=True)

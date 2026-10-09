import json
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak
from .models import MeetingExtraction

def extraction_json(result:MeetingExtraction,ledger)->bytes:
    payload={'extraction':result.model_dump(),'token_ledger':ledger.rows,'token_total':ledger.total_tokens,'estimated_cost_usd':ledger.total_cost}
    return json.dumps(payload,indent=2).encode()

def extraction_pdf(result:MeetingExtraction,ledger)->bytes:
    out=BytesIO(); doc=SimpleDocTemplate(out,pagesize=letter,rightMargin=.55*inch,leftMargin=.55*inch,topMargin=.5*inch,bottomMargin=.5*inch)
    styles=getSampleStyleSheet(); styles.add(ParagraphStyle(name='Tiny',parent=styles['BodyText'],fontSize=8,leading=10))
    story=[Paragraph('DocuSummarizer',styles['Title']),Paragraph(result.title,styles['Heading2']),Paragraph(f'{result.source_words:,} words · {result.chunks} chunks · {result.model}',styles['Tiny']),Spacer(1,12),Paragraph('Executive summary',styles['Heading2']),Paragraph(result.executive_summary,styles['BodyText']),Spacer(1,10)]
    def section(title,rows,headers):
        nonlocal story
        story += [Paragraph(title,styles['Heading2'])]
        if rows:
            t=Table([headers]+rows,colWidths=[1.55*inch,2.9*inch,1.45*inch,1.3*inch][:len(headers)]); t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#17304c')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('GRID',(0,0),(-1,-1),.3,colors.HexColor('#ccd5df')),('FONTSIZE',(0,0),(-1,-1),8),('VALIGN',(0,0),(-1,-1),'TOP'),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f3f6f8')])]))
            story += [t,Spacer(1,12)]
        else: story += [Paragraph('None identified.',styles['Tiny']),Spacer(1,10)]
    section('Key decisions',[[d.speaker,d.decision,f'{d.confidence:.0%}'] for d in result.decisions],['Speaker','Decision','Confidence'])
    section('Action items',[[a.owner,a.task,a.deadline,a.status] for a in result.action_items],['Owner','Task','Deadline','Status'])
    section('Risk flags',[[r.severity,r.risk,r.owner] for r in result.risks],['Severity','Risk','Owner'])
    section('Topic clusters',[[t.topic,t.summary,str(t.mentions)] for t in result.topics],['Topic','Summary','Mentions'])
    story += [Paragraph(f'Token usage: {ledger.total_tokens:,} estimated tokens · Estimated cost: ${ledger.total_cost:.4f}',styles['Tiny']),Spacer(1,8),Paragraph('AI-assisted notes must be reviewed by a meeting owner before distribution.',styles['Tiny'])]
    doc.build(story); out.seek(0); return out.getvalue()

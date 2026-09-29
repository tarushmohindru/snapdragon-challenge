"""Build the submission brief, diagram, and seven-slide deck from frozen copy.

No application inference or benchmark work is performed. Slide images are also
used in the PPTX so its layout matches the reviewed PDF exactly.
"""
from __future__ import annotations

from pathlib import Path
from io import BytesIO
import re
from PIL import Image, ImageDraw, ImageFont
from pptx import Presentation
from pptx.util import Inches
from docx import Document
from docx.shared import Inches as DocInches, Pt, RGBColor
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import Paragraph, Frame
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'final_submission'
ASSETS = OUT / 'assets'
ASSETS.mkdir(parents=True, exist_ok=True)
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
pdfmetrics.registerFont(TTFont('DejaVu', FONT))
pdfmetrics.registerFont(TTFont('DejaVu-Bold', BOLD))
W, H = 1600, 900
NAVY = '#0C172A'
NAVY2 = '#13243A'
WHITE = '#F6F8FC'
MUTED = '#ADC1D0'
CYAN = '#63D8D4'
LIME = '#C6F36A'
GOLD = '#FFC77B'


def font(size, bold=False):
    return ImageFont.truetype(BOLD if bold else FONT, size)


def rr(draw, box, fill, radius=22, outline=None, width=2):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def txt(draw, xy, value, size=28, color=WHITE, bold=False, maxw=None, spacing=13):
    x, y = xy
    f = font(size, bold)
    if maxw is None:
        draw.text((x, y), value, font=f, fill=color)
        return y + size + 8
    words = value.split()
    line = ''
    for word in words:
        next_line = (line + ' ' + word).strip()
        if line and draw.textlength(next_line, font=f) > maxw:
            draw.text((x, y), line, font=f, fill=color)
            y += size + spacing
            line = word
        else:
            line = next_line
    if line:
        draw.text((x, y), line, font=f, fill=color)
    return y + size + 8


def base(n, kicker, title, sub=None):
    im = Image.new('RGB', (W,H), NAVY)
    d = ImageDraw.Draw(im)
    d.rectangle((0,0,W,12), fill=CYAN)
    txt(d,(70,56),kicker.upper(),22,CYAN,True)
    txt(d,(70,105),title,53,WHITE,True)
    if sub: txt(d,(70,185),sub,25,MUTED,maxw=1420)
    d.line((70,830,1530,830),fill='#345066',width=2)
    txt(d,(70,846),'ClipTrail  •  Private, scene-aware search for local video',17,MUTED)
    txt(d,(1480,846),f'{n:02d} / 07',17,MUTED)
    return im,d


def card(d, box, head, body, accent=CYAN):
    rr(d,box,NAVY2,24,outline='#345066')
    x1,y1,x2,y2=box
    d.rectangle((x1+26,y1+32,x1+34,y1+86),fill=accent)
    txt(d,(x1+54,y1+31),head,28,WHITE,True)
    txt(d,(x1+54,y1+88),body,23,MUTED,maxw=x2-x1-95)


def arrow(d,x,y):
    d.line((x,y,x+36,y),fill=CYAN,width=5)
    d.polygon([(x+36,y-11),(x+54,y),(x+36,y+11)],fill=CYAN)


def architecture():
    im=Image.new('RGB',(1800,890),NAVY)
    d=ImageDraw.Draw(im)
    txt(d,(70,38),'CANONICAL ARCHITECTURE',26,CYAN,True)
    txt(d,(70,85),'Verified product path · fully local CPU application',42,WHITE,True)
    upper=[('LOCAL INPUT','Video or folder'),('DECODE','4 Hz samples'),('SCENE SELECT','Change + midpoints'),('EMBED','CLIP image'),('PERSIST','SQLite vectors,\nJPEGs, timestamps')]
    x=70
    widths=[260,260,300,270,440]
    for i,((head,body),wid) in enumerate(zip(upper,widths)):
        rr(d,(x,180,x+wid,300),NAVY2,18,outline='#417086')
        txt(d,(x+18,199),head,20,CYAN,True)
        for j,line in enumerate(body.split('\n')): txt(d,(x+18,235+j*27),line,21,WHITE)
        x+=wid+28
        if i<4: arrow(d,x-25,240)
    d.line((1460,300,1460,350),fill=CYAN,width=5)
    d.line((1460,350,450,350),fill=CYAN,width=5)
    d.line((450,350,450,380),fill=CYAN,width=5)
    lower=[('TEXT QUERY','CLIP text vector'),('RANK','Cosine similarity'),('RESULT','Thumbnail + score\nfilename + timestamp'),('PLAY','Original local video\nat saved timestamp')]
    x=70
    widths=[330,325,385,440]
    for i,((head,body),wid) in enumerate(zip(lower,widths)):
        rr(d,(x,380,x+wid,510),NAVY2,18,outline='#417086')
        txt(d,(x+18,401),head,20,CYAN,True)
        for j,line in enumerate(body.split('\n')): txt(d,(x+18,439+j*28),line,21,WHITE)
        x+=wid+30
        if i<3: arrow(d,x-26,445)
    rr(d,(70,580,1730,808),'#182235',20,outline='#6A5463')
    txt(d,(98,605),'EXPERIMENTAL IMAGE BACKEND · SEPARATE EVIDENCE SCOPE',26,GOLD,True)
    txt(d,(98,659),'Windows ARM64 → ONNX Runtime QNN → pinned HTP backend → provider-level graph execution',27,WHITE)
    txt(d,(98,713),'Observed: provider loading, HTP loading, QNN partition, embedding parity.',22,MUTED)
    txt(d,(98,753),'Physical NPU device execution, acceleration, and full target application deployment remain unverified.',21,GOLD,True)
    im.save(ASSETS/'architecture.png')


def slides():
    frames=[]
    # 1: actual saved frame, not fabricated app screenshot
    im,d=base(1,'Working local product','ClipTrail','Private, scene-aware search for local video')
    txt(d,(75,292),'Describe a scene. Jump to the moment.\nKeep every video local.',40,WHITE,True)
    rr(d,(70,555,800,690),NAVY2,24,outline='#3A6979')
    txt(d,(100,579),'Natural-language query',21,CYAN,True)
    txt(d,(100,619),'“A red-haired woman surrounded by burning rubble.”',24,WHITE,maxw=660)
    rr(d,(860,245,1510,710),NAVY2,25,outline='#417086')
    thumb=Image.open(ROOT/'experiments/cliptrail_app/results/persistent-demo/thumbnails/7.jpg').convert('RGB')
    thumb=thumb.resize((596,335),Image.Resampling.LANCZOS)
    im.paste(thumb,(887,272))
    txt(d,(890,620),'Sintel  ·  23.25 s  ·  saved local result',23,WHITE,True)
    txt(d,(890,658),'Frame: Blender Foundation / Sintel (CC BY 3.0)',17,MUTED)
    frames.append(im)
    # 2
    im,d=base(2,'Problem','The moment is buried inside the file','A filename cannot describe every visual event in a video.')
    card(d,(70,285,760,590),'Manual scrubbing','Finding one moment means opening files and searching the timeline by eye.',GOLD)
    card(d,(815,285,1510,590),'Cloud tradeoff','Remote indexing requires media upload and ongoing external storage.',CYAN)
    txt(d,(90,662),'The user wants a timestamped moment — with the source kept under local control.',29,WHITE,True,maxw=1370)
    frames.append(im)
    # 3
    im,d=base(3,'Solution','Index scenes once. Search them repeatedly.','A compact local visual index turns a plain-language description into a playable moment.')
    steps=[('01','Select','One video or a folder'),('02','Index','Representative scene frames'),('03','Search','Natural-language CLIP query'),('04','Play','Ranked timestamped result')]
    x=70
    for i,(num,head,body) in enumerate(steps):
        rr(d,(x,315,x+340,610),NAVY2,25,outline='#417086')
        txt(d,(x+27,343),num,24,CYAN,True)
        txt(d,(x+27,414),head,37,WHITE,True)
        txt(d,(x+27,489),body,21,MUTED,maxw=280)
        if i<3: arrow(d,x+345,459)
        x+=373
    txt(d,(70,683),'Videos, embeddings, queries, and playback stay on the same computer.',27,LIME,True)
    frames.append(im)
    # 4
    im,d=base(4,'Architecture','Sparse, persistent, local','The verified CPU application path and experimental QNN image path are distinct.')
    arch=Image.open(ASSETS/'architecture.png').convert('RGB')
    arch=arch.crop((35,140,1765,825)).resize((1450,574),Image.Resampling.LANCZOS)
    im.paste(arch,(70,232))
    frames.append(im)
    # 5
    im,d=base(5,'Evidence','Measured on the recorded CPU host','Frozen retrieval benchmark and persistent application diagnostics have different scopes.')
    values=[('87.50%','Recall@3','24 positive queries · 2 films'),('81.82%','Short-event R@3','11 positive queries'),('27.45 ms','Warm search median','5 repeat queries · prebuilt index'),('6.80 s','Index / video minute','After model load'),('~250 KB','Logical index / minute','Vectors + JPEG thumbnails')]
    positions=[(70,285,520,500),(555,285,1005,500),(1040,285,1510,500),(300,530,785,745),(815,530,1300,745)]
    for (big,label,scope),box in zip(values,positions):
        rr(d,box,NAVY2,22,outline='#3C6879')
        x1,y1,*_=box
        txt(d,(x1+26,y1+25),big,42,LIME,True)
        txt(d,(x1+26,y1+98),label,23,WHITE,True)
        txt(d,(x1+26,y1+143),scope,17,MUTED)
    txt(d,(75,782),'CPU: AMD Ryzen 5 5600H · WSL2/Linux · one recorded three-video application run',18,MUTED)
    frames.append(im)
    # 6
    im,d=base(6,'Snapdragon / QNN','Provider-level compatibility observed','One fixed CLIP image graph smoke on an ASUS Snapdragon X2 Elite.')
    card(d,(70,275,760,700),'Observed','Native ARM64 graph execution; QNN provider and pinned HTP libraries loaded; one QNN partition; CPU-reference embedding parity (cosine 0.999982834).',CYAN)
    card(d,(810,275,1510,700),'Unverified','Physical NPU device execution; speedup or energy advantage; production stability; full ClipTrail or HP-device deployment.',GOLD)
    txt(d,(80,740),'Hardware profiler device events were absent. The backend remains experimental.',24,GOLD,True)
    frames.append(im)
    # 7
    im,d=base(7,'Closing','Private video becomes searchable','A working local product with measured sparse retrieval and a precise future ARM64/QNN path.')
    rr(d,(70,275,1510,620),NAVY2,28,outline='#4B8C8D')
    txt(d,(118,327),'Describe a scene.',48,WHITE,True)
    txt(d,(118,410),'Jump to the moment.',48,CYAN,True)
    txt(d,(118,493),'Keep every video local.',48,LIME,True)
    txt(d,(73,685),'Working now: persistent CPU application  •  Future work: broader evaluation and device-level QNN proof',23,MUTED,maxw=1430)
    frames.append(im)
    return frames


def make_deck(frames):
    prs=Presentation()
    prs.slide_width=Inches(13.333)
    prs.slide_height=Inches(7.5)
    pdf=canvas.Canvas(str(OUT/'ClipTrail-Pitch.pdf'),pagesize=(960,540))
    notes=[
        'Video filenames cannot tell us what happens inside a recording. ClipTrail lets people search private videos without uploading them.',
        'The user needs a moment, not another file list. ClipTrail addresses visual events that are buried in the source.',
        'The application indexes representative scenes once, then searches saved vectors locally and opens the source at the result timestamp.',
        'The CPU path is the verified product. The Windows ARM64 QNN image backend is experimental and has separate evidence.',
        'Quality is from a small frozen positive-query corpus. Application speed and size are from one recorded CPU host, not Snapdragon.',
        'Native ARM64 QNN graph execution, HTP loading, partitioning and parity were observed. Physical NPU execution was not verified.',
        'ClipTrail is useful today as private video search. Broader evaluation and device-level QNN proof are future work.'
    ]
    for idx,im in enumerate(frames,1):
        buffer=BytesIO()
        im.save(buffer,format='PNG',optimize=True)
        buffer.seek(0)
        slide=prs.slides.add_slide(prs.slide_layouts[6])
        slide.shapes.add_picture(buffer,0,0,width=prs.slide_width,height=prs.slide_height)
        slide.notes_slide.notes_text_frame.text=notes[idx-1]
        pdf.drawImage(ImageReader(im),0,0,960,540)
        pdf.showPage()
    prs.save(OUT/'ClipTrail-Pitch.pptx')
    pdf.save()


def brief_content():
    raw=(ROOT/'submission/brief-project-description.md').read_text()
    paras=[p.strip() for p in raw.split('\n\n') if p.strip()]
    title=paras[1].replace('## ','')
    body=paras[2:]
    return title,body


def make_brief():
    title,body=brief_content()
    doc=Document()
    sec=doc.sections[0]
    sec.top_margin=DocInches(.75); sec.bottom_margin=DocInches(.65)
    sec.left_margin=DocInches(.75); sec.right_margin=DocInches(.75)
    normal=doc.styles['Normal']; normal.font.name='DejaVu Sans'; normal.font.size=Pt(9)
    normal.paragraph_format.space_after=Pt(8)
    p=doc.add_paragraph('BRIEF PROJECT DESCRIPTION')
    p.style='Subtitle'; p.runs[0].font.color.rgb=RGBColor(14,117,126)
    p=doc.add_heading(title,0)
    p.runs[0].font.name='DejaVu Sans'; p.runs[0].font.size=Pt(20)
    p=doc.add_paragraph('Describe a scene. Jump to the moment. Keep every video local.')
    p.runs[0].bold=True; p.runs[0].font.color.rgb=RGBColor(14,117,126)
    for i,paragraph in enumerate(body):
        p=doc.add_paragraph(paragraph)
        p.paragraph_format.space_after=Pt(8)
        for run in p.runs: run.font.name='DejaVu Sans'; run.font.size=Pt(9)
    sec.footer.paragraphs[0].text='ClipTrail  •  Local CPU application  •  Physical NPU execution unverified'
    doc.save(OUT/'ClipTrail-Brief-Project-Description.docx')
    # The PDF uses the same authoritative paragraph sequence; fixed one-page A4.
    c=canvas.Canvas(str(OUT/'ClipTrail-Brief-Project-Description.pdf'),pagesize=A4)
    pw,ph=A4
    c.setFillColor(HexColor(NAVY)); c.rect(0,ph-130,pw,130,fill=1,stroke=0)
    c.setFont('DejaVu-Bold',10); c.setFillColor(HexColor(CYAN)); c.drawString(48,ph-43,'BRIEF PROJECT DESCRIPTION')
    c.setFont('DejaVu-Bold',17); c.setFillColor(HexColor(WHITE)); c.drawString(48,ph-73,'ClipTrail')
    c.setFont('DejaVu',12); c.drawString(48,ph-93,'Private, Scene-Aware Search for Local Video')
    c.setFont('DejaVu',9); c.setFillColor(HexColor(CYAN)); c.drawString(48,ph-113,'Describe a scene. Jump to the moment. Keep every video local.')
    style=ParagraphStyle('body',fontName='DejaVu',fontSize=8.75,leading=13.5,textColor=HexColor('#17243B'),spaceAfter=10)
    flow=[Paragraph(p.replace('&','&amp;'),style) for p in body]
    frame=Frame(48,49,pw-96,ph-197,leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0,showBoundary=0)
    frame.addFromList(flow,c)
    if flow: raise RuntimeError(f'Brief overflow: {len(flow)} paragraphs')
    c.setStrokeColor(HexColor('#AEC9CB')); c.line(48,40,pw-48,40)
    c.setFont('DejaVu',7.5); c.setFillColor(HexColor('#526679'))
    c.drawString(48,27,'CPU application measurements; Snapdragon compatibility is provider-level. See docs/evidence.md.')
    c.save()


if __name__=='__main__':
    architecture()
    make_deck(slides())
    make_brief()
    print('Built brief, deck, and architecture assets in',OUT)

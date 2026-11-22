"""Optional document build; requires reportlab. Does not affect app dependencies."""
import re
from html import escape
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


root = Path(__file__).resolve().parents[1]
output = root / 'output' / 'pdf' / 'automation-copilot-write-up.pdf'
output.parent.mkdir(parents=True, exist_ok=True)
green = colors.HexColor('#087f5b')
styles = {
    'eyebrow': ParagraphStyle('eyebrow', fontName='Helvetica-Bold', fontSize=8, leading=12, textColor=green, spaceAfter=13),
    'title': ParagraphStyle('title', fontName='Helvetica-Bold', fontSize=25, leading=30, textColor=colors.HexColor('#183d31'), spaceAfter=23),
    'body': ParagraphStyle('body', fontName='Helvetica', fontSize=10, leading=14.7, textColor=colors.HexColor('#3d5148'), spaceAfter=15, alignment=TA_LEFT),
}


def footer(canvas, doc):
    canvas.setStrokeColor(colors.HexColor('#dce6dc'))
    canvas.line(46, 44, A4[0] - 46, 44)
    canvas.setFillColor(colors.HexColor('#819585'))
    canvas.setFont('Helvetica', 8)
    canvas.drawString(46, 30, 'WATI TAKE-HOME  /  Architecture, quality and trade-offs')
    canvas.drawRightString(A4[0] - 46, 30, str(doc.page))


text = (root / 'docs' / 'write-up.md').read_text(encoding='utf-8')
blocks = text.strip().split('\n\n')
story = [Paragraph('AGENTIC BACKEND ENGINEERING · TAKE-HOME', styles['eyebrow']), Paragraph(escape(blocks[0].lstrip('# ')), styles['title'])]
for block in blocks[1:]:
    formatted = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', escape(block.replace('\n', ' ')))
    story.append(Paragraph(formatted, styles['body']))
SimpleDocTemplate(str(output), pagesize=A4, leftMargin=46, rightMargin=46, topMargin=43, bottomMargin=62, title='Automation Builder Copilot — Take-home write-up', author='Wati take-home project').build(story, onFirstPage=footer, onLaterPages=footer)
print(output)

import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Image, Table, TableStyle, HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

# ── Colors ────────────────────────────────────────────────────
PRIMARY  = colors.HexColor("#4C6EF5")
ACCENT   = colors.HexColor("#9775FA")
TEXT     = colors.HexColor("#1A1A2E")
GRAY     = colors.HexColor("#6B6F8A")
BG       = colors.HexColor("#F4F5FF")
SUCCESS  = colors.HexColor("#2F9E44")
ORANGE   = colors.HexColor("#E67700")
WHITE    = colors.white
BORDER   = colors.HexColor("#D0D4F0")


def _s(name, **kw):
    defaults = dict(fontName="Helvetica", fontSize=10,
                    textColor=TEXT, leading=15, spaceAfter=0)
    defaults.update(kw)
    return ParagraphStyle(name, **defaults)


STYLES = {
    "title":    _s("title",    fontName="Helvetica-Bold", fontSize=18,
                               textColor=TEXT, spaceAfter=6, leading=22),
    "tagline":  _s("tagline",  fontSize=9,  textColor=GRAY, spaceAfter=4,
                               leading=14),
    "ts":       _s("ts",       fontSize=8,  textColor=GRAY, spaceAfter=0),
    "sec_hdr":  _s("sec_hdr", fontName="Helvetica-Bold", fontSize=10,
                               textColor=PRIMARY, spaceAfter=6, spaceBefore=14),
    "question": _s("question", fontName="Helvetica-BoldOblique", fontSize=11,
                               textColor=PRIMARY),
    "body":     _s("body",     fontSize=10, textColor=TEXT,
                               leading=16, spaceAfter=3),
    "bullet":   _s("bullet",   fontSize=10, textColor=TEXT,
                               leading=15, leftIndent=12, spaceAfter=2),
    "footer":   _s("footer",   fontSize=8,  textColor=GRAY,
                               alignment=TA_CENTER),
    "sec_label":_s("sec_label",fontName="Helvetica-Bold", fontSize=10,
                               textColor=WHITE),
}


def _section_block(label, content, color, usable_w):
    """Build a colored header + content block that stays together."""
    items = []

    # Colored header
    hdr = Table(
        [[Paragraph(label, STYLES["sec_label"])]],
        colWidths=[usable_w]
    )
    hdr.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), color),
        ("TOPPADDING",    (0,0), (-1,-1), 7),
        ("BOTTOMPADDING", (0,0), (-1,-1), 7),
        ("LEFTPADDING",   (0,0), (-1,-1), 14),
        ("RIGHTPADDING",  (0,0), (-1,-1), 14),
    ]))
    items.append(hdr)

    # Content
    paras = []
    for line in content.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        if line.startswith(("*", "-", "•")):
            line = "• " + line.lstrip("*-• ").strip()
            paras.append(Paragraph(line, STYLES["bullet"]))
        else:
            paras.append(Paragraph(line, STYLES["body"]))

    body = Table(
        [[paras]],
        colWidths=[usable_w]
    )
    body.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), BG),
        ("TOPPADDING",    (0,0), (-1,-1), 10),
        ("BOTTOMPADDING", (0,0), (-1,-1), 10),
        ("LEFTPADDING",   (0,0), (-1,-1), 14),
        ("RIGHTPADDING",  (0,0), (-1,-1), 14),
        ("BOX",           (0,0), (-1,-1), 0.5, BORDER),
    ]))
    items.append(body)
    items.append(Spacer(1, 8))

    return KeepTogether(items)


def _parse(narrative):
    out = {"summary": "", "key_numbers": "", "insight": "", "recommendation": ""}
    cur = None
    for line in narrative.split("\n"):
        l = line.strip()
        low = l.lower()
        if l.startswith("#"):
            if "summary"        in low: cur = "summary"
            elif "key number"   in low: cur = "key_numbers"
            elif "insight"      in low: cur = "insight"
            elif "recommendation" in low: cur = "recommendation"
        elif cur and l:
            out[cur] += l + "\n"
    return out


def generate_pdf(question, narrative, chart_paths,
                 output_path="data/insight_report.pdf"):

    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=0.8*inch, rightMargin=0.8*inch,
        topMargin=0.8*inch,  bottomMargin=0.8*inch,
    )

    W, H     = A4
    usable_w = W - 1.6 * inch
    story    = []

    # ── Header block ──────────────────────────────────────────
    header_data = [[
        Paragraph("AnalystGPT", STYLES["title"]),
        Paragraph(
            datetime.now().strftime("%d %b %Y, %I:%M %p"),
            ParagraphStyle("ts_r", fontName="Helvetica", fontSize=9,
                           textColor=GRAY, alignment=TA_RIGHT)
        )
    ]]
    header_tbl = Table(header_data, colWidths=[usable_w * 0.7, usable_w * 0.3])
    header_tbl.setStyle(TableStyle([
        ("VALIGN",        (0,0), (-1,-1), "BOTTOM"),
        ("LEFTPADDING",   (0,0), (-1,-1), 0),
        ("RIGHTPADDING",  (0,0), (-1,-1), 0),
        ("TOPPADDING",    (0,0), (-1,-1), 0),
        ("BOTTOMPADDING", (0,0), (-1,-1), 0),
    ]))
    story.append(header_tbl)
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "Autonomous Data Analyst Agent  ·  AI-Generated Insight Report",
        STYLES["tagline"]
    ))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=2,
                             color=PRIMARY, spaceAfter=12))

    # ── Question ──────────────────────────────────────────────
    story.append(Paragraph("Question Asked", STYLES["sec_hdr"]))
    q_tbl = Table(
        [[Paragraph(f'"{question}"', STYLES["question"])]],
        colWidths=[usable_w]
    )
    q_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), BG),
        ("TOPPADDING",    (0,0), (-1,-1), 12),
        ("BOTTOMPADDING", (0,0), (-1,-1), 12),
        ("LEFTPADDING",   (0,0), (-1,-1), 16),
        ("RIGHTPADDING",  (0,0), (-1,-1), 16),
        ("BOX",           (0,0), (-1,-1), 1.5, PRIMARY),
    ]))
    story.append(q_tbl)
    story.append(Spacer(1, 10))

    # ── Chart ─────────────────────────────────────────────────
    valid = [cp for cp in chart_paths if cp and os.path.exists(
        cp.replace("\\", "/"))]
    if valid:
        story.append(Paragraph("Generated Chart", STYLES["sec_hdr"]))
        for cp in valid:
            cp = cp.replace("\\", "/")
            chart_h = usable_w * 0.42
            img     = Image(cp, width=usable_w - 16, height=chart_h)
            img.hAlign = "CENTER"
            img_tbl = Table([[img]], colWidths=[usable_w])
            img_tbl.setStyle(TableStyle([
                ("BACKGROUND",    (0,0), (-1,-1), BG),
                ("TOPPADDING",    (0,0), (-1,-1), 8),
                ("BOTTOMPADDING", (0,0), (-1,-1), 8),
                ("LEFTPADDING",   (0,0), (-1,-1), 8),
                ("RIGHTPADDING",  (0,0), (-1,-1), 8),
                ("BOX",           (0,0), (-1,-1), 0.5, BORDER),
            ]))
            story.append(img_tbl)
        story.append(Spacer(1, 10))

    # ── Narrative ─────────────────────────────────────────────
    story.append(Paragraph("Insight Report", STYLES["sec_hdr"]))

    parsed = _parse(narrative)
    sections = [
        ("📌  Summary",        "summary",        SUCCESS),
        ("📊  Key Numbers",    "key_numbers",     PRIMARY),
        ("💡  Insight",        "insight",         ACCENT),
        ("✅  Recommendation", "recommendation",  ORANGE),
    ]

    for label, key, color in sections:
        content = parsed.get(key, "").strip()
        if content:
            story.append(_section_block(label, content, color, usable_w))

    # ── Footer ────────────────────────────────────────────────
    story.append(Spacer(1, 12))
    story.append(HRFlowable(width="100%", thickness=0.5,
                             color=BORDER, spaceAfter=6))
    story.append(Paragraph(
        "Generated by AnalystGPT  ·  Powered by LLaMA 3.3 70B via Groq  ·  "
        "Built with ReAct Agentic Framework",
        STYLES["footer"]
    ))

    doc.build(story)
    return output_path
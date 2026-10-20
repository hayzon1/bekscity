"""
BEKSCITY RUN CLUB — Brand Partnership & Sponsorship Proposal Generator
Generates a formal, high-impact sponsorship proposal PDF for prospective brands and partners.
"""

import os
import json
import datetime as dt
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, white
from reportlab.lib.utils import simpleSplit

HERE = os.path.dirname(os.path.abspath(__file__))

CLUB = "BEKSCITY RUN CLUB"
INK = HexColor("#1b1b1f")
ACC = HexColor("#e8501f")
SOFT = HexColor("#f4f1ec")
MUTE = HexColor("#6b6b73")
GOLD = HexColor("#fff1c9")
GOLDB = HexColor("#e0a800")
GREEN = HexColor("#287D58")
LINE = HexColor("#c9c4bb")

FONT = "Helvetica"
FONTB = "Helvetica-Bold"
W, H = letter


def draw_para(c, text, x, y, w, size=9, lead=12, col=INK, font=FONT):
    c.setFont(font, size)
    c.setFillColor(col)
    for ln in simpleSplit(str(text or ""), font, size, w):
        c.drawString(x, y, ln)
        y -= lead
    return y


def build_proposal_pdf(output_path, proposal_data):
    """
    Builds a formal 2-page sponsorship proposal PDF.
    """
    c = canvas.Canvas(output_path, pagesize=letter)
    c.setTitle(f"BCRC Proposal — {proposal_data.get('brand_name', 'Brand Partnership')}")
    c.setAuthor(CLUB)

    # PAGE 1: PITCH & VALUE PROPOSITION
    # Header Banner
    c.setFillColor(INK)
    c.rect(0, H - 90, W, 90, fill=1, stroke=0)
    c.setFillColor(ACC)
    c.rect(0, H - 94, W, 4, fill=1, stroke=0)

    c.setFillColor(white)
    c.setFont(FONTB, 20)
    c.drawString(40, H - 46, f"{CLUB}")
    c.setFont(FONTB, 12)
    c.setFillColor(HexColor("#e0a800"))
    c.drawString(40, H - 64, "OFFICIAL PARTNERSHIP & SPONSORSHIP PROPOSAL")
    c.setFont(FONT, 9)
    c.setFillColor(HexColor("#cfcfd6"))
    c.drawString(40, H - 80, f"Prepared exclusively for: {proposal_data.get('brand_name', 'Brand Partner').upper()} | Date: {dt.date.today().strftime('%B %d, %Y')}")

    # Executive Summary Card
    y = H - 120
    c.setFillColor(GOLD)
    c.setStrokeColor(GOLDB)
    c.setLineWidth(1.5)
    c.roundRect(40, y - 76, 532, 76, 8, fill=1, stroke=1)
    c.setFillColor(GOLDB)
    c.rect(40, y - 24, 532, 24, fill=1, stroke=0)

    c.setFillColor(INK)
    c.setFont(FONTB, 11)
    c.drawString(54, y - 16, f"PROPOSAL OVERVIEW: {proposal_data.get('brand_name', '').upper()} × {CLUB}")

    c.setFont(FONT, 8.5)
    c.drawString(54, y - 38, f"Target Event: {proposal_data.get('event_name', 'Weekly Signature Event')}")
    c.drawString(54, y - 52, f"Partnership Tier: {proposal_data.get('partnership_tier', 'Headline Sponsor')}")
    c.drawString(54, y - 66, f"Commercial / Support Value: {proposal_data.get('value_amount', 'Terms per agreement')}")

    status = (proposal_data.get('status') or 'DRAFT').upper()
    c.setFont(FONTB, 9)
    c.setFillColor(GREEN if status == 'ACCEPTED' else ACC)
    c.drawRightString(556, y - 48, f"STATUS: {status}")

    y -= 94

    # 1. Why Partner with BEKSCITY RUN CLUB
    c.setFont(FONTB, 13)
    c.setFillColor(INK)
    c.drawString(40, y, "1. ABOUT BEKSCITY RUN CLUB & AUDIENCE IMPACT")
    c.setStrokeColor(ACC)
    c.setLineWidth(1.5)
    c.line(40, y - 4, 340, y - 4)
    y -= 18

    about_text = (
        "BEKSCITY RUN CLUB (BCRC) is the premier active lifestyle, wellness, and community running movement in "
        "Abeokuta, Ogun State. Every Saturday morning, our runners convene across four key demographic districts: "
        "Mile District (Moore junction), Pharmafit District (Kemta junction), Panseke District (Skating ground), and "
        "Funaab District (Funaab gate).\n\n"
        "Our membership comprises young professionals, entrepreneurs, university students, and health-conscious "
        "trendsetters who are deeply engaged with fitness, nutrition, and premium lifestyle brands. Partnering with BCRC "
        "provides your brand with direct experiential engagement, on-ground product trials, and authentic social amplification."
    )
    y = draw_para(c, about_text, 40, y, 532, size=9, lead=13) - 8

    # 2. Strategic Partnership Objectives
    c.setFont(FONTB, 13)
    c.setFillColor(INK)
    c.drawString(40, y, "2. PARTNERSHIP OBJECTIVES & PITCH HOOK")
    c.setStrokeColor(ACC)
    c.line(40, y - 4, 300, y - 4)
    y -= 18

    pitch_hook = proposal_data.get("pitch_hook") or (
        f"Position {proposal_data.get('brand_name')} as the official wellness partner of BEKSCITY RUN CLUB, "
        "delivering memorable on-ground brand experiences, consumer loyalty, and dominant visual visibility."
    )
    y = draw_para(c, pitch_hook, 40, y, 532, size=9, lead=13) - 10

    # 3. Deliverables & Brand Exposure
    c.setFont(FONTB, 13)
    c.setFillColor(INK)
    c.drawString(40, y, "3. SPONSORSHIP DELIVERABLES & COMMITMENTS")
    c.setStrokeColor(ACC)
    c.line(40, y - 4, 320, y - 4)
    y -= 18

    deliverables = proposal_data.get("deliverables") or ""
    if not deliverables:
        deliverables = (
            "• Physical Branding: Prominent feather banner, roll-up banner & start/finish line placement.\n"
            "• Direct Activation: Sampling booth & member engagement zone at Moore junction finish line.\n"
            "• Digital & Media: Co-branded event flyers, digital calendar inclusion, 3 Instagram Reels, and photography library.\n"
            "• Exclusive Access: Product sampling, giveaway announcements & VIP runner discount code integration."
        )
    y = draw_para(c, deliverables, 40, y, 532, size=8.5, lead=12) - 14

    # 4. Brand Benefits & Commercial Terms
    c.setFont(FONTB, 13)
    c.setFillColor(INK)
    c.drawString(40, y, "4. COMMERCIAL TERMS & NEXT STEPS")
    c.setStrokeColor(ACC)
    c.line(40, y - 4, 280, y - 4)
    y -= 18

    benefits = proposal_data.get("brand_benefits") or (
        f"Value Contribution: {proposal_data.get('value_amount', 'Mutually agreed terms')}.\n"
        "To confirm and activate this sponsorship, endorse below or contact the BCRC Co-founders team."
    )
    y = draw_para(c, benefits, 40, y, 532, size=8.5, lead=12) - 20

    # 5. Sign-off / Co-founders Contact
    c.setFillColor(SOFT)
    c.roundRect(40, y - 70, 532, 70, 6, fill=1, stroke=0)
    c.setFillColor(INK)
    c.setFont(FONTB, 9.5)
    c.drawString(54, y - 16, "BEKSCITY RUN CLUB — CO-FOUNDERS LEADERSHIP TEAM")

    c.setFont(FONT, 8)
    c.drawString(54, y - 32, "• Oladipupo Abdulazeez (08101674646 | @jughead_x3)")
    c.drawString(54, y - 46, "• Shittu Oluwadamilare (08168120117 | @sweetboycoal)")
    c.drawString(54, y - 60, "• Adebanjo Oluwatobiloba (07069582118 | @tobenzin)")

    c.drawRightString(556, y - 32, "Abeokuta, Ogun State, Nigeria")
    c.drawRightString(556, y - 46, "Email: partnerships@bekscity.run")
    c.drawRightString(556, y - 60, "Website: bekscity.run")

    c.showPage()
    c.save()
    return output_path

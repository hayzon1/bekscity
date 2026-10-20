"""
BEKSCITY RUN CLUB — Event Itinerary & Operations Run Sheet Builder
Generates a printable, professional 1-to-2 page PDF operations run sheet
for race directors, pacer leads, volunteers, and logistics coordinators.
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


def build_itinerary_pdf(output_path, itinerary_data):
    """
    Builds a crisp, high-visibility operational run sheet.
    """
    c = canvas.Canvas(output_path, pagesize=letter)
    c.setTitle(f"BCRC Operations Sheet — {itinerary_data.get('title', 'Event Itinerary')}")
    c.setAuthor(CLUB)

    # 1. Header Banner
    c.setFillColor(INK)
    c.rect(0, H - 80, W, 80, fill=1, stroke=0)
    c.setFillColor(ACC)
    c.rect(0, H - 84, W, 4, fill=1, stroke=0)

    c.setFillColor(white)
    c.setFont(FONTB, 18)
    c.drawString(40, H - 42, f"{CLUB} — OPERATIONAL RUN SHEET")
    c.setFont(FONT, 10)
    c.setFillColor(HexColor("#cfcfd6"))
    sub = f"Event: {itinerary_data.get('title')} | Date: {itinerary_data.get('date')} | Africa/Lagos (WAT)"
    c.drawString(40, H - 62, sub)

    # 2. Key Information Bar
    y = H - 110
    c.setFillColor(SOFT)
    c.roundRect(40, y - 56, 532, 56, 6, fill=1, stroke=0)
    c.setFillColor(GREEN)
    c.rect(40, y - 56, 6, 56, fill=1, stroke=0)

    # Left Column
    c.setFont(FONTB, 9)
    c.setFillColor(INK)
    c.drawString(54, y - 16, f"Meeting Point:")
    c.setFont(FONT, 9)
    c.drawString(130, y - 16, str(itinerary_data.get("meeting_point", "TBC")))

    c.setFont(FONTB, 9)
    c.drawString(54, y - 32, f"Distance & Course:")
    c.setFont(FONT, 9)
    c.drawString(146, y - 32, f"{itinerary_data.get('distance', 'N/A')} — {itinerary_data.get('route_summary', 'Standard loop')[:55]}")

    c.setFont(FONTB, 9)
    c.drawString(54, y - 48, f"Lead Coordinator:")
    c.setFont(FONT, 9)
    c.drawString(146, y - 48, str(itinerary_data.get("lead_organizer", "Organising Committee")))

    # Right Column
    c.setFont(FONTB, 9)
    c.drawString(380, y - 16, f"Co-founders Hotline:")
    c.setFont(FONT, 8.5)
    c.drawString(380, y - 30, "08101674646 (Abdulazeez)")
    c.drawString(380, y - 44, "08168120117 (Damilare) | 07069582118 (Tobi)")

    y -= 74

    # 3. Minute-by-Minute Run Timeline
    c.setFont(FONTB, 12)
    c.setFillColor(INK)
    c.drawString(40, y, "MINUTE-BY-MINUTE TIMELINE")
    c.setStrokeColor(ACC)
    c.setLineWidth(1.5)
    c.line(40, y - 4, 210, y - 4)
    y -= 18

    # Table Header
    c.setFillColor(INK)
    c.rect(40, y - 16, 532, 16, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont(FONTB, 8)
    c.drawString(46, y - 12, "TIME")
    c.drawString(110, y - 12, "OPERATIONAL ACTION / MILESTONE")
    c.drawString(340, y - 12, "LEAD / MARSHAL")
    c.drawString(450, y - 12, "LOGISTICS & NOTES")
    y -= 20

    timeline = itinerary_data.get("timeline") or []
    if isinstance(timeline, str):
        try:
            timeline = json.loads(timeline)
        except Exception:
            timeline = []

    for idx, item in enumerate(timeline):
        bg = white if (idx % 2 == 0) else SOFT
        c.setFillColor(bg)
        c.rect(40, y - 18, 532, 18, fill=1, stroke=0)

        # Draw time
        c.setFont(FONTB, 8)
        c.setFillColor(ACC)
        c.drawString(46, y - 13, str(item.get("time", "")))

        # Draw activity
        c.setFont(FONT, 8)
        c.setFillColor(INK)
        act_text = str(item.get("activity", ""))
        c.drawString(110, y - 13, act_text[:50])

        # Draw lead
        lead_text = str(item.get("lead", "Marshals"))
        c.drawString(340, y - 13, lead_text[:22])

        # Draw notes
        notes_text = str(item.get("notes", ""))
        c.setFont(FONT, 7.5)
        c.setFillColor(MUTE)
        c.drawString(450, y - 13, notes_text[:28])

        y -= 20

    y -= 10

    # 4. Checkpoints & Hydration Stations
    c.setFont(FONTB, 12)
    c.setFillColor(INK)
    c.drawString(40, y, "ROUTE CHECKPOINTS & HYDRATION STATIONS")
    c.setStrokeColor(ACC)
    c.line(40, y - 4, 300, y - 4)
    y -= 18

    checkpoints = itinerary_data.get("route_checkpoints") or []
    if isinstance(checkpoints, str):
        try:
            checkpoints = json.loads(checkpoints)
        except Exception:
            checkpoints = []

    c.setFillColor(INK)
    c.rect(40, y - 16, 532, 16, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont(FONTB, 8)
    c.drawString(46, y - 12, "STOP #")
    c.drawString(90, y - 12, "CHECKPOINT LOCATION")
    c.drawString(250, y - 12, "FUNCTION / AMENITIES")
    c.drawString(420, y - 12, "MARSHAL ON DUTY")
    y -= 20

    for idx, cp in enumerate(checkpoints):
        bg = white if (idx % 2 == 0) else SOFT
        c.setFillColor(bg)
        c.rect(40, y - 18, 532, 18, fill=1, stroke=0)

        c.setFont(FONTB, 8)
        c.setFillColor(GREEN)
        c.drawString(46, y - 13, f"Stop {cp.get('stop', idx+1)}")

        c.setFont(FONTB, 8)
        c.setFillColor(INK)
        c.drawString(90, y - 13, str(cp.get("name", ""))[:32])

        c.setFont(FONT, 8)
        c.drawString(250, y - 13, str(cp.get("type", "Hydration & Regroup"))[:35])

        c.setFont(FONT, 8)
        c.setFillColor(MUTE)
        c.drawString(420, y - 13, str(cp.get("marshal", "Volunteer Team"))[:25])

        y -= 20

    y -= 12

    # 5. Safety, Medical & Logistics Summary
    c.setFont(FONTB, 11)
    c.setFillColor(INK)
    c.drawString(40, y, "SAFETY, MEDICAL PROTOCOLS & LOGISTICS CHECKLIST")
    c.setStrokeColor(ACC)
    c.line(40, y - 4, 340, y - 4)
    y -= 16

    c.setFillColor(SOFT)
    c.roundRect(40, y - 62, 532, 62, 6, fill=1, stroke=0)
    c.setFillColor(GOLDB)
    c.rect(40, y - 62, 6, 62, fill=1, stroke=0)

    draw_para(
        c,
        "• <b>Medical Emergency:</b> First aid kit, BP monitor, bandages, glucose & ice stationed in logistics support bus. Nearest facility on alert.\n"
        "• <b>Traffic Safety:</b> Fluorescent safety vests mandatory for lead & tail runners. Regulate road crossings at major junctions.\n"
        "• <b>Pacing Protocol:</b> Runners must stick with assigned buddy / pacer group. No member is left behind.\n"
        "• <b>Equipment:</b> Megaphone / sound system, generator, district flags, water coolers, disposable cups, trash bags for eco-clean.",
        54, y - 14, 510, size=7.5, lead=12
    )

    # Footer
    c.setFont(FONT, 7.5)
    c.setFillColor(MUTE)
    c.drawString(40, 24, "BEKSCITY RUN CLUB — Official Operations Document — Generated from BCRC Central Handling System")

    c.showPage()
    c.save()
    return output_path

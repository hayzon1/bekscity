"""
BEKSCITY RUN CLUB — Professional PDF Calendar Builder
Generates a printable, fillable, branded monthly calendar PDF using ReportLab.
Includes configurable date text colors, automatic text wrapping,
clickable calendar links, interactive form fields, and club district administration.
"""

import os
import re
from datetime import datetime, date
import calendar
from urllib.parse import quote

# ==============================================================================
# CONFIGURATION SETTING — DATE TEXT COLOR
# ==============================================================================
# Changing this value changes the date text color across the entire regenerated PDF.
# Accepts hex color values, for example: "#D9A441", "#252525", or "#287D58".
DATE_TEXT_COLOR = "#D9A441"

# Optional category-specific date color accents (falls back to DATE_TEXT_COLOR)
CATEGORY_DATE_COLORS = {
    "Community Improvement": "#287D58",      # Forest Green
    "Sponsor Run": "#2B6CB0",                 # Royal Blue
    "Monthly Signature Event": "#D9A441",     # Warm Honey Gold
    "Community Challenge": "#C05621",         # Energetic Amber/Rust
}

BRAND_COLORS = {
    "primary_gold": "#D9A441",
    "forest_green": "#287D58",
    "charcoal": "#252525",
    "deep_slate": "#1E293B",
    "card_bg": "#F8FAFC",
    "card_border": "#CBD5E1",
    "tag_bg": "#FEF3C7",
    "tag_text": "#92400E",
    "text_dark": "#0F172A",
    "text_muted": "#475569",
    "white": "#FFFFFF",
    "cream": "#FDFBF7",
}


def validate_hex_color(hex_str, field_name="DATE_TEXT_COLOR"):
    """
    Validates a hexadecimal color string.
    Reports clear, descriptive errors for invalid values.
    """
    if not hex_str or not isinstance(hex_str, str):
        raise ValueError(f"[{field_name}] Color value must be a non-empty string (e.g. '#D9A441').")

    cleaned = hex_str.strip()
    if not re.match(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$", cleaned):
        raise ValueError(
            f"[{field_name}] Invalid hexadecimal color value: '{hex_str}'. "
            "Must be formatted as #RGB or #RRGGBB (e.g. '#D9A441', '#252525', '#287D58')."
        )

    if len(cleaned) == 4:
        cleaned = "#" + "".join([c * 2 for c in cleaned[1:]])

    return cleaned.upper()


def get_effective_date_color(category=None, override_color=None, use_category_accents=False):
    """
    Returns validated HexColor for date text.
    If override_color is provided, it takes priority.
    """
    base_color = override_color or DATE_TEXT_COLOR
    validated_hex = validate_hex_color(base_color, "DATE_TEXT_COLOR")

    if use_category_accents and category in CATEGORY_DATE_COLORS:
        try:
            cat_hex = validate_hex_color(CATEGORY_DATE_COLORS[category], "CATEGORY_DATE_COLORS")
            return cat_hex
        except Exception:
            pass

    return validated_hex


def format_display_time(time_str):
    """
    Converts '16:00' to '04:00 PM', or returns existing formatted string.
    """
    if not time_str:
        return "TBC"
    time_str = time_str.strip()
    if "AM" in time_str.upper() or "PM" in time_str.upper():
        return time_str
    try:
        parts = time_str.split(":")
        hh = int(parts[0])
        mm = int(parts[1]) if len(parts) > 1 else 0
        dt = datetime(2026, 1, 1, hh, mm)
        return dt.strftime("%I:%M %p")
    except Exception:
        return time_str


def get_month_saturdays(year, month):
    """
    Returns list of date objects for all Saturdays in given year and month.
    """
    cal = calendar.monthcalendar(year, month)
    saturdays = []
    for week in cal:
        day = week[calendar.SATURDAY]
        if day != 0:
            saturdays.append(date(year, month, day))
    return saturdays


def build_calendar_pdf(
    output_path,
    events,
    year=2026,
    month=10,
    date_text_color_override=None,
    use_category_accents=False,
    include_interactive_fields=True
):
    """
    Constructs the professional BEKSCITY RUN CLUB Calendar PDF.
    """
    # Lazy import reportlab so module can be imported anywhere
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, PageBreak, HRFlowable
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.pdfgen import canvas

    effective_date_hex = get_effective_date_color(override_color=date_text_color_override)
    date_color_obj = colors.HexColor(effective_date_hex)

    # Document setup: A4 portrait, 0.45 in margins for maximum readable printable area
    margin = 32
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=margin,
        rightMargin=margin,
        topMargin= margin,
        bottomMargin=margin,
        title=f"BEKSCITY RUN CLUB — {calendar.month_name[month]} {year} Calendar",
        author="BEKSCITY RUN CLUB",
        subject="Monthly Saturday Run Calendar & Operations"
    )

    usable_width = A4[0] - (2 * margin)

    styles = getSampleStyleSheet()

    # Custom typography styles
    style_club_header = ParagraphStyle(
        "ClubHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor(BRAND_COLORS["text_dark"]),
        spaceAfter=2
    )

    style_sub_header = ParagraphStyle(
        "ClubSubHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor(BRAND_COLORS["forest_green"]),
        spaceAfter=4
    )

    style_month_badge = ParagraphStyle(
        "MonthBadge",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        alignment=2, # Right
        textColor=colors.HexColor(BRAND_COLORS["primary_gold"])
    )

    style_date_label = ParagraphStyle(
        "EventDateLabel",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=26,
        leading=28,
        alignment=1, # Center
        textColor=date_color_obj
    )

    style_date_dayname = ParagraphStyle(
        "EventDateDayName",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=11,
        alignment=1, # Center
        textColor=date_color_obj
    )

    style_event_title = ParagraphStyle(
        "EventTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=colors.HexColor(BRAND_COLORS["text_dark"])
    )

    style_category_pill = ParagraphStyle(
        "CategoryPill",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor(BRAND_COLORS["tag_text"])
    )

    style_status_pill = ParagraphStyle(
        "StatusPill",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=9.5,
        alignment=2, # Right
        textColor=colors.HexColor(BRAND_COLORS["forest_green"])
    )

    style_body = ParagraphStyle(
        "EventBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor(BRAND_COLORS["text_muted"])
    )

    style_body_bold = ParagraphStyle(
        "EventBodyBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor(BRAND_COLORS["text_dark"])
    )

    style_activities = ParagraphStyle(
        "EventActivities",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=10.5,
        textColor=colors.HexColor(BRAND_COLORS["text_dark"])
    )

    style_link = ParagraphStyle(
        "EventLink",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor(BRAND_COLORS["forest_green"])
    )

    style_footer_heading = ParagraphStyle(
        "FooterHeading",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=13,
        textColor=colors.HexColor(BRAND_COLORS["text_dark"]),
        spaceAfter=4
    )

    style_footer_text = ParagraphStyle(
        "FooterText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7,
        leading=9.5,
        textColor=colors.HexColor(BRAND_COLORS["text_muted"])
    )

    story = []

    # -------------------------------------------------------------------------
    # 1. HEADER SECTION
    # -------------------------------------------------------------------------
    month_name = calendar.month_name[month]
    confirmed_count = sum(1 for e in events if e.get("status", "").upper() == "CONFIRMED")
    
    header_data = [
        [
            Paragraph(
                "<b>BEKSCITY RUN CLUB</b><br/>"
                f"<font color='{BRAND_COLORS['forest_green']}'><b>RUN. IMPROVE. CONNECT. — OFFICIAL SATURDAY CALENDAR</b></font>",
                style_club_header
            ),
            Paragraph(
                f"<b>{month_name.upper()} {year}</b><br/>"
                f"<font size=8 color='{BRAND_COLORS['text_muted']}'>{confirmed_count} Confirmed Runs | Africa/Lagos WAT</font>",
                style_month_badge
            )
        ]
    ]

    header_table = Table(header_data, colWidths=[usable_width * 0.65, usable_width * 0.35])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(header_table)

    story.append(HRFlowable(
        width="100%", thickness=2, color=colors.HexColor(BRAND_COLORS["primary_gold"]),
        spaceBefore=4, spaceAfter=8
    ))

    # -------------------------------------------------------------------------
    # 2. SATURDAY RUNS LISTING (AND 5TH SATURDAY PLANNING SLOT)
    # -------------------------------------------------------------------------
    month_saturdays = get_month_saturdays(year, month)
    events_by_date = {e.get("date"): e for e in events}

    date_col_w = 68
    content_col_w = usable_width - date_col_w - 8

    for sat_idx, sat_date in enumerate(month_saturdays, 1):
        sat_str = sat_date.strftime("%Y-%m-%d")
        event = events_by_date.get(sat_str)
        is_fifth_sat = (sat_idx == 5)

        # Determine date color
        card_date_hex = effective_date_hex
        if use_category_accents and event:
            card_date_hex = get_effective_date_color(
                event.get("category"), override_color=date_text_color_override, use_category_accents=True
            )
        
        card_date_color_obj = colors.HexColor(card_date_hex)

        # Style for this specific date cell
        cell_date_num_style = ParagraphStyle(
            f"DateNum_{sat_str}",
            parent=style_date_label,
            textColor=card_date_color_obj
        )
        cell_date_day_style = ParagraphStyle(
            f"DateDay_{sat_str}",
            parent=style_date_dayname,
            textColor=card_date_color_obj
        )

        if event:
            # Populated Event Card
            ev_name = event.get("name", "Saturday Run")
            ev_status = event.get("status", "PLANNING").upper()
            ev_category = event.get("category", "Monthly Signature Event")
            start_fmt = format_display_time(event.get("start_time", "06:45"))
            end_fmt = format_display_time(event.get("end_time", "08:30"))
            district = event.get("district") or "ALL DISTRICTS"
            meeting_point = event.get("meeting_point") or "TBC"
            venue = event.get("venue") or meeting_point
            distance = event.get("distance") or "Standard Loop"
            route_stops = event.get("route_stops") or "Designated Waypoints"
            sponsor = event.get("sponsor")
            partners = event.get("partners")
            event_lead = event.get("event_lead")
            activities = event.get("planned_activities") or "Weekly endurance, form coaching, and community run."
            desc = event.get("description") or ""

            # Calendar Links
            from ics_exporter import generate_google_calendar_url
            gcal_url = generate_google_calendar_url(event)

            # Status pill color
            status_color = BRAND_COLORS["forest_green"] if ev_status == "CONFIRMED" else (
                "#E53E3E" if ev_status == "CANCELLED" else "#DD6B20"
            )

            # Left Date Box
            date_cell = [
                Spacer(1, 2),
                Paragraph(f"<b>SATURDAY</b>", cell_date_day_style),
                Paragraph(f"<b>{sat_date.day:02d}</b>", cell_date_num_style),
                Paragraph(f"<b>{month_name[:3].upper()} {year}</b>", cell_date_day_style),
                Spacer(1, 4),
                Paragraph(f"<font size=6 color='{status_color}'><b>● {ev_status}</b></font>", style_date_dayname)
            ]

            # Right Event Content Box
            right_content = []

            # Row 1: Title + Category Pill + Status
            right_content.append(Paragraph(
                f"<b>{ev_name.upper()}</b> "
                f"<font size=7 color='{BRAND_COLORS['tag_text']}'>[{ev_category.upper()}]</font> "
                f"— <font size=7 color='{BRAND_COLORS['forest_green']}'><b>{district}</b></font>",
                style_event_title
            ))

            # Row 2: Timing, Gathering point, Distance
            loc_text = meeting_point
            if venue and venue != meeting_point:
                loc_text += f" (Venue: {venue})"

            meta_line = f"<b>Time:</b> {start_fmt} – {end_fmt} | <b>Meet:</b> {loc_text} | <b>Dist:</b> {distance}"
            if route_stops and route_stops != "None":
                meta_line += f" | <b>Stops:</b> {route_stops}"

            right_content.append(Spacer(1, 2))
            right_content.append(Paragraph(meta_line, style_body))

            # Row 3: Sponsors, Partners, Event Lead
            sponsor_parts = []
            if sponsor:
                sponsor_parts.append(f"<b>Sponsor:</b> {sponsor}")
            if partners:
                sponsor_parts.append(f"<b>Partners:</b> {partners}")
            if event_lead:
                sponsor_parts.append(f"<b>Lead:</b> {event_lead}")

            if sponsor_parts:
                right_content.append(Paragraph(" | ".join(sponsor_parts), style_body_bold))

            # Row 4: Planned Activities
            right_content.append(Spacer(1, 2))
            right_content.append(Paragraph(
                f"<b>Activities:</b> {activities}",
                style_activities
            ))

            # Row 5: Description (if different)
            if desc and desc != activities:
                # Wrap description
                clean_desc = desc.replace("\n", " ")
                if len(clean_desc) > 220:
                    clean_desc = clean_desc[:217] + "..."
                right_content.append(Paragraph(f"<b>Details:</b> {clean_desc}", style_body))

            # Row 6: Clickable Calendar Action Links & Notes
            right_content.append(Spacer(1, 2))
            links_html = (
                f"<font color='{BRAND_COLORS['forest_green']}'><b>+ Add to Calendar:</b></font> "
                f"<a href='{gcal_url}'><font color='#2563EB'><u>Google Calendar Link</u></font></a> "
                f" | <font color='{BRAND_COLORS['text_muted']}'>Apple / Outlook: Use Club .ics master export</font>"
            )
            right_content.append(Paragraph(links_html, style_link))

        else:
            # Slot with no confirmed event yet
            slot_title = "FIFTH SATURDAY — COMMUNITY / SPECIAL COLLABORATION" if is_fifth_sat else f"SATURDAY RUN — {sat_str}"
            slot_status = "PLANNING OPPORTUNITY" if is_fifth_sat else "TBC"
            
            date_cell = [
                Spacer(1, 4),
                Paragraph(f"<b>SATURDAY</b>", cell_date_day_style),
                Paragraph(f"<b>{sat_date.day:02d}</b>", cell_date_num_style),
                Paragraph(f"<b>{month_name[:3].upper()} {year}</b>", cell_date_day_style),
                Spacer(1, 4),
                Paragraph(f"<font size=6 color='#DD6B20'><b>● {slot_status}</b></font>", style_date_dayname)
            ]

            right_content = [
                Paragraph(f"<b>{slot_title}</b>", style_event_title),
                Spacer(1, 2),
                Paragraph(
                    "<b>Status:</b> Unconfirmed / Open Planning Slot. "
                    "Fifth Saturdays offer an additional club planning slot for special pop-up runs, cross-district meets, or community partnerships.",
                    style_body
                ),
                Spacer(1, 2),
                Paragraph(
                    "<b>Standard Morning Window:</b> 06:45 AM – 08:30 AM | Africa/Lagos Time | To schedule or confirm, open the Event Manager Dashboard.",
                    style_activities
                )
            ]

        card_table_data = [[date_cell, right_content]]
        card_table = Table(
            card_table_data,
            colWidths=[date_col_w, content_col_w]
        )

        card_bg = BRAND_COLORS["card_bg"] if (event and event.get("status") == "CONFIRMED") else "#F1F5F9"
        card_border = BRAND_COLORS["primary_gold"] if (event and event.get("date") == "2026-10-24") else BRAND_COLORS["card_border"]

        card_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(card_bg)),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor(card_border)),
            ('LINEBEFORE', (1, 0), (1, 0), 1, colors.HexColor(BRAND_COLORS["card_border"])),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (0, 0), 4),
            ('RIGHTPADDING', (0, 0), (0, 0), 4),
            ('LEFTPADDING', (1, 0), (1, 0), 8),
            ('RIGHTPADDING', (1, 0), (1, 0), 6),
        ]))

        story.append(card_table)
        story.append(Spacer(1, 6))

    # -------------------------------------------------------------------------
    # 3. DISTRICT ADMINISTRATION & OPERATIONS REFERENCE SECTION
    # -------------------------------------------------------------------------
    story.append(Spacer(1, 4))
    story.append(HRFlowable(
        width="100%", thickness=1, color=colors.HexColor(BRAND_COLORS["card_border"]),
        spaceBefore=2, spaceAfter=6
    ))

    district_info_html = (
        "<b>FOUR PERMANENT DISTRICTS:</b><br/>"
        "• <b>MILE DISTRICT:</b> Central gathering point | District Lead & Pacing Teams | BCRC & Mile Flags.<br/>"
        "• <b>PHARMAFIT DISTRICT:</b> Hill repeats & endurance trail | Dedicated hill safety marshals.<br/>"
        "• <b>PANSHEKE DISTRICT:</b> Boulevard course & speed development | Pacing groups 1–4.<br/>"
        "• <b>FUNAAB DISTRICT:</b> Campus perimeter & trail circuit | Youth and student development."
    )

    ops_checklist_html = (
        "<b>STANDARD RUN PROTOCOLS & LOGISTICS CHECKLIST:</b><br/>"
        "• <b>Morning Schedule:</b> 06:45 Check-in → 07:00 Warm-up → 07:15 Run → 08:15 Cooldown → 08:30 Social.<br/>"
        "• <b>Equipment:</b> Megaphone / Sound System, Generator & Fuel, Walkie-Talkies, District Flags, Safe Box.<br/>"
        "• <b>Medical & Safety:</b> First Aid Kit, BP Monitor, Bandages, Diclofenac Gel, Glucose, Traffic Safety Team.<br/>"
        "• <b>Hospitality:</b> Bottled / Dispenser Water, Energy Snacks, Recovery Fruits."
    )

    admin_table_data = [
        [
            Paragraph("<b>BEKSCITY DISTRICT ADMINISTRATION</b>", style_footer_heading),
            Paragraph("<b>RUN OPERATIONS & SAFETY CHECKLIST</b>", style_footer_heading)
        ],
        [
            Paragraph(district_info_html, style_footer_text),
            Paragraph(ops_checklist_html, style_footer_text)
        ]
    ]

    admin_table = Table(admin_table_data, colWidths=[usable_width * 0.5, usable_width * 0.5])
    admin_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(BRAND_COLORS["cream"])),
        ('BOX', (0, 0), (-1, -1), 0.75, colors.HexColor(BRAND_COLORS["primary_gold"])),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('LINEBEFORE', (1, 0), (1, 1), 0.5, colors.HexColor(BRAND_COLORS["card_border"])),
    ]))

    story.append(admin_table)

    # Disclaimer on PDF edits vs database
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "<i>Notice: This official calendar is generated dynamically from the BEKSCITY RUN CLUB Event Manager Database. "
        "Any independent edits made inside this PDF file remain local and do not modify the club master records. "
        "To update event schedules, visit the Event Manager Dashboard.</i>",
        style_footer_text
    ))

    # Build the PDF document
    doc.build(story)
    return output_path


if __name__ == "__main__":
    # Test generation with sample seed data
    import sys
    from database import init_db, get_all_events

    init_db()
    events = get_all_events()
    test_pdf = os.path.join(os.path.dirname(__file__), "test_calendar_oct2026.pdf")
    print(f"Building calendar PDF with DATE_TEXT_COLOR = '{DATE_TEXT_COLOR}'...")
    build_calendar_pdf(test_pdf, events, year=2026, month=10)
    print(f"Calendar PDF successfully created at: {test_pdf}")

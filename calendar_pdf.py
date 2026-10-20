"""
BEKSCITY RUN CLUB calendar builder
Generates the exact interactive, fillable, wrapped-text PDF calendar,
master .ics calendar, and individual event .ics files.
Fully integrated with the persistent database.
"""

import calendar
import os
import re
import datetime as dt
from urllib.parse import quote

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, white
from reportlab.lib.utils import simpleSplit
from reportlab.pdfbase.pdfmetrics import stringWidth

HERE = os.path.dirname(os.path.abspath(__file__))

CLUB = "BEKSCITY RUN CLUB"
DISTRICTS = ["MILE DISTRICT", "PHARMAFIT DISTRICT", "PANSEKE DISTRICT", "FUNAAB DISTRICT"]

COFOUNDERS_DATA = [
    {"name": "Oladipupo Abdulazeez", "role": "Co-founder", "phone": "08101674646", "social": "jughead_x3"},
    {"name": "Shittu Oluwadamilare", "role": "Co-founder", "phone": "08168120117", "social": "sweetboycoal"},
    {"name": "Adebanjo Oluwatobiloba", "role": "Co-founder", "phone": "07069582118", "social": "tobenzin"}
]

DISTRICTS_DATA = [
    {"name": "MILE DISTRICT", "spot": "Moore junction", "lead": "", "contact": ""},
    {"name": "PHARMAFIT DISTRICT", "spot": "Kemta junction", "lead": "", "contact": ""},
    {"name": "PANSEKE DISTRICT", "spot": "Skating ground, Panseke", "lead": "", "contact": ""},
    {"name": "FUNAAB DISTRICT", "spot": "Funaab gate", "lead": "", "contact": ""}
]

MONTHS = [(2026, 10), (2026, 11), (2026, 12)]
START_DATE = dt.date(2026, 10, 24)   # calendar starts here; earlier Saturdays are left out
TZ = "Africa/Lagos"
DEFAULT_START, DEFAULT_END = "6:45 AM", "8:30 AM"
REMINDER_MINUTES = 30
OUT_PDF = os.path.join(HERE, "bekscity_run_club_calendar_Oct-Dec_2026.pdf")
OUT_ICS = os.path.join(HERE, "bekscity_saturdays_Oct-Dec.ics")
OUT_ICS_DIR = os.path.join(HERE, "individual_events")
SCHEDULE = "6:45 check-in, 7:00 warm-up, 7:15 run, 8:15 cooldown, 8:30 coffee and social"

# ---- DATE COLOURS --------------------------------------------------------
# >>> THIS IS THE LINE TO EDIT TO CHANGE THE COLOUR OF EVERY EVENT DATE IN THE PDF <<<
# Use a hex colour: "#D9A441" gold, "#252525" black, "#287D58" green (any #RRGGBB works).
DATE_TEXT_COLOR = "#D9A441"
# OPTIONAL: different date colour for a category. Categories left out use DATE_TEXT_COLOR. Example:
#   DATE_COLOR_BY_CATEGORY = {"Signature Event": "#252525", "Community Challenge": "#287D58"}
DATE_COLOR_BY_CATEGORY = {}
# Keeps dates readable: if the date colour has poor contrast against the card's coloured date block,
# a small dark or light backing panel is drawn behind the date text only. The card colour never changes.
DATE_AUTO_BACKING = True
DATE_MIN_CONTRAST = 3.0

# ---- INDIVIDUAL & MASTER .ics DOWNLOAD LINKS IN THE PDF -------------------
# Leave "" unless the individual_events folder is really uploaded somewhere public.
HOSTED_ICS_BASE_URL = ""
DEFAULT_MASTER_ICS_URL = "http://127.0.0.1:5050/api/calendar.ics"

CATS = ["Community Improvement", "Sponsor Run", "Signature Event", "Monthly Signature Event", "Community Challenge", "TBC"]
STATUSES = ["Confirmed", "TBC", "Planning slot", "Cancelled"]
STATUS_LABEL = {"Confirmed": "CONFIRMED", "TBC": "TBC", "Planning slot": "PLANNING", "Cancelled": "CANCELLED"}

def parse_hex_colour(value, setting="DATE_TEXT_COLOR"):
    if not value:
        raise ValueError(f"\nERROR: {setting} is empty, which is not a valid colour.")
    s = str(value).strip()
    if not s.startswith("#"):
        raise ValueError(f"\nERROR: {setting} is {value!r}, which is not a valid colour.\n"
                         f"Use a hex colour such as '#D9A441', '#252525' or '#287D58' "
                         f"(a # followed by 6 hex digits, 0-9 and A-F).")
    s_clean = s.lstrip("#")
    if re.fullmatch(r"[0-9a-fA-F]{3}", s_clean):
        s_clean = "".join(ch * 2 for ch in s_clean)
    if not re.fullmatch(r"[0-9a-fA-F]{6}", s_clean):
        raise ValueError(f"\nERROR: {setting} is {value!r}, which is not a valid colour.\n"
                         f"Use a hex colour such as '#D9A441', '#252525' or '#287D58' "
                         f"(a # followed by 6 hex digits, 0-9 and A-F).")
    return HexColor("#" + s_clean)

def validate_hex_color(hex_str, field_name="DATE_TEXT_COLOR"):
    col = parse_hex_colour(hex_str, field_name)
    s = str(hex_str).strip().lstrip("#")
    if len(s) == 3:
        s = "".join(ch * 2 for ch in s)
    return "#" + s.upper()

# ------------------------------------------------------------------ DESIGN
W, H = letter
INK = HexColor("#1b1b1f")
ACC = HexColor("#e8501f")
SOFT = HexColor("#f4f1ec")
MUTE = HexColor("#6b6b73")
GOLD = HexColor("#fff1c9")
GOLDB = HexColor("#e0a800")
LINE = HexColor("#c9c4bb")
SLOT = HexColor("#8a8a92")

CATCOL = {
    "Community Improvement": HexColor("#2f9e6e"),
    "Sponsor Run": HexColor("#2b6fd6"),
    "Signature Event": ACC,
    "Monthly Signature Event": ACC,
    "Community Challenge": HexColor("#7a4fd1"),
    "TBC": HexColor("#c28a00")
}

FONT = "Helvetica"
FONTB = "Helvetica-Bold"
FIELD_PAD_X = 10      # horizontal room reserved inside a field (border + padding both sides)
MARGIN_BOTTOM = 40

def _lum(col):
    def f(v): return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(col.red) + 0.7152 * f(col.green) + 0.0722 * f(col.blue)

def contrast(a, b):
    la, lb = sorted([_lum(a), _lum(b)], reverse=True)
    return (la + 0.05) / (lb + 0.05)

def is_confirmed(e):
    return str(e.get("status", "")).strip().lower() == "confirmed"

def block_colour(e):
    return CATCOL.get(e.get("category"), SLOT) if is_confirmed(e) else SLOT

def date_style(e, custom_date_color=None, custom_cat_colors=None):
    """Returns (text colour, backing panel colour or None)."""
    base_color = custom_date_color or parse_hex_colour(DATE_TEXT_COLOR, "DATE_TEXT_COLOR")
    cat_colors = custom_cat_colors if custom_cat_colors is not None else DATE_COLOR_BY_CATEGORY
    
    text = base_color
    if e.get("category") in cat_colors:
        text = parse_hex_colour(cat_colors[e["category"]], f"cat_colors[{e['category']}]")

    bg = block_colour(e)
    if contrast(text, bg) >= DATE_MIN_CONTRAST or not DATE_AUTO_BACKING:
        return text, None
    panel = max([INK, white], key=lambda p: contrast(text, p))
    return text, panel

# ---- text wrapping helpers (used for layout AND for the form-field appearances) ----
def wrap(text, font, size, width):
    out = []
    for part in str(text or "").split("\n"):
        out += simpleSplit(part, font, size, width) or [""]
    return out or [""]

def field_height(text, size, width):
    n = len(wrap(text, FONT, size, width - FIELD_PAD_X))
    return max(18, n * size * 1.2 + 7)

# ------------------------------------------------------------------ FORMATTING & URL HELPERS
def t12(s):
    s = str(s).strip()
    if not s:
        return dt.time(6, 45)
    for fmt in ("%I:%M %p", "%I:%M%p", "%H:%M", "%H:%M:%S"):
        try:
            return dt.datetime.strptime(s, fmt).time()
        except ValueError:
            pass
    return dt.time(6, 45)

def format_time_display(s):
    t = t12(s)
    return t.strftime("%I:%M %p").lstrip("0")

def title_of(e):
    return f"{CLUB}: {e['name']}"

def desc_of(e):
    lines = [
        f"Category: {e['category']}",
        f"District: {e.get('district') or 'TBC'}",
        f"Meeting point / venue: {e.get('venue') or e.get('meeting_point') or 'TBC'}"
    ]
    sponsor = e.get("sponsor") or e.get("partners")
    if sponsor:
        lines.append(f"Sponsor / partner: {sponsor}")
    activities = e.get("planned_activities") or e.get("activities")
    if activities and activities != "TBC":
        lines.append(f"Activities: {activities}")
    if e.get("notes"):
        lines.append(f"Notes: {e['notes']}")
    sched = e.get("schedule") or SCHEDULE
    lines.append(f"Schedule: {sched}")
    return "\n".join(lines)

def gcal_url(e):
    d_val = e["date"]
    if isinstance(d_val, str):
        d_val = dt.date.fromisoformat(d_val)
    d = d_val.strftime("%Y%m%d")
    s = t12(e.get("start") or e.get("start_time") or DEFAULT_START).strftime("%H%M%S")
    f = t12(e.get("end") or e.get("end_time") or DEFAULT_END).strftime("%H%M%S")
    venue_loc = e.get("venue") or e.get("meeting_point") or "TBC"
    if venue_loc in ("", "TBC"):
        venue_loc = "Abeokuta, Ogun State, Nigeria"
    else:
        venue_loc = f"{venue_loc}, Abeokuta, Nigeria"
    return (
        "https://calendar.google.com/calendar/render?action=TEMPLATE&text=" + quote(title_of(e)) +
        f"&dates={d}T{s}/{d}T{f}&ctz={TZ}&location=" + quote(venue_loc) +
        "&details=" + quote(desc_of(e))
    )

def slug(e):
    return re.sub(r"[^a-z0-9]+", "-", e["name"].lower()).strip("-")

def ics_filename(e):
    d_val = e["date"]
    if isinstance(d_val, str):
        d_val = dt.date.fromisoformat(d_val)
    return f"{d_val.isoformat()}_{slug(e)}.ics"

def ics_url(e, base_url=None):
    if e.get("ics_url"):
        return e["ics_url"]
    if base_url:
        if e.get("id"):
            return f"{base_url.rstrip('/')}/api/events/{e['id']}/calendar.ics"
        return f"{base_url.rstrip('/')}/individual_events/{quote(ics_filename(e))}"
    if HOSTED_ICS_BASE_URL:
        return HOSTED_ICS_BASE_URL.rstrip('/') + "/" + quote(ics_filename(e))
    return ""

def event_dict_from_db(db_event):
    """Normalizes database row dict to builder format."""
    d_val = db_event["date"]
    if isinstance(d_val, str):
        d_val = dt.date.fromisoformat(d_val)

    status_raw = db_event.get("status", "Confirmed").strip()
    canon_status = "Confirmed"
    for st in STATUSES:
        if st.lower() == status_raw.lower():
            canon_status = st
            break

    cat = db_event.get("category", "Signature Event")
    if cat == "Monthly Signature Event":
        cat = "Signature Event"

    sched = db_event.get("notes") if "schedule" in str(db_event.get("notes", "")).lower() else None
    if d_val == dt.date(2026, 10, 24):
        sched = "Evening event, 4:00 PM to 9:00 PM. The standard morning schedule does not apply."

    start_raw = db_event.get("start_time") or db_event.get("start") or DEFAULT_START
    end_raw = db_event.get("end_time") or db_event.get("end") or DEFAULT_END

    # Ensure formatted as 12-hour AM/PM
    start_fmt = format_time_display(start_raw)
    end_fmt = format_time_display(end_raw)

    sponsor = db_event.get("sponsor", "")
    partners = db_event.get("partners", "")
    combined_sponsor = sponsor
    if partners:
        combined_sponsor = f"{sponsor}; {partners}" if sponsor else partners

    return {
        "id": db_event.get("id"),
        "date": d_val,
        "name": db_event.get("name", ""),
        "category": cat,
        "district": db_event.get("district", ""),
        "venue": db_event.get("venue") or db_event.get("meeting_point") or "TBC",
        "meeting_point": db_event.get("meeting_point", ""),
        "sponsor": combined_sponsor,
        "lead": db_event.get("event_lead") or "TBC",
        "activities": db_event.get("planned_activities") or "TBC",
        "notes": db_event.get("notes", ""),
        "start": start_fmt,
        "end": end_fmt,
        "status": canon_status,
        "schedule": sched or SCHEDULE
    }

def blank_slot(date_obj, nth, total):
    note = "Fifth Saturday: optional extra slot, unconfirmed." if nth == 5 else ""
    return {
        "date": date_obj,
        "name": "",
        "category": "Select category",
        "district": "",
        "venue": "",
        "sponsor": "",
        "lead": "",
        "activities": "",
        "notes": note,
        "start": "",
        "end": "",
        "status": "Planning slot",
        "schedule": SCHEDULE
    }

# ------------------------------------------------------------------ PDF DRAWING FUNCTIONS
def card_rows(e, base_url=None):
    """Field layout of one card. kind: 'text' (wrapping multiline), 'time' (single line), 'combo' (dropdown)."""
    has_ics = is_confirmed(e) and bool(ics_url(e, base_url))
    notes_w = 250 if has_ics else 340
    F = lambda key, lab, x, w, size, text, kind="text": dict(
        key=key, label=lab, x=x, w=w, size=size, text=text, kind=kind
    )
    return [
        [
            F("name", "Event name", 114, 196, 10, e["name"]),
            F("cat", "Category", 318, 128, 8.5, e["category"] or "Select category", "combo"),
            F("district", "District", 454, 108, 8, e["district"])
        ],
        [
            F("venue", "Meeting point / venue", 114, 170, 9, e["venue"]),
            F("start", "Start", 292, 52, 8.5, e["start"], "time"),
            F("end", "End", 350, 52, 8.5, e["end"], "time"),
            F("sponsor", "Sponsor / partner", 410, 152, 9, e["sponsor"])
        ],
        [
            F("lead", "Event lead", 114, 110, 9, e["lead"]),
            F("status", "Status", 232, 92, 8.5, e["status"], "combo"),
            F("acts", "Planned activities", 332, 230, 9, e["activities"])
        ],
        [
            F("notes", "Notes", 114, notes_w, 8.5, e["notes"])
        ],
    ], has_ics

def card_metrics(e, base_url=None):
    rows, has_ics = card_rows(e, base_url)
    heights = []
    for row in rows:
        for f in row:
            f["h"] = 18 if f["kind"] != "text" else field_height(f["text"], f["size"], f["w"])
        heights.append(11 + max(f["h"] for f in row) + 7)
    return rows, has_ics, heights, max(148, 4 + sum(heights))

def draw_header(c, title, sub, master_ics_url=None):
    c.setFillColor(INK)
    c.rect(0, H - 90, W, 90, fill=1, stroke=0)
    c.setFillColor(ACC)
    c.rect(0, H - 94, W, 4, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont(FONTB, 22)
    c.drawString(40, H - 48, title)
    c.setFont(FONT, 9.5)
    c.setFillColor(HexColor("#cfcfd6"))
    c.drawString(40, H - 70, sub)

    # ADD ALL CONFIRMED RUNS TO CALENDAR BUTTON (WITH REMINDERS)
    if master_ics_url:
        bx = 328
        by = H - 74
        bw = 244
        bh = 38
        # Button background: rich dark emerald green with gold border
        c.setFillColor(HexColor("#1e5e42"))
        c.setStrokeColor(HexColor("#D9A441"))
        c.setLineWidth(1.2)
        c.roundRect(bx, by, bw, bh, 6, fill=1, stroke=1)

        # Vector calendar icon
        ix, iy, isize = bx + 10, by + 18, 12
        c.setStrokeColor(white)
        c.setLineWidth(1)
        c.roundRect(ix, iy, isize, isize, 2, fill=0, stroke=1)
        c.setFillColor(HexColor("#D9A441"))
        c.rect(ix, iy + isize - 3.5, isize, 3.5, fill=1, stroke=0)
        c.setFillColor(white)
        c.circle(ix + 3, iy + isize + 0.5, 0.8, fill=1, stroke=0)
        c.circle(ix + isize - 3, iy + isize + 0.5, 0.8, fill=1, stroke=0)

        # Button title
        c.setFillColor(white)
        c.setFont(FONTB, 7.8)
        c.drawString(bx + 28, by + 22, "ADD ALL CONFIRMED RUNS TO CALENDAR")

        # Subtitle: reminders & timezone
        c.setFillColor(HexColor("#FEF3C7"))
        c.setFont(FONT, 6.8)
        c.drawString(bx + 14, by + 9, "Tap to sync all runs • 3 Reminders (1d, 2h, 15m) • WAT")

        # Clickable PDF URI link
        c.linkURL(master_ics_url, (bx, by, bx + bw, by + bh), relative=0)

def draw_field(form, name, x, y, w, h=18, value="", size=9, fill=white, border=LINE, multi=True):
    form.textfield(
        name=name, value=value or "", x=x, y=y, width=w, height=h, fontSize=size,
        borderColor=border, fillColor=fill, textColor=INK, borderWidth=0.8,
        forceBorder=True, maxlen=1000, fieldFlags="multiline" if multi else ""
    )

def draw_choice(form, name, x, y, w, options, value, h=18, size=8.5, border=LINE):
    form.choice(
        name=name, value=value or "", options=options, x=x, y=y, width=w, height=h,
        fontSize=size, borderColor=border, fillColor=white, textColor=INK,
        borderWidth=0.8, forceBorder=True, fieldFlags="combo"
    )

def draw_label(c, t, x, y, size=7, col=MUTE):
    c.setFont(FONTB, size)
    c.setFillColor(col)
    c.drawString(x, y, t.upper())

def draw_para(c, text, x, y, w, size=9, lead=12, col=HexColor("#333338"), font=FONT):
    c.setFont(font, size)
    c.setFillColor(col)
    for ln in simpleSplit(text, font, size, w):
        c.drawString(x, y, ln)
        y -= lead
    return y

def para_lines(text, w, size=9, font=FONT):
    return len(simpleSplit(text, font, size, w))

def draw_card(c, form, top, n, total, e, custom_date_color=None, custom_cat_colors=None, base_url=None):
    d = e["date"]
    confirmed = is_confirmed(e)
    rows, has_ics, heights, ch = card_metrics(e, base_url)
    col = block_colour(e)
    dcol, panel = date_style(e, custom_date_color, custom_cat_colors)

    c.setFillColor(SOFT)
    c.roundRect(40, top - ch, 532, ch, 8, fill=1, stroke=0)
    c.setFillColor(col)
    c.roundRect(40, top - ch, 62, ch, 8, fill=1, stroke=0)
    c.rect(80, top - ch, 22, ch, fill=1, stroke=0)

    if panel is not None:  # readability backing behind the date text only
        c.setFillColor(panel)
        c.roundRect(46, top - 82, 50, 70, 5, fill=1, stroke=0)

    # ---- DATE TEXT: colour comes from date_style() ----
    c.setFillColor(dcol)
    c.setFont(FONTB, 9)
    c.drawCentredString(71, top - 24, d.strftime("%a").upper())
    c.setFont(FONTB, 28)
    c.drawCentredString(71, top - 58, str(d.day))
    c.setFont(FONTB, 8.5)
    c.drawCentredString(71, top - 73, d.strftime("%b").upper())

    # ---- supporting labels stay white ----
    c.setFillColor(white)
    c.setFont(FONT, 7.5)
    c.drawCentredString(71, top - 96, f"Sat {n} of {total}")
    c.setFont(FONTB, 8)
    c.drawCentredString(71, top - 118, STATUS_LABEL.get(e["status"], e["status"].upper()))

    if confirmed:
        c.setFont("Helvetica-Oblique", 6.5)
        c.drawCentredString(71, top - 132, "tap date to add")
        c.linkURL(gcal_url(e), (40, top - ch, 102, top), relative=0)

    k = d.strftime("%Y%m%d")
    ytop = top - 4
    last_field_top = None

    for ri, row in enumerate(rows):
        ftop = ytop - 11
        for f in row:
            draw_label(c, f["label"], f["x"], ytop - 9)
            fy = ftop - f["h"]
            nm = f"{k}_{f['key']}"
            if f["kind"] == "combo":
                opts = ["Select category"] + [c_opt for c_opt in CATS if c_opt != "Monthly Signature Event"] if f["key"] == "cat" else STATUSES
                draw_choice(form, nm, f["x"], fy, f["w"], opts, f["text"])
            else:
                draw_field(form, nm, f["x"], fy, f["w"], f["h"], f["text"], f["size"], border=LINE, multi=(f["kind"] == "text"))
        if ri == len(rows) - 1:
            last_field_top = ftop
        ytop -= heights[ri]

    by = last_field_top - 18  # button / hint aligned with the top of the Notes field
    if confirmed:
        single_ics_link = ics_url(e, base_url)
        if single_ics_link:
            c.setFillColor(INK)
            c.roundRect(370, by, 84, 18, 4, fill=1, stroke=0)
            c.setFillColor(white)
            c.setFont(FONTB, 6.8)
            c.drawCentredString(412, by + 6, "DOWNLOAD .ICS")
            c.linkURL(single_ics_link, (370, by, 454, by + 18), relative=0)

        c.setFillColor(ACC)
        c.roundRect(462, by, 100, 18, 4, fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont(FONTB, 6.8)
        c.drawCentredString(512, by + 6, "+ ADD TO CALENDAR")
        c.linkURL(gcal_url(e), (462, by, 562, by + 18), relative=0)
    else:
        c.setFillColor(MUTE)
        c.setFont("Helvetica-Oblique", 7)
        c.drawString(462, by + 6, "Cancelled: no link" if e["status"] == "Cancelled" else "Link added once confirmed")

    return ch


# ------------------------------------------------------------------ MAKE MULTILINE FIELDS DISPLAY WRAPPED TEXT
def rewrap_multiline_appearances(path):
    """
    ReportLab draws multiline fields as one clipped line. Rewrite their appearance
    so wrapped text shows in every viewer.
    """
    try:
        from pypdf import PdfReader, PdfWriter
        from pypdf.generic import DecodedStreamObject, NameObject
    except ImportError:
        return 0

    try:
        reader = PdfReader(path)
        writer = PdfWriter(clone_from=reader)
        count = 0
        for page in writer.pages:
            for a in page.get("/Annots") or []:
                a = a.get_object()
                if a.get("/FT") != "/Tx" or not (int(a.get("/Ff", 0)) & 4096):
                    continue
                r = [float(v) for v in a["/Rect"]]
                w, h = r[2] - r[0], r[3] - r[1]
                
                da_str = str(a.get("/DA", ""))
                size_match = re.search(r"([\d.]+) Tf", da_str)
                size = float(size_match.group(1)) if size_match else 8.5
                
                ap_obj = a.get("/AP")
                if not ap_obj:
                    continue
                n_obj = ap_obj.get_object().get("/N")
                if not n_obj:
                    continue
                ap = n_obj.get_object()
                data = ap.get_data().decode("latin-1")
                
                i, j = data.find("\nBT\n"), data.rfind("\nET\n")
                if i == -1 or j == -1:
                    continue

                col_match = re.search(r"\n([\d. -]+ rg)\n1 0 0 1", data[i:])
                colour = col_match.group(1) if col_match else "0 g"
                lines = wrap(str(a.get("/V", "")), FONT, size, w - FIELD_PAD_X)
                esc = lambda s: s.encode("latin-1", "replace").decode("latin-1").replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
                body = f"\nBT\n/Helv {size} Tf\n{colour}\n{size*1.2:.2f} TL\n1 0 0 1 4 {h-3-size*0.85:.2f} Tm\n"
                body += "".join(f"({esc(l)}) Tj\nT*\n" for l in lines)
                new = DecodedStreamObject()
                new.set_data((data[:i] + body + "ET\n" + data[j + 4:]).encode("latin-1"))
                for key, val in ap.items():
                    if key not in ("/Filter", "/Length", "/DecodeParms"):
                        new[NameObject(key)] = val
                a["/AP"].get_object()[NameObject("/N")] = writer._add_object(new)
                count += 1

        with open(path, "wb") as f:
            writer.write(f)
        return count
    except Exception as e:
        print(f"Notice: rewrap_multiline_appearances note: {e}")
        return 0


# ------------------------------------------------------------------ MAIN BUILD FUNCTION
def build_calendar_pdf(
    output_path=OUT_PDF,
    events=None,
    year=2026,
    month=None,
    date_text_color_override=None,
    use_category_accents=False,
    include_cover_pages=True,
    master_ics_url=None,
    base_url=None
):
    """
    Constructs the exact BEKSCITY RUN CLUB Calendar PDF matching the user's template:
    Page 1: Club Information, The 3 Cofounders & Our 4 Districts (with Master Calendar Sync button)
    Page 2: Monthly Event Structure & 4 Pillars (with Master Calendar Sync banner)
    Month Pages: October to December 2026 (each with header Master Calendar Sync button & individual links)
    """
    import database

    if not master_ics_url:
        master_ics_url = DEFAULT_MASTER_ICS_URL
    if not base_url:
        base_url = master_ics_url.rsplit("/api/", 1)[0] if "/api/" in master_ics_url else "http://127.0.0.1:5050"

    # If events not provided, fetch from database
    if events is None:
        db_events = database.get_all_events()
        event_list = [event_dict_from_db(e) for e in db_events]
    else:
        event_list = [event_dict_from_db(e) if isinstance(e, dict) and "id" in e and "start_time" in e else e for e in events]

    events_by_date = {e["date"]: e for e in event_list}

    # Determine months to generate
    if month is not None:
        target_months = [(year, month)]
        # When generating single month, allow start date from 1st of that month if not Oct 2026
        eff_start_date = START_DATE if (year == 2026 and month == 10) else dt.date(year, month, 1)
    else:
        target_months = MONTHS
        eff_start_date = START_DATE

    # Date colors
    custom_date_col = None
    if date_text_color_override:
        custom_date_col = parse_hex_colour(date_text_color_override, "date_text_color_override")

    c = canvas.Canvas(output_path, pagesize=letter)
    c.setTitle(CLUB + " Community Calendar")
    c.setAuthor(CLUB)
    form = c.acroForm

    # ------------------------------------------------------------------ PAGE 1: CLUB INFORMATION
    if include_cover_pages:
        draw_header(c, CLUB, "Community calendar  |  24 October to December 2026  |  Run every Saturday", master_ics_url=master_ics_url)
        y = H - 125
        c.setFillColor(INK)
        c.setFont(FONTB, 14)
        c.drawString(40, y, "THE 3 COFOUNDERS")
        c.setStrokeColor(ACC)
        c.setLineWidth(2)
        c.line(40, y - 6, 185, y - 6)
        y -= 12
        cardw = 170
        gap = 11
        CF_H = 220
        for i in range(3):
            cf = COFOUNDERS_DATA[i]
            x = 40 + i * (cardw + gap)
            top = y
            c.setFillColor(GOLD)
            c.setStrokeColor(GOLDB)
            c.setLineWidth(1.5)
            c.roundRect(x, top - CF_H, cardw, CF_H, 8, fill=1, stroke=1)
            c.setFillColor(GOLDB)
            c.rect(x, top - 26, cardw, 26, fill=1, stroke=0)
            c.setFillColor(INK)
            c.setFont(FONTB, 10)
            c.drawString(x + 10, top - 18, f"COFOUNDER {i+1}")
            fields_info = [
                ("Full name", "name", cf["name"]),
                ("Role / focus", "role", cf["role"]),
                ("Phone / WhatsApp", "phone", cf["phone"]),
                ("Instagram / email", "social", cf["social"])
            ]
            for k, (lab, nm, val) in enumerate(fields_info):
                draw_label(c, lab, x + 10, top - 44 - k * 46)
                draw_field(form, f"cof{i+1}_{nm}", x + 10, top - 46 - k * 46 - 28, cardw - 20, 28, value=val, fill=white, border=GOLDB)
        y -= CF_H + 25
        c.setFillColor(INK)
        c.setFont(FONTB, 14)
        c.drawString(40, y, "OUR 4 DISTRICTS")
        c.setStrokeColor(ACC)
        c.line(40, y - 6, 170, y - 6)
        y -= 14
        draw_label(c, "District", 44, y - 4)
        draw_label(c, "Meet-up point", 190, y - 4)
        draw_label(c, "District lead", 392, y - 4)
        draw_label(c, "Lead contact", 482, y - 4)
        y -= 34
        for i, dist in enumerate(DISTRICTS_DATA):
            draw_field(form, f"dist_{i}_name", 40, y, 140, 30, value=dist["name"])
            draw_field(form, f"dist_{i}_spot", 186, y, 196, 30, value=dist["spot"])
            draw_field(form, f"dist_{i}_lead", 388, y, 84, 30, value=dist["lead"])
            draw_field(form, f"dist_{i}_contact", 478, y, 94, 30, value=dist["contact"])
            y -= 36
        y -= 10
        RHYTHM = [
            "Every Saturday morning: 6:45 check-in, 7:00 warm-up, 7:15 run, 8:15 cooldown, 8:30 coffee and social. Evening or special events show their own times on their card.",
            "Four event types each month: Community Improvement, Sponsor Run, Signature Event, Community Challenge.",
            "A fifth Saturday is an optional extra slot, left open until organisers confirm it.",
            "Tap 'ADD ALL CONFIRMED RUNS TO CALENDAR' in the header to sync all confirmed runs into Apple Calendar, Google Calendar, or Outlook with 3 automated reminders (1 day, 2 hours, 15 minutes prior) in Africa/Lagos (WAT, UTC+1)."
        ]
        bh = 38 + sum(para_lines("-  " + t, 500, 9.5) * 13 + 3 for t in RHYTHM) + 32
        c.setFillColor(SOFT)
        c.roundRect(40, y - bh, 532, bh, 8, fill=1, stroke=0)
        c.setFillColor(INK)
        c.setFont(FONTB, 12)
        c.drawString(54, y - 20, "Our rhythm")
        yy = y - 38
        for t in RHYTHM:
            yy = draw_para(c, "-  " + t, 54, yy, 500, 9.5, 13) - 3

        # Dedicated action button inside Page 1 Rhythm card
        btn_y = y - bh + 8
        c.setFillColor(HexColor("#1e5e42"))
        c.setStrokeColor(HexColor("#D9A441"))
        c.setLineWidth(1)
        c.roundRect(54, btn_y, 504, 22, 4, fill=1, stroke=1)
        c.setFillColor(white)
        c.setFont(FONTB, 8.5)
        c.drawCentredString(54 + 252, btn_y + 6.5, "+ ADD ALL CONFIRMED RUNS TO MY CALENDAR (WITH 3 REMINDERS)")
        if master_ics_url:
            c.linkURL(master_ics_url, (54, btn_y, 558, btn_y + 22), relative=0)

        c.showPage()

        # ------------------------------------------------------------------ PAGE 2: MONTHLY EVENT STRUCTURE GUIDE
        draw_header(c, "MONTHLY EVENT STRUCTURE", f"Four pillars of {CLUB}", master_ics_url=master_ics_url)
        PILLARS = [
            ("Community Improvement", "Improve technique, confidence, consistency and personal performance.",
             "Beginner-friendly runs and PB work, drills and form coaching, individual goals, monthly progress check-ins (distance or time), short talks on nutrition, recovery and injury prevention."),
            ("Sponsor Run", "Connect the community with partner brands and local businesses.",
             "Group run to a sponsor's shop, business or venue. Photo and content for the sponsor. Post-run giveaways, offers or discount codes. Record sponsor, destination, meeting point, content lead and giveaway details."),
            ("Signature Event", "A memorable event members look forward to. Organisers choose the format for each confirmed date.",
             "Timed 5K Challenge, Charity or Cause Run, Themed Fun Run (costume, daybreak, night), or Social Day (breakfast, music, games). Record format, theme or cause, distance, venue and partners."),
            ("Community Challenge", "Build endurance, accountability and stronger relationships.",
             "Long run, hill run or interval session. Member spotlights and milestone shout-outs. Buddy-up or volunteer support. Record format, distance or intensity, lead runner and buddy assignments."),
        ]
        y = H - 118
        for name, purpose, acts in PILLARS:
            col = CATCOL[name]
            h = max(100, 36 + para_lines(purpose, 500, 9.5, FONTB) * 12 + 3 + para_lines(acts, 500, 9) * 12 + 10)
            c.setFillColor(SOFT)
            c.roundRect(40, y - h, 532, h, 8, fill=1, stroke=0)
            c.setFillColor(col)
            c.rect(40, y - h, 7, h, fill=1, stroke=0)
            c.setFont(FONTB, 12)
            c.drawString(58, y - 22, name.upper())
            yy = draw_para(c, purpose, 58, y - 38, 500, 9.5, 12, font=FONTB, col=INK)
            draw_para(c, acts, 58, yy - 4, 500, 9, 12)
            y -= h + 20

        # Action banner at bottom of Page 2
        p2_by = 48
        c.setFillColor(HexColor("#1e5e42"))
        c.setStrokeColor(HexColor("#D9A441"))
        c.setLineWidth(1.2)
        c.roundRect(40, p2_by, 532, 34, 6, fill=1, stroke=1)
        c.setFillColor(white)
        c.setFont(FONTB, 9)
        c.drawCentredString(306, p2_by + 19, "+ ADD ALL CONFIRMED SATURDAY RUNS TO YOUR CALENDAR")
        c.setFillColor(HexColor("#FEF3C7"))
        c.setFont(FONT, 7.5)
        c.drawCentredString(306, p2_by + 7, "Tap to sync all runs with 3 automated reminders (1 day, 2 hours, 15 minutes prior) in Africa/Lagos (WAT)")
        if master_ics_url:
            c.linkURL(master_ics_url, (40, p2_by, 572, p2_by + 34), relative=0)

        c.showPage()

    # ------------------------------------------------------------------ MONTH PAGES (cards grow to fit wrapped text)
    CARD_GAP = 8
    month_event_groups = []
    for (yr, mo) in target_months:
        sats = [dt.date(yr, mo, d) for d in range(1, calendar.monthrange(yr, mo)[1] + 1) if dt.date(yr, mo, d).weekday() == 5]
        evs = []
        for n, d in enumerate(sats, 1):
            if d < eff_start_date:
                continue
            evs.append((n, len(sats), events_by_date.get(d) or blank_slot(d, n, len(sats))))
        month_event_groups.append(((yr, mo), evs))

    for (yr, mo), evs in month_event_groups:
        title = dt.date(yr, mo, 1).strftime("%B %Y").upper()
        draw_header(c, title, f"{CLUB}  |  Saturday programme", master_ics_url=master_ics_url)
        top = H - 108
        for (n, total, e) in evs:
            ch = card_metrics(e, base_url)[3]
            if top - ch < MARGIN_BOTTOM:
                c.showPage()
                draw_header(c, title, f"{CLUB}  |  Saturday programme  |  continued", master_ics_url=master_ics_url)
                top = H - 108
            draw_card(c, form, top, n, total, e, custom_date_color=custom_date_col, base_url=base_url)
            top -= ch + CARD_GAP
        c.showPage()

    c.save()

    # ------------------------------------------------------------------ MAKE MULTILINE FIELDS DISPLAY WRAPPED TEXT
    rewrap_multiline_appearances(output_path)
    return output_path


def generate_all_outputs():
    """Builds the master PDF, master .ics, and individual .ics files."""
    import database
    database.init_db()
    db_events = database.get_all_events()
    event_list = [event_dict_from_db(e) for e in db_events]
    confirmed = sorted([e for e in event_list if is_confirmed(e)], key=lambda x: x["date"])

    # Build PDF
    build_calendar_pdf(OUT_PDF, event_list)

    # Build Master ICS
    from ics_exporter import generate_ics_calendar
    ics_text = generate_ics_calendar(
        [database.get_event_by_id(e["id"]) if e.get("id") else e for e in confirmed],
        calendar_name=CLUB
    )
    with open(OUT_ICS, "w", encoding="utf-8") as f:
        f.write(ics_text)

    # Build Individual ICS files
    os.makedirs(OUT_ICS_DIR, exist_ok=True)
    for old in os.listdir(OUT_ICS_DIR):
        if old.endswith(".ics"):
            os.remove(os.path.join(OUT_ICS_DIR, old))

    for e in confirmed:
        single_path = os.path.join(OUT_ICS_DIR, ics_filename(e))
        db_ev = database.get_event_by_id(e["id"]) if e.get("id") else e
        single_ics = generate_ics_calendar([db_ev], calendar_name=title_of(e))
        with open(single_path, "w", encoding="utf-8") as f:
            f.write(single_ics)

    print(f"Built {os.path.basename(OUT_PDF)}, {os.path.basename(OUT_ICS)} and {len(confirmed)} individual .ics files ({len(event_list)-len(confirmed)} non-confirmed events left out of exports)")


if __name__ == "__main__":
    generate_all_outputs()

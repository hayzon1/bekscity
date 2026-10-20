"""
BEKSCITY RUN CLUB — Executive Pitch Deck & Sponsorship Proposal PDF Generator
Generates a complete 11-page widescreen (16:9) executive presentation deck matching
the Pocari Sweat Proposal and Run & Rumble Pitch Deck templates.
"""

import os
import json
import re
import urllib.request
import urllib.parse
import datetime as dt
from reportlab.lib.colors import HexColor, white
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit
from PIL import Image

try:
    import fitz
    FITZ_AVAILABLE = True
except ImportError:
    fitz = None
    FITZ_AVAILABLE = False

HERE = os.path.dirname(os.path.abspath(__file__))

TEMPLATE_PDF_CANDIDATES = {
    "run_and_rumble": [
        os.path.join(HERE, "proposal_templates", "editable.pdf"),
        os.path.expanduser("~/Downloads/editable.pdf")
    ],
    "partnership_proposal": [
        os.path.join(HERE, "proposal_templates", "Pocari Sweat Proposal.pdf"),
        os.path.expanduser("~/Downloads/Pocari Sweat Proposal.pdf")
    ]
}


def find_pdf_template(template_name="partnership_proposal"):
    candidates = TEMPLATE_PDF_CANDIDATES.get(template_name, TEMPLATE_PDF_CANDIDATES["partnership_proposal"])
    for p in candidates:
        if os.path.exists(p) and os.path.getsize(p) > 100000:
            return p
    return None


def resolve_local_gallery_path(img_url):
    if not img_url:
        return None
    if img_url.startswith("/static/"):
        p = os.path.join(HERE, img_url.lstrip("/"))
        if os.path.exists(p):
            return p
    if os.path.exists(img_url):
        return img_url
    if img_url.startswith("http"):
        return safe_download_image(img_url)
    return None

# 16:9 Widescreen slide format (matches Pocari Sweat Proposal & editable.pdf: 960 x 540 pt)
W = 960
H = 540

# Visual Identity Palette
CLUB = "BEKSCITY RUN CLUB"
CHARCOAL = HexColor("#1b1b1f")
DARK_NAVY = HexColor("#111827")
GOLD = HexColor("#D9A441")
GOLD_LIGHT = HexColor("#fffbeb")
GOLD_BORDER = HexColor("#f59e0b")
EMERALD = HexColor("#1e5e42")
EMERALD_LIGHT = HexColor("#ecfdf5")
CARD_BG = HexColor("#f8fafc")
CARD_BORDER = HexColor("#e2e8f0")
TEXT_MAIN = HexColor("#0f172a")
TEXT_MUTED = HexColor("#475569")
TEXT_SUB = HexColor("#64748b")
LINE_COL = HexColor("#cbd5e1")

FONT = "Helvetica"
FONTB = "Helvetica-Bold"


def safe_download_image(url, cache_dir="static/uploads/cache"):
    """Safely downloads and caches a remote image (e.g. brand logo)."""
    if not url or not url.startswith("http"):
        return None
    try:
        # Normalize Wikimedia thumbnail width to 500px to avoid HTTP 400 on non-standard sizes (e.g. 300px)
        if "wikimedia.org" in url and "/thumb/" in url:
            url = re.sub(r"/\d+px-", "/500px-", url)

        os.makedirs(cache_dir, exist_ok=True)
        base_name = url.split("?")[0].split("/")[-1]
        filename = re.sub(r"[^a-zA-Z0-9_\.-]", "_", base_name)
        if not filename.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
            filename += ".png"
        local_path = os.path.join(cache_dir, filename)
        if os.path.exists(local_path) and os.path.getsize(local_path) > 100:
            return local_path

        req = urllib.request.Request(
            url,
            headers={"User-Agent": "BekscityRunClub/2.0 (contact@bekscity.run; runner-proposal-engine)"}
        )
        with urllib.request.urlopen(req, timeout=6) as response:
            with open(local_path, "wb") as f:
                f.write(response.read())

        # Verify Pillow can open it
        Image.open(local_path).verify()
        return local_path
    except Exception as e:
        print(f"[ProposalPDF] Image download warning for '{url}': {e}")
        return None


def resolve_local_image(path):
    """Resolves local web path (e.g. /static/img/gallery/image1.jpeg) to absolute file path."""
    if not path:
        return None
    clean_path = path.lstrip("/")
    abs_path = os.path.join(HERE, clean_path)
    if os.path.exists(abs_path) and os.path.isfile(abs_path):
        return abs_path
    return None


def draw_para(c, text, x, y, w, size=10, lead=14, col=TEXT_MAIN, font=FONT):
    c.setFont(font, size)
    c.setFillColor(col)
    for ln in simpleSplit(str(text or ""), font, size, w):
        c.drawString(x, y, ln)
        y -= lead
    return y


def draw_slide_header(c, category, title, page_num, brand_name):
    """Draws standardized clean top header and running footer across presentation slides."""
    # Top Category Tag
    c.setFont(FONTB, 9)
    c.setFillColor(GOLD)
    c.drawString(50, H - 42, category.upper())

    # Slide Title
    c.setFont(FONTB, 18)
    c.setFillColor(CHARCOAL)
    c.drawString(50, H - 66, title)

    # Accent divider rule
    c.setStrokeColor(GOLD)
    c.setLineWidth(2)
    c.line(50, H - 74, 50 + min(len(title) * 11, 400), H - 74)

    # Running Footer
    c.setFont(FONTB, 8)
    c.setFillColor(TEXT_SUB)
    c.drawString(50, 28, f"{CLUB}  ×  {brand_name.upper()}")
    c.drawRightString(W - 50, 28, f"{page_num:02d}")
    c.setStrokeColor(CARD_BORDER)
    c.setLineWidth(0.8)
    c.line(50, 42, W - 50, 42)


def _build_proposal_pdf_reportlab(output_path, proposal_data):
    """
    Fallback generator: builds the executive 11-page presentation deck PDF using ReportLab canvas.
    """
    c = canvas.Canvas(output_path, pagesize=(W, H))
    brand_name = (proposal_data.get("brand_name") or "Brand Partner").strip()
    proposed_role = (proposal_data.get("proposed_role") or "Official Category Partner").strip()
    tier = (proposal_data.get("partnership_tier") or "Strategic Partner").strip()
    event_name = (proposal_data.get("event_name") or "Run and Rumble").strip()

    c.setTitle(f"BCRC Proposal — {brand_name}")
    c.setAuthor(CLUB)

    # Resolve Brand Logo (uploaded or auto-researched)
    brand_logo_file = None
    if proposal_data.get("brand_logo_url"):
        raw_logo = proposal_data["brand_logo_url"]
        if raw_logo.startswith("http"):
            brand_logo_file = safe_download_image(raw_logo)
        else:
            brand_logo_file = resolve_local_image(raw_logo)

    # Resolve Run Club Photos (for Gallery slide)
    run_club_imgs = []
    raw_imgs = proposal_data.get("run_club_images") or []
    if isinstance(raw_imgs, str):
        try:
            raw_imgs = json.loads(raw_imgs)
        except Exception:
            raw_imgs = [raw_imgs]

    for p in raw_imgs:
        loc = resolve_local_image(p) if not p.startswith("http") else safe_download_image(p)
        if loc and loc not in run_club_imgs:
            run_club_imgs.append(loc)

    # Default gallery fallback images if none specified
    if len(run_club_imgs) < 4:
        defaults = [
            "static/img/gallery/image1.jpeg",
            "static/img/gallery/image5.jpeg",
            "static/img/gallery/image6.jpeg",
            "static/img/gallery/image10.jpeg"
        ]
        for d in defaults:
            abs_d = os.path.join(HERE, d)
            if os.path.exists(abs_d) and abs_d not in run_club_imgs:
                run_club_imgs.append(abs_d)

    # -------------------------------------------------------------------------
    # SLIDE 1: COVER SLIDE
    # -------------------------------------------------------------------------
    # Deep premium background
    c.setFillColor(DARK_NAVY)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    # Gold Accent Top Bar
    c.setFillColor(GOLD)
    c.rect(0, H - 6, W, 6, fill=1, stroke=0)

    # Top Tag
    c.setFont(FONTB, 11)
    c.setFillColor(HexColor("#fbbf24"))
    c.drawString(60, H - 70, "P A R T N E R S H I P   P R O P O S A L")

    # Main Co-Branded Title
    c.setFont(FONTB, 34)
    c.setFillColor(white)
    c.drawString(60, H - 120, f"{brand_name.upper()}  ×  BEKS CITY RUN CLUB")

    # Proposed Role Pill
    c.setFillColor(EMERALD)
    c.setStrokeColor(GOLD)
    c.setLineWidth(1.5)
    c.roundRect(60, H - 175, 480, 36, 6, fill=1, stroke=1)
    c.setFillColor(white)
    c.setFont(FONTB, 13)
    c.drawString(75, H - 153, f"Proposed Role: {proposed_role}")

    # Draw Brand Logo if present
    if brand_logo_file and os.path.exists(brand_logo_file):
        try:
            # White backing box for clean logo presentation
            c.setFillColor(white)
            c.roundRect(W - 270, H - 240, 210, 110, 8, fill=1, stroke=0)
            c.drawImage(brand_logo_file, W - 255, H - 225, width=180, height=80, preserveAspectRatio=True, mask="auto")
        except Exception as e:
            print(f"[ProposalPDF] Failed to render cover logo: {e}")

    # Pitch Hook Statement
    pitch_hook = proposal_data.get("pitch_hook") or (
        f"We'd like to invite {brand_name} to become the {proposed_role} of Beks City Run Club, "
        "connecting your brand directly with Abeokuta's premier urban running community through "
        "authentic on-ground engagement and experiential activations."
    )
    draw_para(c, pitch_hook, 60, H - 215, 560, size=11, lead=16, col=HexColor("#e2e8f0"))

    # Bottom Metadata Panel
    c.setFillColor(HexColor("#1f2937"))
    c.roundRect(60, 50, W - 120, 110, 8, fill=1, stroke=0)

    c.setFont(FONTB, 9.5)
    c.setFillColor(HexColor("#fbbf24"))
    c.drawString(85, 132, "PREPARED FOR")
    c.drawString(330, 132, "PREPARED BY")
    c.drawString(570, 132, "LOCATION & MARKET")
    c.drawString(770, 132, "COMMUNITY REACH")

    c.setFont(FONTB, 12)
    c.setFillColor(white)
    c.drawString(85, 112, f"The {brand_name} Team")
    c.drawString(330, 112, "BEKSCITY RUN CLUB")
    c.drawString(570, 112, "Abeokuta, Ogun State")
    c.drawString(770, 112, "1,000+ Runners")

    c.setFont(FONT, 9)
    c.setFillColor(HexColor("#9ca3af"))
    c.drawString(85, 94, "Brand & Sponsorship Leadership")
    c.drawString(330, 94, "Co-founders & Archers Live")
    c.drawString(570, 94, "Nigeria (4 Key Districts)")
    c.drawString(770, 94, "200k+ Digital Views")

    c.showPage()

    # -------------------------------------------------------------------------
    # SLIDE 2: PROPOSED PARTNERSHIP / WHAT WE ARE REQUESTING
    # -------------------------------------------------------------------------
    draw_slide_header(c, "Proposed Partnership", "What We Are Requesting", 2, brand_name)

    intro_req = (
        f"We would like to formally invite {brand_name} to become the {proposed_role} of BEKSCITY RUN CLUB "
        "for an agreed partnership period covering our weekly runs and signature community festival events."
    )
    draw_para(c, intro_req, 50, H - 98, W - 100, size=11, lead=15, col=TEXT_MAIN, font=FONTB)

    # 5 Structured Request Cards
    req_items = [
        ("1. Product Support", "Direct product allocation for runners, volunteers, pacers, and recovery support teams based on confirmed attendance."),
        ("2. Financial Sponsorship", f"Contribution toward route logistics, road safety marshals, emergency medical escorts, timing, and stage production ({proposal_data.get('value_amount', 'Mutually agreed terms')})."),
        ("3. Infrastructure & Staging", f"Co-branded {brand_name} checkpoint stations, cooling tubs, gazebo tents, and start/finish line feather banners."),
        ("4. Brand Activation Support", "Active product sampling, finish-line recovery experience, and runner engagement zones."),
        ("5. Multi-Event Consideration", "A long-term multi-event or annual roadmap as the BEKSCITY running community expands across Ogun State.")
    ]

    card_y = H - 150
    for title_txt, body_txt in req_items:
        c.setFillColor(CARD_BG)
        c.setStrokeColor(CARD_BORDER)
        c.setLineWidth(1)
        c.roundRect(50, card_y - 44, W - 100, 48, 6, fill=1, stroke=1)

        c.setFillColor(GOLD)
        c.rect(50, card_y - 44, 6, 48, fill=1, stroke=0)

        c.setFont(FONTB, 11)
        c.setFillColor(CHARCOAL)
        c.drawString(70, card_y - 18, title_txt)

        c.setFont(FONT, 9.5)
        c.setFillColor(TEXT_MUTED)
        c.drawString(70, card_y - 34, body_txt)

        card_y -= 58

    c.showPage()

    # -------------------------------------------------------------------------
    # SLIDE 3: ABOUT US (BEKSCITY RUN CLUB)
    # -------------------------------------------------------------------------
    draw_slide_header(c, "About Us", "BEKSCITY RUN CLUB — Grassroots Running Movement", 3, brand_name)

    about_body = (
        "BEKSCITY RUN CLUB (BCRC) is a community-driven athletic and wellness movement in Abeokuta, Ogun State, "
        "committed to promoting distance running, cardiovascular fitness, and active lifestyle habits through weekly "
        "structured group runs and themed running festivals.\n\n"
        "Our runs unite runners of all athletic abilities — from beginners to seasoned marathoners, university students, "
        "and young professionals. All marquee runs are produced in technical partnership with ARCHERS LIVE, ensuring "
        "every activation meets the highest standards of safety, logistics, sound, and athlete hospitality."
    )
    draw_para(c, about_body, 50, H - 100, 500, size=10, lead=15, col=TEXT_MAIN)

    # 4 Permanent Districts Grid (Right side)
    c.setFont(FONTB, 11)
    c.setFillColor(CHARCOAL)
    c.drawString(590, H - 98, "OUR 4 PERMANENT RUNNING DISTRICTS")

    districts = [
        ("Mile District", "Moore junction", "Central hub for signature runs & festival finishes"),
        ("Pharmafit District", "Kemta junction", "Elevation training, hills & endurance stamina"),
        ("Panseke District", "Skating ground", "Youth commercial center & sprint checkpoints"),
        ("Funaab District", "Funaab gate", "Campus connector & collegiate student athletes")
    ]

    dy = H - 125
    for name_d, spot_d, desc_d in districts:
        c.setFillColor(CARD_BG)
        c.setStrokeColor(CARD_BORDER)
        c.roundRect(590, dy - 40, 320, 44, 6, fill=1, stroke=1)

        c.setFont(FONTB, 10)
        c.setFillColor(EMERALD)
        c.drawString(605, dy - 16, name_d.upper())

        c.setFont(FONTB, 9)
        c.setFillColor(CHARCOAL)
        c.drawString(605, dy - 30, f"Meet-up: {spot_d}")

        c.setFont(FONT, 7.5)
        c.setFillColor(TEXT_SUB)
        c.drawRightString(895, dy - 30, desc_d[:32])

        dy -= 52

    # Verified Metrics Banner at Bottom
    c.setFillColor(DARK_NAVY)
    c.roundRect(50, 60, W - 100, 75, 8, fill=1, stroke=0)

    stats = [
        ("3+", "EDITIONS DELIVERED", "Proven operational capability"),
        ("1,000+", "COMBINED PARTICIPANTS", "Active runners and attendees"),
        ("~7x", "ATTENDANCE GROWTH", "80 to 600+ monthly attendees"),
        ("200k+", "SOCIAL VIDEO VIEWS", "Instagram & TikTok virality")
    ]
    sx = 80
    for num, lbl, sub_s in stats:
        c.setFont(FONTB, 22)
        c.setFillColor(HexColor("#fbbf24"))
        c.drawString(sx, 106, num)

        c.setFont(FONTB, 8.5)
        c.setFillColor(white)
        c.drawString(sx, 88, lbl)

        c.setFont(FONT, 7.5)
        c.setFillColor(HexColor("#9ca3af"))
        c.drawString(sx, 74, sub_s)

        sx += 215

    c.showPage()

    # -------------------------------------------------------------------------
    # SLIDE 4: OUR VISION / WHY THIS BRAND?
    # -------------------------------------------------------------------------
    draw_slide_header(c, "Our Vision", f"Why {brand_name}? — Strategic Alignment", 4, brand_name)

    why_p = proposal_data.get("why_partner") or (
        f"We seek strategic partnerships with brands whose core values naturally align with health, active living, "
        f"and community endurance. {brand_name}'s market positioning makes it an authentic and credible fit for "
        "our runners, moving beyond passive logo placement into meaningful, participatory experiences."
    )
    draw_para(c, why_p, 50, H - 105, W - 100, size=10.5, lead=16, col=TEXT_MAIN)

    # 4 Strategic Opportunity Cards in 2x2 Grid
    opps = [
        ("Authentic Product Trial", f"Introduce {brand_name} directly to 600+ health-conscious runners in an actual sporting environment where recovery, performance, and lifestyle matter."),
        ("Repeated Brand Touchpoints", f"Build lasting brand recall through repeated exposure across weekly Saturday training runs and high-energy monthly signature festivals in Abeokuta."),
        ("Dominant Regional Footprint", f"Establish {brand_name} as a pioneer wellness champion in the rapidly growing Ogun State sports and youth demographic."),
        ("Organic Digital Amplification", f"Leverage BCRC's viral user-generated content, race photography, and post-event recap reels reaching over 200k+ active viewers.")
    ]

    c_w = (W - 130) / 2
    c_h = 105
    for idx, (head_o, text_o) in enumerate(opps):
        col_idx = idx % 2
        row_idx = idx // 2
        bx = 50 + col_idx * (c_w + 30)
        by = H - 240 - row_idx * (c_h + 20)

        c.setFillColor(CARD_BG)
        c.setStrokeColor(CARD_BORDER)
        c.setLineWidth(1)
        c.roundRect(bx, by, c_w, c_h, 8, fill=1, stroke=1)

        c.setFillColor(EMERALD if idx % 2 == 0 else GOLD)
        c.rect(bx, by + c_h - 6, c_w, 6, fill=1, stroke=0)

        c.setFont(FONTB, 11)
        c.setFillColor(CHARCOAL)
        c.drawString(bx + 16, by + c_h - 26, head_o)

        draw_para(c, text_o, bx + 16, by + c_h - 44, c_w - 32, size=9, lead=13, col=TEXT_MUTED)

    c.showPage()

    # -------------------------------------------------------------------------
    # SLIDE 5: IN RETURN (WHAT BCRC OFFERS THE BRAND)
    # -------------------------------------------------------------------------
    draw_slide_header(c, "In Return", f"What Beks City Run Club Offers {brand_name}", 5, brand_name)

    intro_ret = f"Deliverables are tailored and guaranteed to maximize return on investment for {brand_name}:"
    draw_para(c, intro_ret, 50, H - 98, W - 100, size=10.5, lead=14, col=TEXT_MAIN, font=FONTB)

    # Deliverables from proposal data or defaults
    deliv_text = proposal_data.get("deliverables") or ""
    deliv_lines = [line.strip().lstrip("•- ") for line in deliv_text.split("\n") if line.strip()]
    if not deliv_lines:
        deliv_lines = [
            f"Official recognition as the {proposed_role} across all press and media releases",
            f"Prominent {brand_name} branding on finish line gantries, stage backdrops, and feather flags",
            f"Dedicated {brand_name} experiential activation station at Moore Junction / Kemta Junction",
            "Direct product sampling rights to every registered runner and spectator",
            "Minimum 3 dedicated co-branded Instagram Reels & TikTok recaps (200k+ collective reach)",
            "Logo placement on weekly digital calendar PDFs, route maps, and event web portals",
            "Full commercial rights to official event photography and recap video clips"
        ]

    dy = H - 128
    for line_d in deliv_lines[:7]:
        c.setFillColor(white)
        c.setStrokeColor(CARD_BORDER)
        c.roundRect(50, dy - 28, W - 100, 32, 5, fill=1, stroke=1)

        c.setFillColor(EMERALD)
        c.circle(68, dy - 12, 5, fill=1, stroke=0)

        c.setFont(FONT, 9.5)
        c.setFillColor(CHARCOAL)
        c.drawString(84, dy - 15, line_d)

        dy -= 38

    c.showPage()

    # -------------------------------------------------------------------------
    # SLIDE 6: PROPOSED EVENT ACTIVATION
    # -------------------------------------------------------------------------
    draw_slide_header(c, "Activation", f"Proposed On-Ground Event Activations", 6, brand_name)

    act_intro = "Experiential touchpoints that embed your brand into the runners' journey:"
    draw_para(c, act_intro, 50, H - 98, W - 100, size=10.5, lead=14, col=TEXT_MAIN, font=FONTB)

    act_text = proposal_data.get("activations") or ""
    act_lines = [line.strip().lstrip("•- ") for line in act_text.split("\n") if line.strip()]
    if not act_lines:
        act_lines = [
            f"{brand_name} Hydration & Energy Checkpoint at Mile 5 (Moore Junction)",
            f"{brand_name} Rapid Recovery Zone (Ice-cold product distribution & recovery drills)",
            f"Direct runner sampling & brand ambassador product education",
            "Branded photo opportunity & social media celebration wall",
            "Fastest Split Challenge & 'Runner of the Day' branded podium award"
        ]

    ay = H - 135
    for idx, act in enumerate(act_lines[:5], 1):
        c.setFillColor(CARD_BG)
        c.setStrokeColor(CARD_BORDER)
        c.roundRect(50, ay - 46, W - 100, 52, 6, fill=1, stroke=1)

        c.setFillColor(DARK_NAVY)
        c.roundRect(56, ay - 40, 40, 40, 4, fill=1, stroke=0)
        c.setFillColor(GOLD)
        c.setFont(FONTB, 16)
        c.drawCentredString(76, ay - 26, str(idx))

        c.setFont(FONTB, 11)
        c.setFillColor(CHARCOAL)
        c.drawString(110, ay - 18, act)

        c.setFont(FONT, 8.5)
        c.setFillColor(TEXT_MUTED)
        c.drawString(110, ay - 34, "Executed with professional marshals and media team to guarantee participant immersion.")

        ay -= 62

    c.showPage()

    # -------------------------------------------------------------------------
    # SLIDE 7: PARTNERSHIP FRAMEWORK (3 TIERS)
    # -------------------------------------------------------------------------
    draw_slide_header(c, "Framework", "Partnership Options & Commercial Framework", 7, brand_name)

    col_w = (W - 140) / 3
    col_h = 360
    base_y = 65

    tiers = [
        ("OPTION 1", "Product Partner", "Product-Only Support", [
            "100% Product support allocation",
            "Checkpoint hydration station",
            "Logo on recap flyers & digital exports",
            "Product sampling rights to runners",
            "Standard event photo coverage"
        ], False),
        ("OPTION 2", "Community Partner", "Product + ₦650,000 Support", [
            "Product support + logistical funding",
            "Branded recovery activation lounge",
            "Feather flags & start/finish signage",
            "2 Dedicated Instagram Reels recaps",
            "VIP passes for brand personnel"
        ], False),
        ("OPTION 3", "Strategic Partner", proposal_data.get("value_amount") or "₦1,500,000 + Product", [
            f"Official {proposed_role} title",
            "Dominant finish line & stage branding",
            "Exclusive category rights",
            "3+ Dedicated Reels & photo album",
            "Annual multi-event roadmap consideration"
        ], True)
    ]

    for i, (tag, tname, price, perks, is_rec) in enumerate(tiers):
        bx = 50 + i * (col_w + 20)

        # Background
        c.setFillColor(HexColor("#fefce8") if is_rec else CARD_BG)
        c.setStrokeColor(GOLD if is_rec else CARD_BORDER)
        c.setLineWidth(2 if is_rec else 1)
        c.roundRect(bx, base_y, col_w, col_h, 8, fill=1, stroke=1)

        # Header tag
        c.setFillColor(EMERALD if is_rec else CHARCOAL)
        c.roundRect(bx, base_y + col_h - 36, col_w, 36, 6, fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont(FONTB, 11)
        c.drawCentredString(bx + col_w / 2, base_y + col_h - 22, f"{tag} {'★ RECOMMENDED' if is_rec else ''}")

        # Tier title & valuation
        c.setFont(FONTB, 14)
        c.setFillColor(CHARCOAL)
        c.drawCentredString(bx + col_w / 2, base_y + col_h - 60, tname)

        c.setFont(FONTB, 10.5)
        c.setFillColor(GOLD if is_rec else TEXT_MUTED)
        c.drawCentredString(bx + col_w / 2, base_y + col_h - 78, price)

        c.setStrokeColor(LINE_COL)
        c.setLineWidth(0.8)
        c.line(bx + 20, base_y + col_h - 90, bx + col_w - 20, base_y + col_h - 90)

        # Perks list
        py = base_y + col_h - 115
        for perk in perks:
            c.setFillColor(EMERALD)
            c.drawString(bx + 18, py, "✓")
            c.setFont(FONT, 8.5)
            c.setFillColor(TEXT_MAIN)
            c.drawString(bx + 32, py, perk[:34])
            py -= 28

    c.showPage()

    # -------------------------------------------------------------------------
    # SLIDE 8: COMMERCIAL PRINCIPLES (FAIR & SUSTAINABLE)
    # -------------------------------------------------------------------------
    draw_slide_header(c, "Commercial Principles", "Fair & Sustainable, By Design", 8, brand_name)

    principles = [
        ("1. Proportionate Benefits", "Partnership entitlements and deliverables are strictly tied to the confirmed level and duration of contribution."),
        ("2. Defined Exclusivity", "Category exclusivity is clearly bounded to an agreed timeframe and defined product scope without open-ended ambiguity."),
        ("3. Intellectual Property Protection", "BCRC retains ownership of its club marks, community identity, and event IP unless explicitly licensed in writing."),
        ("4. Transparent Media Rights", "Commercial re-use of BCRC event photography, videography, or participant content requires documented consent."),
        ("5. Pre-Event Specification", "All quantities, branding coordinates, dates, and volunteer support duties are documented and locked in prior to race day."),
        ("6. No Open-Ended Obligations", "Guarantees a clean, structured commercial partnership without indefinite liabilities or unagreed promotional burdens.")
    ]

    p_w = (W - 130) / 2
    p_h = 95
    for idx, (p_title, p_desc) in enumerate(principles):
        col_idx = idx % 2
        row_idx = idx // 2
        bx = 50 + col_idx * (p_w + 30)
        by = H - 210 - row_idx * (p_h + 15)

        c.setFillColor(CARD_BG)
        c.setStrokeColor(CARD_BORDER)
        c.roundRect(bx, by, p_w, p_h, 6, fill=1, stroke=1)

        c.setFont(FONTB, 11)
        c.setFillColor(CHARCOAL)
        c.drawString(bx + 16, by + p_h - 24, p_title)

        draw_para(c, p_desc, bx + 16, by + p_h - 42, p_w - 32, size=9, lead=13, col=TEXT_MUTED)

    c.showPage()

    # -------------------------------------------------------------------------
    # SLIDE 9: COMMUNITY GALLERY (BCRC IN ACTION)
    # -------------------------------------------------------------------------
    draw_slide_header(c, "Community Gallery", "BCRC In Action — Abeokuta's Premier Fitness Tribe", 9, brand_name)

    # 4-Photo Collage of high-res action shots
    gw = (W - 130) / 4
    gh = 340
    gy = 65

    for idx in range(4):
        bx = 50 + idx * (gw + 10)
        img_path = run_club_imgs[idx] if idx < len(run_club_imgs) else None

        c.setFillColor(CARD_BG)
        c.setStrokeColor(CARD_BORDER)
        c.roundRect(bx, gy, gw, gh, 8, fill=1, stroke=1)

        if img_path and os.path.exists(img_path):
            try:
                # Save and restore canvas clip to keep images neatly rounded
                c.saveState()
                p = c.beginPath()
                p.roundRect(bx + 2, gy + 2, gw - 4, gh - 4, 6)
                c.clipPath(p, stroke=0)
                c.drawImage(img_path, bx + 2, gy + 2, width=gw - 4, height=gh - 4, preserveAspectRatio=True, mask="auto")
                c.restoreState()
            except Exception as e:
                print(f"[ProposalPDF] Failed rendering gallery image {img_path}: {e}")
        else:
            c.setFont(FONTB, 10)
            c.setFillColor(TEXT_SUB)
            c.drawCentredString(bx + gw / 2, gy + gh / 2, f"BCRC Action Shot {idx+1}")

    c.showPage()

    # -------------------------------------------------------------------------
    # SLIDE 10: LONG-TERM OPPORTUNITY
    # -------------------------------------------------------------------------
    draw_slide_header(c, "Long-Term Opportunity", "Built to Grow, Together", 10, brand_name)

    lt_body = (
        f"While our immediate partnership can activate around the upcoming {event_name}, we believe "
        f"the greatest commercial value lies in a multi-event and annual strategic alignment. "
        f"A multi-event relationship allows {brand_name} to cement sustained awareness, brand affinity, and "
        "habitual loyalty among active consumers across Abeokuta and Ogun State.\n\n"
        "BEKSCITY RUN CLUB provides a turn-key experiential platform: disciplined weekly Saturday runs, "
        "energetic community engagement, professional media recaps, and an enthusiastic young demographic. "
        f"Together, we can establish {brand_name} as a permanent lifestyle pillar in the region's active culture."
    )
    draw_para(c, lt_body, 50, H - 110, W - 100, size=11, lead=17, col=TEXT_MAIN)

    # Growth Roadmap Box
    c.setFillColor(DARK_NAVY)
    c.roundRect(50, 65, W - 100, 160, 8, fill=1, stroke=0)

    c.setFont(FONTB, 13)
    c.setFillColor(HexColor("#fbbf24"))
    c.drawString(75, 195, "LONG-TERM COLLABORATION ROADMAP (2026 – 2027)")

    phases = [
        ("Phase 1: Activation Launch", f"{event_name} Marquee Debut", "Headline checkpoint & sampling integration"),
        ("Phase 2: Monthly Saturday Rhythm", "Weekly Continuous Touchpoints", "Sustained product presence across all 4 districts"),
        ("Phase 3: Quarterly Grand Festivals", "Run & Rumble, Run & Splash", "Exclusive title partnership and festival stage production")
    ]
    px = 75
    for p_num, p_head, p_sub in phases:
        c.setFont(FONTB, 10)
        c.setFillColor(HexColor("#34d399"))
        c.drawString(px, 160, p_num.upper())

        c.setFont(FONTB, 11)
        c.setFillColor(white)
        c.drawString(px, 142, p_head)

        c.setFont(FONT, 8.5)
        c.setFillColor(HexColor("#9ca3af"))
        c.drawString(px, 126, p_sub)

        px += 280

    c.showPage()

    # -------------------------------------------------------------------------
    # SLIDE 11: LET'S BUILD THIS TOGETHER (CONTACT & NEXT STEPS)
    # -------------------------------------------------------------------------
    draw_slide_header(c, "Let's Build This Together", "Next Steps & Co-Founders Leadership", 11, brand_name)

    closing_text = (
        f"We welcome the opportunity to meet with the {brand_name} team to finalize partnership tiers, "
        "tailor deliverables to your corporate objectives, and deliver an unforgettable brand experience."
    )
    draw_para(c, closing_text, 50, H - 105, W - 100, size=11, lead=16, col=TEXT_MAIN, font=FONTB)

    # Co-founders Contact Cards
    cfs = [
        ("Oladipupo Abdulazeez", "08101674646", "@jughead_x3", "Co-Founder & Operations"),
        ("Shittu Oluwadamilare", "08168120117", "@sweetboycoal", "Co-Founder & Partnerships"),
        ("Adebanjo Oluwatobiloba", "07069582118", "@tobenzin", "Co-Founder & Logistics")
    ]

    cf_w = (W - 140) / 3
    cf_h = 130
    for i, (cf_name, cf_phone, cf_social, cf_role) in enumerate(cfs):
        bx = 50 + i * (cf_w + 20)
        by = H - 280

        c.setFillColor(CARD_BG)
        c.setStrokeColor(CARD_BORDER)
        c.roundRect(bx, by, cf_w, cf_h, 8, fill=1, stroke=1)

        c.setFillColor(GOLD)
        c.rect(bx, by + cf_h - 4, cf_w, 4, fill=1, stroke=0)

        c.setFont(FONTB, 12)
        c.setFillColor(CHARCOAL)
        c.drawString(bx + 16, by + cf_h - 26, cf_name)

        c.setFont(FONT, 9)
        c.setFillColor(TEXT_MUTED)
        c.drawString(bx + 16, by + cf_h - 42, cf_role)

        c.setFont(FONTB, 9.5)
        c.setFillColor(EMERALD)
        c.drawString(bx + 16, by + cf_h - 68, f"📱 {cf_phone}")

        c.setFont(FONTB, 9.5)
        c.setFillColor(CHARCOAL)
        c.drawString(bx + 16, by + cf_h - 90, f"📸 {cf_social}")

    # Official Club Channels
    c.setFillColor(DARK_NAVY)
    c.roundRect(50, 50, W - 100, 75, 8, fill=1, stroke=0)

    c.setFont(FONTB, 11)
    c.setFillColor(HexColor("#fbbf24"))
    c.drawString(75, 96, "OFFICIAL COMMUNICATIONS & DIGITAL HUB")

    c.setFont(FONT, 9.5)
    c.setFillColor(white)
    c.drawString(75, 74, "📧 partnerships@bekscity.run  |  Bekscityrunclub@gmail.com")
    c.drawString(500, 74, "🌐 bekscity.run  |  📸 @beks.cityrunclub  |  📍 Abeokuta, Ogun State, Nigeria")

    c.showPage()
    c.save()
    return output_path


def _build_proposal_pdf_from_template(output_path, proposal_data, template_path, template_type):
    """
    Brands the authentic master PDF template matching the user's local device files
    ('Pocari Sweat Proposal.pdf' or 'editable.pdf') with dynamic brand data, logos, and gallery photos.
    """
    doc = fitz.open(template_path)
    brand_name = (proposal_data.get("brand_name") or "PARTNER BRAND").strip()
    proposed_role = (proposal_data.get("proposed_role") or proposal_data.get("partnership_tier") or "Official Category Partner").strip()

    # Resolve logo local path
    logo_source = proposal_data.get("brand_logo_url")
    logo_local = None
    if logo_source:
        if logo_source.startswith("http"):
            logo_local = safe_download_image(logo_source)
        elif logo_source.startswith("/static/"):
            candidate = os.path.join(HERE, logo_source.lstrip("/"))
            if os.path.exists(candidate):
                logo_local = candidate
        elif os.path.exists(logo_source):
            logo_local = logo_source

    # Parse gallery images
    gallery_imgs = []
    raw_gallery = proposal_data.get("run_club_images")
    if raw_gallery:
        if isinstance(raw_gallery, str) and raw_gallery.startswith("["):
            try:
                gallery_imgs = json.loads(raw_gallery)
            except Exception:
                gallery_imgs = []
        elif isinstance(raw_gallery, str):
            gallery_imgs = [s.strip() for s in raw_gallery.split(",") if s.strip()]
        elif isinstance(raw_gallery, list):
            gallery_imgs = raw_gallery

    if template_type == "run_and_rumble":
        # 14-page Run & Rumble template (editable.pdf)
        p1 = doc[0]
        p1.insert_text(
            (55, 380),
            f"Prepared for: {brand_name.upper()}",
            fontsize=13,
            fontname="helv",
            color=(0.85, 0.65, 0.25)
        )
        if logo_local and os.path.exists(logo_local):
            try:
                p1.insert_image(fitz.Rect(55, 400, 180, 470), filename=logo_local, keep_proportion=True)
            except Exception as e:
                print(f"[proposal_pdf] Warning inserting logo into editable.pdf: {e}")

        # Page 12: Photo collage
        if len(doc) > 11 and gallery_imgs:
            p12 = doc[11]
            rects12 = [
                fitz.Rect(43.2, 129.6, 324.8, 302.4),
                fitz.Rect(339.2, 129.6, 620.8, 302.4),
                fitz.Rect(635.2, 129.6, 916.8, 302.4),
                fitz.Rect(43.2, 316.8, 324.8, 489.6),
                fitz.Rect(339.2, 316.8, 620.8, 489.6),
                fitz.Rect(635.2, 316.8, 916.8, 489.6)
            ]
            for r, img_url in zip(rects12, gallery_imgs):
                local_img = resolve_local_gallery_path(img_url)
                if local_img and os.path.exists(local_img):
                    try:
                        p12.insert_image(r, filename=local_img, keep_proportion=False)
                    except Exception:
                        pass

    else:
        # 11-page Partnership Proposal template (Pocari Sweat Proposal.pdf)
        is_pocari = (brand_name.upper() == "POCARI SWEAT")

        if not is_pocari:
            for page in doc:
                # Search and redact POCARI SWEAT
                hits = page.search_for("POCARI SWEAT")
                for h in hits:
                    page.add_redact_annot(h, text=brand_name.upper(), fontname="helv", fontsize=h.height * 0.72)

                # Search and redact Official Hydration Partner
                hits_role = page.search_for("Official Hydration Partner")
                for hr in hits_role:
                    page.add_redact_annot(hr, text=proposed_role, fontname="helv", fontsize=hr.height * 0.72)

                page.apply_redactions()

        # Page 1: Brand Logo replacement
        # Unconditionally obliterate the original Pocari Sweat logo if this proposal is for another brand!
        if not is_pocari:
            p1 = doc[0]
            logo_rect = fitz.Rect(741.72, 32.40, 910.56, 135.72)
            p1.add_redact_annot(logo_rect, fill=(17/255, 24/255, 39/255))
            p1.apply_redactions()

            if logo_local and os.path.exists(logo_local):
                try:
                    p1.insert_image(logo_rect, filename=logo_local, keep_proportion=True)
                except Exception as e:
                    print(f"[proposal_pdf] Warning inserting logo into Pocari PDF: {e}")
            else:
                # Polished fallback badge when brand logo is unavailable
                try:
                    p1.draw_rect(logo_rect, color=(217/255, 164/255, 65/255), width=1.5, fill=(24/255, 32/255, 47/255))
                    badge_text = brand_name.upper()
                    font_sz = min(13.0, max(8.5, 130.0 / max(1, len(badge_text))))
                    text_w = fitz.get_text_length(badge_text, fontname="helv", fontsize=font_sz)
                    tx = logo_rect.x0 + (logo_rect.width - text_w) / 2
                    ty = logo_rect.y0 + (logo_rect.height / 2) + (font_sz / 3)
                    p1.insert_text((tx, ty), badge_text, fontname="helv", fontsize=font_sz, color=(1, 1, 1))
                except Exception as e:
                    print(f"[proposal_pdf] Warning drawing brand badge: {e}")

        # Page 9: 4 Community Gallery images
        if len(doc) > 8 and gallery_imgs:
            p9 = doc[8]
            rects9 = [
                fitz.Rect(36.0, 158.0, 256.7, 464.3),
                fitz.Rect(270.4, 157.3, 490.0, 463.6),
                fitz.Rect(502.4, 159.7, 717.8, 464.3),
                fitz.Rect(731.8, 158.0, 951.4, 462.7)
            ]
            for r, img_url in zip(rects9, gallery_imgs):
                local_img = resolve_local_gallery_path(img_url)
                if local_img and os.path.exists(local_img):
                    try:
                        p9.insert_image(r, filename=local_img, keep_proportion=False)
                    except Exception:
                        pass

    doc.save(output_path)
    return output_path


def build_proposal_pdf(output_path, proposal_data):
    """
    Main PDF dispatcher:
    Uses the master template PDF matching the user's local device files ('Pocari Sweat Proposal.pdf' or 'editable.pdf').
    Falls back gracefully to ReportLab canvas generator if template is missing.
    """
    template_type = proposal_data.get("presentation_template") or "partnership_proposal"
    tpl_path = find_pdf_template(template_type)
    if tpl_path and FITZ_AVAILABLE:
        try:
            return _build_proposal_pdf_from_template(output_path, proposal_data, tpl_path, template_type)
        except Exception as e:
            print(f"[proposal_pdf] Master PDF template branding error: {e}, falling back to ReportLab.")

    return _build_proposal_pdf_reportlab(output_path, proposal_data)


"""
BEKSCITY RUN CLUB — Executive Pitch Deck PowerPoint (.pptx) Generator
Generates an 11-slide 16:9 widescreen presentation deck using python-pptx.
"""

import os
import json
import pptx
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

HERE = os.path.dirname(os.path.abspath(__file__))

# Colors
C_DARK_NAVY = RGBColor(17, 24, 39)
C_CHARCOAL = RGBColor(27, 27, 31)
C_GOLD = RGBColor(217, 164, 65)
C_EMERALD = RGBColor(30, 94, 66)
C_WHITE = RGBColor(255, 255, 255)
C_CARD_BG = RGBColor(248, 250, 252)
C_MUTED = RGBColor(100, 116, 139)
C_LIGHT_GRAY = RGBColor(226, 232, 240)


def add_slide_header(slide, category, title, page_num, brand_name):
    # Top Tag
    tb_cat = slide.shapes.add_textbox(Inches(0.6), Inches(0.4), Inches(12.0), Inches(0.3))
    tf_cat = tb_cat.text_frame
    p_cat = tf_cat.paragraphs[0]
    p_cat.text = category.upper()
    p_cat.font.size = Pt(11)
    p_cat.font.bold = True
    p_cat.font.color.rgb = C_GOLD

    # Title
    tb_title = slide.shapes.add_textbox(Inches(0.6), Inches(0.7), Inches(12.0), Inches(0.6))
    tf_title = tb_title.text_frame
    p_title = tf_title.paragraphs[0]
    p_title.text = title
    p_title.font.size = Pt(22)
    p_title.font.bold = True
    p_title.font.color.rgb = C_CHARCOAL

    # Running Footer
    tb_foot = slide.shapes.add_textbox(Inches(0.6), Inches(6.9), Inches(12.0), Inches(0.3))
    tf_foot = tb_foot.text_frame
    p_foot = tf_foot.paragraphs[0]
    p_foot.text = f"BEKSCITY RUN CLUB  ×  {brand_name.upper()}   |   Slide {page_num:02d}"
    p_foot.font.size = Pt(9)
    p_foot.font.color.rgb = C_MUTED


def build_proposal_pptx(output_path, proposal_data):
    prs = pptx.Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    brand_name = (proposal_data.get("brand_name") or "Brand Partner").strip()
    proposed_role = (proposal_data.get("proposed_role") or "Official Category Partner").strip()
    tier = (proposal_data.get("partnership_tier") or "Strategic Partner").strip()
    event_name = (proposal_data.get("event_name") or "Run and Rumble").strip()

    # SLIDE 1: COVER
    s1 = prs.slides.add_slide(blank_layout)
    bg1 = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    bg1.fill.solid()
    bg1.fill.fore_color.rgb = C_DARK_NAVY
    bg1.line.fill.background()

    # Top Gold Rule
    rule = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(0.1))
    rule.fill.solid()
    rule.fill.fore_color.rgb = C_GOLD
    rule.line.fill.background()

    tb1 = s1.shapes.add_textbox(Inches(0.8), Inches(1.0), Inches(11.7), Inches(2.5))
    tf1 = tb1.text_frame
    p1 = tf1.paragraphs[0]
    p1.text = "P A R T N E R S H I P   P R O P O S A L"
    p1.font.size = Pt(13)
    p1.font.bold = True
    p1.font.color.rgb = C_GOLD

    p2 = tf1.add_paragraph()
    p2.text = f"{brand_name.upper()}  ×  BEKS CITY RUN CLUB"
    p2.font.size = Pt(36)
    p2.font.bold = True
    p2.font.color.rgb = C_WHITE

    p3 = tf1.add_paragraph()
    p3.text = f"Proposed Role: {proposed_role}"
    p3.font.size = Pt(16)
    p3.font.bold = True
    p3.font.color.rgb = C_GOLD

    pitch = proposal_data.get("pitch_hook") or f"Inviting {brand_name} to power Abeokuta's premier running movement."
    p4 = tf1.add_paragraph()
    p4.text = pitch
    p4.font.size = Pt(12)
    p4.font.color.rgb = RGBColor(226, 232, 240)

    # Footer Card on Slide 1
    f_card = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(5.2), Inches(11.733), Inches(1.5))
    f_card.fill.solid()
    f_card.fill.fore_color.rgb = RGBColor(31, 41, 55)
    f_card.line.fill.background()

    tb_meta = s1.shapes.add_textbox(Inches(1.1), Inches(5.4), Inches(11.1), Inches(1.1))
    tf_meta = tb_meta.text_frame
    pm1 = tf_meta.paragraphs[0]
    pm1.text = f"PREPARED FOR: The {brand_name} Team   |   PREPARED BY: BEKSCITY RUN CLUB & Archers Live"
    pm1.font.size = Pt(12)
    pm1.font.bold = True
    pm1.font.color.rgb = C_WHITE

    pm2 = tf_meta.add_paragraph()
    pm2.text = "LOCATION: Abeokuta, Ogun State, Nigeria (4 Key Districts: Mile, Pharmafit, Panseke, Funaab)"
    pm2.font.size = Pt(10)
    pm2.font.color.rgb = RGBColor(156, 163, 175)

    pm3 = tf_meta.add_paragraph()
    pm3.text = "TRACK RECORD: 3+ Editions Delivered   |   1,000+ Combined Participants   |   200,000+ Social Media Video Views"
    pm3.font.size = Pt(10)
    pm3.font.color.rgb = C_GOLD

    # SLIDE 2: WHAT WE ARE REQUESTING
    s2 = prs.slides.add_slide(blank_layout)
    add_slide_header(s2, "Proposed Partnership", "What We Are Requesting", 2, brand_name)

    tb2 = s2.shapes.add_textbox(Inches(0.6), Inches(1.6), Inches(12.0), Inches(5.0))
    tf2 = tb2.text_frame
    reqs = [
        "1. Product Support: Chilled product allocation for runners, volunteers, and support crews based on attendance.",
        f"2. Financial Sponsorship: Logistical support toward route safety, emergency medical escorts, timing chips, and staging ({proposal_data.get('value_amount', 'Terms per agreement')}).",
        f"3. Infrastructure: Co-branded {brand_name} checkpoints, hydration stations, cooling tubs, and feather banners.",
        "4. Brand Activation: On-ground product sampling, recovery experience zone, and runner engagement.",
        "5. Multi-Event Pathway: Multi-event or annual consideration as BCRC expands across Ogun State."
    ]
    for r in reqs:
        p = tf2.add_paragraph()
        p.text = r
        p.font.size = Pt(13)
        p.font.color.rgb = C_CHARCOAL
        p.space_after = Pt(14)

    # SLIDE 3: ABOUT US
    s3 = prs.slides.add_slide(blank_layout)
    add_slide_header(s3, "About Us", "BEKSCITY RUN CLUB — Grassroots Running Movement", 3, brand_name)

    tb3 = s3.shapes.add_textbox(Inches(0.6), Inches(1.6), Inches(6.0), Inches(5.0))
    tf3 = tb3.text_frame
    p_a = tf3.paragraphs[0]
    p_a.text = (
        "BEKSCITY RUN CLUB is Abeokuta's premier active lifestyle movement, bringing together runners, "
        "university students, and young professionals for weekly Saturday morning runs and grand themed festivals.\n\n"
        "Delivered with ARCHERS LIVE, our official production partner, ensuring professional safety, "
        "electronic timing, traffic management, and high-energy community experiences."
    )
    p_a.font.size = Pt(12)
    p_a.font.color.rgb = C_CHARCOAL

    tb3_d = s3.shapes.add_textbox(Inches(7.0), Inches(1.6), Inches(5.6), Inches(5.0))
    tf3_d = tb3_d.text_frame
    p_dh = tf3_d.paragraphs[0]
    p_dh.text = "OUR 4 PERMANENT RUNNING DISTRICTS:"
    p_dh.font.size = Pt(12)
    p_dh.font.bold = True
    p_dh.font.color.rgb = C_GOLD

    d_list = [
        "• Mile District (Moore junction): Signature runs & festival finishes",
        "• Pharmafit District (Kemta junction): Elevation training & endurance stamina",
        "• Panseke District (Skating ground): Youth commercial center & sprint checkpoints",
        "• Funaab District (Funaab gate): Collegiate athletes & campus tempo runs"
    ]
    for dl in d_list:
        p = tf3_d.add_paragraph()
        p.text = dl
        p.font.size = Pt(11)
        p.font.color.rgb = C_CHARCOAL
        p.space_after = Pt(6)

    # SLIDE 4: OUR VISION / WHY THIS BRAND?
    s4 = prs.slides.add_slide(blank_layout)
    add_slide_header(s4, "Our Vision", f"Why {brand_name}? — Strategic Alignment", 4, brand_name)

    tb4 = s4.shapes.add_textbox(Inches(0.6), Inches(1.6), Inches(12.0), Inches(5.0))
    tf4 = tb4.text_frame
    why_text = proposal_data.get("why_partner") or (
        f"{brand_name}'s market positioning makes it a natural partner for BEKSCITY RUN CLUB. "
        "Abeokuta's warm running climate and active young demographic create an authentic, high-impact "
        "environment for product trial, brand affinity, and community wellness leadership."
    )
    p_w = tf4.paragraphs[0]
    p_w.text = why_text
    p_w.font.size = Pt(13)
    p_w.font.color.rgb = C_CHARCOAL
    p_w.space_after = Pt(16)

    opps = [
        f"• Authentic Product Trial: Direct engagement with 600+ health-conscious runners.",
        f"• Repeated Brand Touchpoints: Weekly continuous presence across all 4 city districts.",
        f"• Youth & Regional Footprint: Dominant brand equity across Ogun State athletic communities.",
        f"• Organic Social Virality: 200,000+ views across Instagram & TikTok recap media."
    ]
    for o in opps:
        p = tf4.add_paragraph()
        p.text = o
        p.font.size = Pt(12)
        p.font.color.rgb = C_CHARCOAL
        p.space_after = Pt(10)

    # SLIDE 5: IN RETURN (DELIVERABLES)
    s5 = prs.slides.add_slide(blank_layout)
    add_slide_header(s5, "In Return", f"What Beks City Run Club Offers {brand_name}", 5, brand_name)

    tb5 = s5.shapes.add_textbox(Inches(0.6), Inches(1.6), Inches(12.0), Inches(5.0))
    tf5 = tb5.text_frame
    delivs = (proposal_data.get("deliverables") or "").split("\n")
    if not delivs or not delivs[0].strip():
        delivs = [
            f"Official recognition as {proposed_role} across all press and media releases",
            f"Prominent {brand_name} branding on finish line gantries, stage backdrops, and feather flags",
            f"Dedicated {brand_name} experiential activation station at Moore Junction / Kemta Junction",
            "Direct product sampling rights to every registered runner and spectator",
            "Minimum 3 dedicated co-branded Instagram Reels & TikTok recaps (200k+ collective reach)",
            "Logo placement on weekly digital calendar PDFs, route maps, and event web portals",
            "Full commercial rights to official event photography and recap video clips"
        ]
    for d in delivs:
        if d.strip():
            p = tf5.add_paragraph()
            p.text = "✓  " + d.strip().lstrip("•- ")
            p.font.size = Pt(12)
            p.font.color.rgb = C_CHARCOAL
            p.space_after = Pt(8)

    # SLIDE 6: PROPOSED ACTIVATION
    s6 = prs.slides.add_slide(blank_layout)
    add_slide_header(s6, "Activation", "Proposed On-Ground Event Activations", 6, brand_name)

    tb6 = s6.shapes.add_textbox(Inches(0.6), Inches(1.6), Inches(12.0), Inches(5.0))
    tf6 = tb6.text_frame
    acts = (proposal_data.get("activations") or "").split("\n")
    if not acts or not acts[0].strip():
        acts = [
            f"{brand_name} Checkpoint & Stations at key route landmarks",
            f"{brand_name} Post-Run Recovery Lounge & Ice-Cold Distribution",
            f"Direct runner sampling & brand ambassador product education",
            "Branded celebration photo opportunity & social media celebration wall",
            "Podium prizes & 'Runner of the Day' recognition"
        ]
    for a in acts:
        if a.strip():
            p = tf6.add_paragraph()
            p.text = "●  " + a.strip().lstrip("•- ")
            p.font.size = Pt(13)
            p.font.color.rgb = C_CHARCOAL
            p.space_after = Pt(12)

    # SLIDE 7: PARTNERSHIP FRAMEWORK
    s7 = prs.slides.add_slide(blank_layout)
    add_slide_header(s7, "Framework", "Partnership Options & Commercial Framework", 7, brand_name)

    tb7 = s7.shapes.add_textbox(Inches(0.6), Inches(1.6), Inches(12.0), Inches(5.0))
    tf7 = tb7.text_frame
    tf7.paragraphs[0].text = "OPTION 1: Product / Category Partner (Product support in exchange for checkpoint sampling)"
    tf7.paragraphs[0].font.size = Pt(12)
    tf7.paragraphs[0].font.bold = True
    tf7.paragraphs[0].font.color.rgb = C_CHARCOAL

    p_t2 = tf7.add_paragraph()
    p_t2.text = "OPTION 2: Community Partner (Product support + event operational funding in exchange for broader digital and physical visibility)"
    p_t2.font.size = Pt(12)
    p_t2.font.bold = True
    p_t2.font.color.rgb = C_CHARCOAL
    p_t2.space_before = Pt(14)

    p_t3 = tf7.add_paragraph()
    p_t3.text = f"OPTION 3: Strategic Partner (RECOMMENDED) — {proposal_data.get('value_amount', '₦1,500,000 + Product')}"
    p_t3.font.size = Pt(13)
    p_t3.font.bold = True
    p_t3.font.color.rgb = C_GOLD
    p_t3.space_before = Pt(14)

    p_t3_sub = tf7.add_paragraph()
    p_t3_sub.text = f"Headline {proposed_role} rights, exclusive category privileges, dominant staging, and annual multi-event partnership consideration."
    p_t3_sub.font.size = Pt(11)
    p_t3_sub.font.color.rgb = C_MUTED

    # SLIDE 8: COMMERCIAL PRINCIPLES
    s8 = prs.slides.add_slide(blank_layout)
    add_slide_header(s8, "Commercial Principles", "Fair & Sustainable, By Design", 8, brand_name)

    tb8 = s8.shapes.add_textbox(Inches(0.6), Inches(1.6), Inches(12.0), Inches(5.0))
    tf8 = tb8.text_frame
    principles = [
        "1. Proportionate Benefits: Rights and exposure are strictly aligned with confirmed contributions.",
        "2. Defined Category Exclusivity: Clearly bounded by agreement timeframe and product scope.",
        "3. Intellectual Property Protection: BCRC retains ownership of its club marks and community IP.",
        "4. Transparent Media Rights: Commercial reuse of BCRC event footage requires separate mutual sign-off.",
        "5. Pre-Event Specification: All quantities, branding coordinates, and deliverables locked before race day.",
        "6. No Open-Ended Obligations: Zero unlimited exposure or unagreed liabilities."
    ]
    for pr in principles:
        p = tf8.add_paragraph()
        p.text = pr
        p.font.size = Pt(11.5)
        p.font.color.rgb = C_CHARCOAL
        p.space_after = Pt(10)

    # SLIDE 9: COMMUNITY GALLERY
    s9 = prs.slides.add_slide(blank_layout)
    add_slide_header(s9, "Community Gallery", "BCRC In Action — Abeokuta's Premier Fitness Tribe", 9, brand_name)

    tb9 = s9.shapes.add_textbox(Inches(0.6), Inches(1.6), Inches(12.0), Inches(5.0))
    tf9 = tb9.text_frame
    p9 = tf9.paragraphs[0]
    p9.text = "High-energy crowd, podium celebrations, and community runners across Abeokuta:"
    p9.font.size = Pt(12)
    p9.font.color.rgb = C_CHARCOAL

    # Insert up to 4 images if present in static/img/gallery/
    gallery_files = [
        os.path.join(HERE, "static/img/gallery/image1.jpeg"),
        os.path.join(HERE, "static/img/gallery/image5.jpeg"),
        os.path.join(HERE, "static/img/gallery/image6.jpeg"),
        os.path.join(HERE, "static/img/gallery/image10.jpeg")
    ]
    x_offset = Inches(0.6)
    img_w = Inches(2.8)
    img_h = Inches(4.2)
    for g_img in gallery_files:
        if os.path.exists(g_img):
            try:
                s9.shapes.add_picture(g_img, x_offset, Inches(2.2), width=img_w, height=img_h)
            except Exception as e:
                print(f"[ProposalPPTX] Gallery image error: {e}")
        x_offset += Inches(3.0)

    # SLIDE 10: LONG-TERM OPPORTUNITY
    s10 = prs.slides.add_slide(blank_layout)
    add_slide_header(s10, "Long-Term Opportunity", "Built to Grow, Together", 10, brand_name)

    tb10 = s10.shapes.add_textbox(Inches(0.6), Inches(1.6), Inches(12.0), Inches(5.0))
    tf10 = tb10.text_frame
    p10 = tf10.paragraphs[0]
    p10.text = (
        f"While our immediate activation launches with the upcoming {event_name}, BCRC's vision is an annual "
        f"multi-event strategic alignment. As BEKSCITY expands across all four districts, {brand_name} can establish "
        "permanent community goodwill, authentic product trial, and undisputed wellness leadership in Ogun State."
    )
    p10.font.size = Pt(13)
    p10.font.color.rgb = C_CHARCOAL
    p10.space_after = Pt(20)

    p10_r = tf10.add_paragraph()
    p10_r.text = (
        "ROADMAP:\n"
        f"• Phase 1: {event_name} Marquee Launch (Checkpoint branding & finish-line sampling)\n"
        f"• Phase 2: Monthly Saturday Rhythm (Sustained presence across Moore, Kemta, Panseke, and Funaab)\n"
        f"• Phase 3: Grand Annual Running Festival (Exclusive title partnership and festival production)"
    )
    p10_r.font.size = Pt(12)
    p10_r.font.color.rgb = C_GOLD

    # SLIDE 11: LET'S BUILD THIS TOGETHER
    s11 = prs.slides.add_slide(blank_layout)
    add_slide_header(s11, "Let's Build This Together", "Next Steps & Co-Founders Leadership", 11, brand_name)

    tb11 = s11.shapes.add_textbox(Inches(0.6), Inches(1.6), Inches(12.0), Inches(5.0))
    tf11 = tb11.text_frame
    p11 = tf11.paragraphs[0]
    p11.text = (
        f"We welcome the opportunity to meet with the {brand_name} team to review this proposal, "
        "customize deliverables, and lock in our partnership timeline."
    )
    p11.font.size = Pt(13)
    p11.font.bold = True
    p11.font.color.rgb = C_CHARCOAL
    p11.space_after = Pt(20)

    cfs = [
        "• Oladipupo Abdulazeez (08101674646 | @jughead_x3) — Co-Founder & Operations",
        "• Shittu Oluwadamilare (08168120117 | @sweetboycoal) — Co-Founder & Partnerships",
        "• Adebanjo Oluwatobiloba (07069582118 | @tobenzin) — Co-Founder & Logistics",
        "",
        "Email: partnerships@bekscity.run  |  Bekscityrunclub@gmail.com",
        "Web: bekscity.run  |  Instagram: @beks.cityrunclub",
        "Location: Abeokuta, Ogun State, Nigeria"
    ]
    for cfl in cfs:
        p = tf11.add_paragraph()
        p.text = cfl
        p.font.size = Pt(11.5)
        p.font.color.rgb = C_CHARCOAL

    prs.save(output_path)
    return output_path

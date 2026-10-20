"""
BEKSCITY RUN CLUB — Brand Online Intelligence & Partnership Strategy Engine
Researches prospective partner brands online (via Wikipedia API & web intelligence),
normalizes brand aliases (e.g. Procari -> Pocari Sweat), and synthesizes a tailored
sponsorship proposal strategy matching the BCRC pitch deck template.
"""

import json
import os
import re
import urllib.parse
import urllib.request

# Curated knowledge base for common sports, beverage, nutrition and lifestyle brands
CURATED_BRANDS = {
    "pocari": {
        "canonical_name": "POCARI SWEAT",
        "parent_company": "Otsuka Pharmaceutical",
        "category": "Hydration & Electrolyte Sports Drink",
        "description": "Pocari Sweat is a premier isotonic ion-supply beverage formulated to replenish water and essential electrolytes lost through perspiration during exercise and endurance running.",
        "proposed_role": "Official Hydration Partner",
        "why_partner": "Hydration is essential to the running experience. POCARI SWEAT's positioning around replenishing fluids and essential electrolytes makes it a natural fit for BEKSCITY RUN CLUB in Abeokuta's warm running climate. Tropical humidity requires active rehydration, creating an authentic trial and consumption environment for runners.",
        "requests_summary": (
            "• Product Support: Chilled POCARI SWEAT beverage units for runners, pacers, and volunteer crew across Saturday runs.\n"
            "• Financial Sponsorship: Direct support toward course logistics, medical safety, and event production.\n"
            "• Hydration Infrastructure: Branded cooling coolers, ice tubs, branded gazebo, and cup stations.\n"
            "• Multi-Event Consideration: Annual partnership across monthly signature runs and marquee festivals."
        ),
        "deliverables": (
            "• Exclusive status as the Official Hydration Partner of BEKSCITY RUN CLUB.\n"
            "• POCARI SWEAT branded hydration stations at key course checkpoints (Moore Junction & Kemta Junction).\n"
            "• Dedicated post-run Rehydration & Recovery Zone with chilled drink distribution.\n"
            "• Co-branded digital flyers, weekly training calendars, and email newsletters.\n"
            "• Minimum 3 dedicated Instagram Reels & TikTok recaps highlighting the hydration station.\n"
            "• High-resolution event photography and videography recap package featuring the brand."
        ),
        "brand_benefits": (
            "• Direct physical product sampling to 600+ active, health-conscious young professionals and runners.\n"
            "• Over 200,000+ digital impressions across BCRC and Archers Live social media channels.\n"
            "• Deep authentic brand equity by actively powering wellness and endurance in Ogun State.\n"
            "• Category exclusivity in the sports hydration and electrolyte beverage segment."
        ),
        "activations": (
            "• POCARI SWEAT Mile 5 Hydration Checkpoint (ice-cold rehydration cup hand-offs)\n"
            "• Finish-Line Rapid Recovery Lounge (hydration status testing & electrolyte replenishment)\n"
            "• 'Sweat & Replenish' social media photo opportunity with branded props\n"
            "• Branded hydration bibs or water bottles for VIP pacers"
        ),
        "value_amount": "₦1,500,000 Sponsorship + 1,200 Chilled Product Units",
        "partnership_tier": "Official Hydration Partner",
        "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6f/Pocari_Sweat_logo.png/330px-Pocari_Sweat_logo.png"
    },
    "red bull": {
        "canonical_name": "RED BULL",
        "parent_company": "Red Bull GmbH",
        "category": "Energy & Endurance Beverage",
        "description": "Red Bull is the world's leading energy drink, energizing athletic performance, urban culture, and high-intensity community experiences worldwide.",
        "proposed_role": "Official Energy & Performance Partner",
        "why_partner": "Red Bull's mission to give wings to human potential aligns directly with BEKSCITY RUN CLUB's Saturday morning tempo runs and marquee festivals. The brand's vibrant urban lifestyle appeal resonates strongly with our collegiate and young professional runner demographic in Abeokuta.",
        "requests_summary": (
            "• Product Support: Chilled Red Bull cans and sugar-free options for post-run energy boost.\n"
            "• Financial Sponsorship: Support toward high-energy sound truck, DJ stage, and finish-line arch.\n"
            "• Event Production: Red Bull sound equipment, DJ activation, and branded inflatable archway.\n"
            "• Athlete & Community Activation: Pacing prizes and DJ entertainment support."
        ),
        "deliverables": (
            "• Title recognition as Official Energy & Performance Partner.\n"
            "• Red Bull finish line DJ booth and celebration arena at Moore Junction.\n"
            "• Product sampling to runners during warm-up and post-run cool-down social.\n"
            "• Prominent logo integration across all digital flyers and race recaps.\n"
            "• Dedicated Red Bull 'Sprint King & Queen' challenge awards segment."
        ),
        "brand_benefits": (
            "• Direct trial among 600+ energetic young athletes, university students, and creatives.\n"
            "• 200k+ organic social video impressions featuring Red Bull energy activations.\n"
            "• Dominant youth lifestyle visibility in Abeokuta's premier fitness culture movement."
        ),
        "activations": (
            "• Red Bull Finish Line Energy Station & DJ Sound Deck\n"
            "• 'Wings for the Run' Pre-Run Warm-up Shot\n"
            "• Fastest Kilometer Sprint Segment Challenge"
        ),
        "value_amount": "₦2,000,000 Sponsorship + Sound Support & 800 Cans",
        "partnership_tier": "Official Energy & Performance Partner",
        "logo_url": "https://upload.wikimedia.org/wikipedia/en/thumb/f/f5/RedBullEnergyDrink.svg/300px-RedBullEnergyDrink.svg.png"
    },
    "nike": {
        "canonical_name": "NIKE",
        "parent_company": "Nike, Inc.",
        "category": "Athletic Footwear, Apparel & Equipment",
        "description": "Nike is the world's leading athletic footwear and apparel brand, dedicated to inspiring athletes worldwide and innovating athletic performance.",
        "proposed_role": "Official Footwear & Apparel Partner",
        "why_partner": "BEKSCITY RUN CLUB runners represent the future of grassroots running in West Africa. Partnering with Nike connects the brand directly with authentic everyday runners clocking weekly mileage on Abeokuta's hills and avenues.",
        "requests_summary": (
            "• Apparel Support: Official BCRC club singlets, technical tees, and pacer running caps.\n"
            "• Trial Experience: Shoe-trial fleet for community 5K and 7K PB time trials.\n"
            "• Financial Sponsorship: Logistics and community development fund."
        ),
        "deliverables": (
            "• Official Apparel Partner branding across all run photos, media kits, and video recaps.\n"
            "• Co-branded BCRC x Nike community technical singlets.\n"
            "• Shoe trial demo zone at starting terminal Moore Junction.\n"
            "• Pacer crew and co-founders fully outfitted in Nike running gear."
        ),
        "brand_benefits": (
            "• Authentic grassroots running credibility and everyday runner advocacy.\n"
            "• High-resolution photo and video assets of real runners in Nike footwear.\n"
            "• High-intent product trials leading directly to retail sales in Nigeria."
        ),
        "activations": (
            "• Nike Try-On & Run Shoe Demo Van\n"
            "• Pacer Pace Team Outfitting\n"
            "• Personal Best (PB) Milestone Awards"
        ),
        "value_amount": "Technical Kit Outfitting + ₦2,500,000 Sponsorship",
        "partnership_tier": "Official Footwear & Apparel Partner",
        "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a6/Logo_NIKE.svg/330px-Logo_NIKE.svg.png"
    }
}


def normalize_brand_name(input_name):
    """Normalizes brand typos and slang to canonical search terms."""
    clean = input_name.strip()
    low = clean.lower()
    
    # Common variations of Pocari Sweat
    if any(k in low for k in ["procari", "pocari", "pokari", "pocary", "pocarisweat"]):
        return "Pocari Sweat", "pocari"
    if "red bull" in low or "redbull" in low:
        return "Red Bull", "red bull"
    if "nike" in low:
        return "Nike", "nike"
    if "gatorade" in low:
        return "Gatorade", None
    if "power oil" in low or "poweroil" in low:
        return "Power Oil", None
    if "fearless" in low:
        return "Fearless Energy Drink", None
    if "milo" in low:
        return "Nestle Milo", None
    if "guinness" in low or "malta guinness" in low:
        return "Malta Guinness", None
    if "soakers" in low:
        return "Soakers", None
    if "archers" in low:
        return "Archers Live", None
        
    return clean, None


def query_wikipedia_online(search_term):
    """
    Queries Wikipedia API for brand summary, description, and logo.
    """
    try:
        # Step 1: Opensearch for best article match
        opensearch_url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={urllib.parse.quote(search_term)}&limit=3&namespace=0&format=json"
        req = urllib.request.Request(opensearch_url, headers={"User-Agent": "BekscityRunClub/2.0 (contact@bekscity.run)"})
        with urllib.request.urlopen(req, timeout=5) as res:
            data = json.loads(res.read().decode("utf-8"))
            titles = data[1] if len(data) > 1 else []
            if not titles:
                return None
            best_title = titles[0]

        # Step 2: Fetch article summary and thumbnail
        summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(best_title)}"
        req2 = urllib.request.Request(summary_url, headers={"User-Agent": "BekscityRunClub/2.0 (contact@bekscity.run)"})
        with urllib.request.urlopen(req2, timeout=5) as res2:
            s_data = json.loads(res2.read().decode("utf-8"))
            return {
                "title": s_data.get("title", best_title),
                "description": s_data.get("description", ""),
                "extract": s_data.get("extract", ""),
                "thumbnail": s_data.get("thumbnail", {}).get("source")
            }
    except Exception as e:
        print(f"[BrandResearcher] Online query warning for '{search_term}': {e}")
        return None


def synthesize_partnership_strategy(brand_input, event_name=None):
    """
    Main entry point: researches brand online, builds partnership strategy,
    activations, and commercial deliverables matching the BCRC pitch deck.
    """
    clean_name, curated_key = normalize_brand_name(brand_input)

    # Check curated repository first for instant perfection
    if curated_key and curated_key in CURATED_BRANDS:
        brand_info = dict(CURATED_BRANDS[curated_key])
        if event_name:
            brand_info["event_name"] = event_name
        return brand_info

    # Query online Wikipedia intelligence
    online_data = query_wikipedia_online(clean_name)
    title = online_data["title"] if online_data else clean_name
    desc = online_data["description"] if online_data else "Consumer Brand"
    extract = online_data["extract"] if online_data else f"{clean_name} is a consumer lifestyle brand."
    thumb = online_data.get("thumbnail") if online_data else None

    # Infer category & proposed role from extract/description
    combined_text = f"{title} {desc} {extract}".lower()

    if any(w in combined_text for w in ["drink", "beverage", "hydration", "electrolyte", "water", "juice"]):
        if any(w in combined_text for w in ["energy", "caffeine", "stimulant"]):
            category = "Energy & Performance Beverage"
            proposed_role = "Official Energy & Performance Partner"
            tier = "Official Energy Partner"
            pitch_hook = f"Energize Abeokuta's premier urban running community with {title}'s iconic vitality."
            val_amount = "₦1,500,000 Sponsorship + 800 Product Units"
        else:
            category = "Hydration & Active Refreshment"
            proposed_role = "Official Hydration Partner"
            tier = "Official Hydration Partner"
            pitch_hook = f"Keep Abeokuta's runners refreshed and rehydrated across every kilometer with {title}."
            val_amount = "₦1,200,000 Sponsorship + 1,000 Beverage Units"
    elif any(w in combined_text for w in ["footwear", "shoe", "sneaker", "apparel", "clothing", "sportswear"]):
        category = "Athletic Footwear & Apparel"
        proposed_role = "Official Footwear & Apparel Partner"
        tier = "Headline Technical Kit Partner"
        pitch_hook = f"Equip Abeokuta's fastest runners with cutting-edge {title} performance wear."
        val_amount = "Pacer Technical Kits + ₦2,000,000 Sponsorship"
    elif any(w in combined_text for w in ["nutrition", "food", "cereal", "snack", "dairy", "bakery", "oil"]):
        category = "Healthy Nutrition & Recovery"
        proposed_role = "Official Nutrition & Breakfast Partner"
        tier = "Official Nutrition Partner"
        pitch_hook = f"Fuel post-run recovery and community breakfast social bonding with {title}."
        val_amount = "₦1,000,000 Sponsorship + Post-Run Refreshments"
    elif any(w in combined_text for w in ["telecom", "network", "bank", "financial", "fintech", "payment"]):
        category = "Digital Services & Lifestyle Enabler"
        proposed_role = "Official Technology & Payment Partner"
        tier = "Headline Experience Partner"
        pitch_hook = f"Connect and empower 1,000+ active health enthusiasts with {title}."
        val_amount = "₦2,500,000 Sponsorship + Community Grants"
    else:
        category = "Community Lifestyle & Wellness"
        proposed_role = "Official Brand Experience Partner"
        tier = "Strategic Experience Partner"
        pitch_hook = f"Create authentic grassroots brand engagement in Abeokuta with {title} x BEKSCITY RUN CLUB."
        val_amount = "₦1,200,000 Commercial Sponsorship"

    why_partner = (
        f"Partnering with {title} creates an authentic synergy with BEKSCITY RUN CLUB. "
        f"Our community of runners, fitness enthusiasts, and young professionals in Abeokuta "
        f"aligns naturally with {title}'s commitment to quality, movement, and wellness. "
        f"This partnership connects your brand directly with consumers in an active, experiential environment."
    )

    requests_summary = (
        f"• Product Support: Direct product supply of {title} for runners and event staff.\n"
        f"• Financial Sponsorship: Financial backing toward timing, logistics, and road safety.\n"
        f"• Brand Infrastructure: Branded station, feather flags, and finish-line presence.\n"
        f"• Multi-Event Road-map: Consideration for annual partnership across all 2026/2027 runs."
    )

    deliverables = (
        f"• Official recognition as {proposed_role} of BEKSCITY RUN CLUB.\n"
        f"• Dedicated {title} branding touchpoint and product sampling station at the venue.\n"
        f"• Minimum 3 dedicated Instagram Reels and social media shout-outs to our 200k+ audience.\n"
        f"• Prominent logo inclusion on all digital event flyers, race maps, and calendar exports.\n"
        f"• High-resolution recap photography and video package featuring brand engagement."
    )

    brand_benefits = (
        f"• Direct experiential sampling to 600+ active, health-conscious consumers in Abeokuta.\n"
        f"• Over 200,000+ views across Instagram and TikTok recap media.\n"
        f"• Authentic brand association with healthy living, fitness, and youth community culture.\n"
        f"• Category exclusivity within your commercial sector during the event."
    )

    activations = (
        f"• {title} Experience Zone (Sampling & runner engagement)\n"
        f"• Branded Finish-Line Celebration & Photo Booth\n"
        f"• Social Media Giveaway & Runner of the Day Prize"
    )

    return {
        "canonical_name": title.upper(),
        "parent_company": "",
        "category": category,
        "description": extract,
        "proposed_role": proposed_role,
        "why_partner": why_partner,
        "requests_summary": requests_summary,
        "deliverables": deliverables,
        "brand_benefits": brand_benefits,
        "activations": activations,
        "value_amount": val_amount,
        "partnership_tier": tier,
        "pitch_hook": pitch_hook,
        "logo_url": thumb or "",
        "event_name": event_name or "Run and Rumble"
    }

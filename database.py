"""
BEKSCITY RUN CLUB — Database Persistence Layer
Handles SQLite storage, schema initialization, duplicate prevention,
CRUD operations, and JSON backup/import/export.
"""

import sqlite3
import json
import os
import re
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bekscity.db")

VALID_CATEGORIES = [
    "Community Improvement",
    "Sponsor Run",
    "Monthly Signature Event",
    "Community Challenge"
]

VALID_STATUSES = [
    "PLANNING",
    "TBC",
    "CONFIRMED",
    "CANCELLED"
]

VALID_DISTRICTS = [
    "MILE DISTRICT",
    "PHARMAFIT DISTRICT",
    "PANSEKE DISTRICT",
    "PANSHEKE DISTRICT",
    "FUNAAB DISTRICT",
    "ALL DISTRICTS",
    "TBC",
    ""
]

COFOUNDERS_DEFAULT = [
    {"name": "Oladipupo Abdulazeez", "role": "Co-founder", "phone": "08101674646", "social": "jughead_x3"},
    {"name": "Shittu Oluwadamilare", "role": "Co-founder", "phone": "08168120117", "social": "sweetboycoal"},
    {"name": "Adebanjo Oluwatobiloba", "role": "Co-founder", "phone": "07069582118", "social": "tobenzin"}
]

DISTRICTS_DEFAULT = [
    {"name": "MILE DISTRICT", "spot": "Moore junction", "lead": "", "contact": ""},
    {"name": "PHARMAFIT DISTRICT", "spot": "Kemta junction", "lead": "", "contact": ""},
    {"name": "PANSEKE DISTRICT", "spot": "Skating ground, Panseke", "lead": "", "contact": ""},
    {"name": "FUNAAB DISTRICT", "spot": "Funaab gate", "lead": "", "contact": ""}
]


def get_connection(db_path=None):
    path = db_path or DB_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init_db(db_path=None):
    """Initializes the database schema and seeds initial data if missing."""
    conn = get_connection(db_path)
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                date TEXT NOT NULL,
                category TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'PLANNING',
                start_time TEXT NOT NULL DEFAULT '06:45',
                end_time TEXT NOT NULL DEFAULT '08:30',
                timezone TEXT NOT NULL DEFAULT 'Africa/Lagos',
                meeting_point TEXT,
                venue TEXT,
                district TEXT,
                sponsor TEXT,
                partners TEXT,
                event_lead TEXT,
                planned_activities TEXT,
                description TEXT,
                distance TEXT,
                route_stops TEXT,
                notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS club_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS itineraries (
                id TEXT PRIMARY KEY,
                event_id TEXT NOT NULL,
                title TEXT NOT NULL,
                date TEXT NOT NULL,
                lead_organizer TEXT,
                meeting_point TEXT,
                route_summary TEXT,
                distance TEXT,
                timeline TEXT NOT NULL,
                route_checkpoints TEXT,
                volunteer_roles TEXT,
                logistics_items TEXT,
                safety_plan TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS proposals (
                id TEXT PRIMARY KEY,
                brand_name TEXT NOT NULL,
                event_id TEXT,
                event_name TEXT,
                partnership_tier TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'DRAFT',
                value_amount TEXT,
                pitch_hook TEXT,
                deliverables TEXT,
                brand_benefits TEXT,
                contact_person TEXT,
                contact_email TEXT,
                contact_phone TEXT,
                notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        # Default settings
        default_settings = {
            "date_text_color": "#D9A441",
            "club_name": "BEKSCITY RUN CLUB",
            "club_tagline": "Run. Improve. Connect.",
            "default_timezone": "Africa/Lagos",
            "pdf_theme": "classic_gold"
        }

        now_iso = datetime.now().isoformat()
        for k, v in default_settings.items():
            conn.execute("""
                INSERT OR IGNORE INTO club_settings (key, value, updated_at)
                VALUES (?, ?, ?)
            """, (k, v, now_iso))

    seed_default_events(conn)
    seed_default_itineraries(conn)
    seed_default_proposals(conn)
    conn.close()


def generate_event_id(date_str, conn=None):
    """
    Generates a unique Event ID formatted like BCRC-YYYYMMDD-XX.
    """
    clean_date = date_str.replace("-", "")
    prefix = f"BCRC-{clean_date}-"
    
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    cursor = conn.cursor()
    cursor.execute("SELECT id FROM events WHERE id LIKE ? ORDER BY id DESC LIMIT 1", (f"{prefix}%",))
    row = cursor.fetchone()
    
    seq = 1
    if row:
        last_id = row["id"]
        parts = last_id.split("-")
        if len(parts) >= 3 and parts[-1].isdigit():
            seq = int(parts[-1]) + 1
            
    if close_conn:
        conn.close()
        
    return f"{prefix}{seq:02d}"


def seed_default_events(conn=None):
    """
    Seeds the six known confirmed event records specified for BEKSCITY RUN CLUB.
    Guarantees no duplicate events are created on startup or application reload.
    """
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    now_iso = datetime.now().isoformat()

    seed_records = [
        {
            "date": "2026-10-24",
            "name": "Run and Rumble",
            "category": "Monthly Signature Event",
            "status": "CONFIRMED",
            "start_time": "16:00",
            "end_time": "21:00",
            "timezone": "Africa/Lagos",
            "meeting_point": "Moore Junction",
            "venue": "Moore Junction",
            "district": "ALL DISTRICTS",
            "sponsor": "",
            "partners": "Archers Live; Game Experience",
            "event_lead": "Organising Committee",
            "planned_activities": "7 km run, three stops along the route, and post-run games.",
            "description": "Run and Rumble is a premier evening signature event. Runners take on an energetic 7 km route across the city with three dedicated hydration and regrouping stops. The run concludes with post-run competitive games, social bonding, music, and community celebrations from 4:00 PM to 9:00 PM.",
            "distance": "7 km",
            "route_stops": "3 stops along the route",
            "notes": "Evening schedule override: 4:00 PM to 9:00 PM. Traffic safety escorts & hydration stations confirmed at all three stops."
        },
        {
            "date": "2026-10-31",
            "name": "Social Run",
            "category": "Monthly Signature Event",
            "status": "CONFIRMED",
            "start_time": "06:45",
            "end_time": "08:30",
            "timezone": "Africa/Lagos",
            "meeting_point": "OOPL",
            "venue": "OOPL (Olusegun Obasanjo Presidential Library grounds)",
            "district": "ALL DISTRICTS",
            "sponsor": "Breakfast Club",
            "partners": "",
            "event_lead": "",
            "planned_activities": "Morning community run, recovery stretching, and breakfast social time.",
            "description": "Saturday morning social run gathering at OOPL. Run followed by breakfast and social bonding courtesy of the Breakfast Club.",
            "distance": "5 km",
            "route_stops": "Standard scenic loop",
            "notes": "Sponsor run collaboration with Breakfast Club providing morning refreshments."
        },
        {
            "date": "2026-11-07",
            "name": "Run and Splash",
            "category": "Monthly Signature Event",
            "status": "CONFIRMED",
            "start_time": "06:45",
            "end_time": "08:30",
            "timezone": "Africa/Lagos",
            "meeting_point": "TBC",
            "venue": "TBC",
            "district": "ALL DISTRICTS",
            "sponsor": "",
            "partners": "Soakers",
            "event_lead": "",
            "planned_activities": "High energy club run, hydration splash zones, and recovery drills.",
            "description": "Run and Splash in special collaboration with Soakers. An exhilarating group run with designated hydration checkpoints and post-run cool down activities.",
            "distance": "6 km",
            "route_stops": "2 water splash checkpoints",
            "notes": "Collaboration partner: Soakers."
        },
        {
            "date": "2026-11-14",
            "name": "Signature Run",
            "category": "Monthly Signature Event",
            "status": "CONFIRMED",
            "start_time": "06:45",
            "end_time": "08:30",
            "timezone": "Africa/Lagos",
            "meeting_point": "MKO Stadium",
            "venue": "MKO Stadium",
            "district": "ALL DISTRICTS",
            "sponsor": "",
            "partners": "",
            "event_lead": "",
            "planned_activities": "Track warm-up, pacing groups (Beginner, Intermediate, Fast), and cool-down stretch.",
            "description": "Flagship monthly signature run congregating at MKO Stadium. Pacing groups organized for all fitness levels to build running endurance and camaraderie.",
            "distance": "7.5 km",
            "route_stops": "Stadium perimeter & boulevard course",
            "notes": "Standard morning schedule (6:45 AM gather, 7:00 AM warm-up, 7:15 AM run)."
        },
        {
            "date": "2026-11-21",
            "name": "Hill Run",
            "category": "Community Challenge",
            "status": "CONFIRMED",
            "start_time": "06:45",
            "end_time": "08:30",
            "timezone": "Africa/Lagos",
            "meeting_point": "Kemta junction",
            "venue": "Kemta junction",
            "district": "PHARMAFIT DISTRICT",
            "sponsor": "",
            "partners": "",
            "event_lead": "Pharmafit District Coordinator",
            "planned_activities": "Elevation training, hill incline repeats, endurance conditioning, and buddy pacing.",
            "description": "Community challenge focusing on stamina, hill climbs, and mental toughness through the Pharmafit District hills. Buddy up with experienced runners to conquer the incline.",
            "distance": "8 km",
            "route_stops": "Hill crest checkpoint & summit regroup",
            "notes": "District flag run for PHARMAFIT DISTRICT starting at Kemta junction."
        },
        {
            "date": "2026-11-28",
            "name": "Social Day",
            "category": "Monthly Signature Event",
            "status": "CONFIRMED",
            "start_time": "06:45",
            "end_time": "08:30",
            "timezone": "Africa/Lagos",
            "meeting_point": "Fruit Oasis",
            "venue": "Fruit Oasis",
            "district": "ALL DISTRICTS",
            "sponsor": "",
            "partners": "",
            "event_lead": "",
            "planned_activities": "Easy recovery 5k jog, fresh fruit breakfast, healthy lifestyle talk, and community games.",
            "description": "Monthly social day celebrating runners' monthly achievements at Fruit Oasis. Easy recovery jog followed by healthy smoothies, fruit platters, music, and social bonding.",
            "distance": "5 km",
            "route_stops": "Scenic parkway route to Fruit Oasis",
            "notes": "Post-run social and nutrition celebration."
        }
    ]

    with conn:
        for rec in seed_records:
            cursor = conn.cursor()
            # Check duplicate by date and name
            cursor.execute(
                "SELECT id FROM events WHERE date = ? AND LOWER(name) = LOWER(?)",
                (rec["date"], rec["name"])
            )
            existing = cursor.fetchone()
            if not existing:
                event_id = generate_event_id(rec["date"], conn)
                cursor.execute("""
                    INSERT INTO events (
                        id, name, date, category, status, start_time, end_time, timezone,
                        meeting_point, venue, district, sponsor, partners, event_lead,
                        planned_activities, description, distance, route_stops, notes,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event_id,
                    rec["name"],
                    rec["date"],
                    rec["category"],
                    rec["status"],
                    rec["start_time"],
                    rec["end_time"],
                    rec["timezone"],
                    rec["meeting_point"],
                    rec["venue"],
                    rec["district"],
                    rec["sponsor"],
                    rec["partners"],
                    rec["event_lead"],
                    rec["planned_activities"],
                    rec["description"],
                    rec["distance"],
                    rec["route_stops"],
                    rec["notes"],
                    now_iso,
                    now_iso
                ))

    if close_conn:
        conn.close()


def row_to_dict(row):
    if row is None:
        return None
    d = dict(row)
    return d


def get_all_events(status=None, category=None, district=None, month=None, search=None, conn=None):
    """
    Returns filtered event records ordered chronologically by date and start_time.
    """
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    query = "SELECT * FROM events WHERE 1=1"
    params = []

    if status:
        query += " AND UPPER(status) = UPPER(?)"
        params.append(status)

    if category:
        query += " AND category = ?"
        params.append(category)

    if district:
        query += " AND (district = ? OR district = 'ALL DISTRICTS')"
        params.append(district)

    if month:
        # month formatted as YYYY-MM
        query += " AND date LIKE ?"
        params.append(f"{month}%")

    if search:
        query += " AND (name LIKE ? OR description LIKE ? OR planned_activities LIKE ? OR meeting_point LIKE ? OR venue LIKE ? OR sponsor LIKE ? OR partners LIKE ?)"
        s = f"%{search}%"
        params.extend([s, s, s, s, s, s, s])

    query += " ORDER BY date ASC, start_time ASC"

    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    results = [row_to_dict(r) for r in rows]

    if close_conn:
        conn.close()

    return results


def get_event_by_id(event_id, conn=None):
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM events WHERE id = ?", (event_id,))
    row = cursor.fetchone()
    result = row_to_dict(row)

    if close_conn:
        conn.close()

    return result


def create_event(data, conn=None):
    """
    Creates a new event with auto-generated Event ID and timestamps.
    """
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    now_iso = datetime.now().isoformat()
    date_val = data.get("date", datetime.now().strftime("%Y-%m-%d")).strip()
    event_id = data.get("id") or generate_event_id(date_val, conn)

    # Standard default times if blank
    start_time = data.get("start_time") or "06:45"
    end_time = data.get("end_time") or "08:30"
    timezone = data.get("timezone") or "Africa/Lagos"

    category = data.get("category") or "Community Improvement"
    if category not in VALID_CATEGORIES:
        # Default or fallback
        category = "Monthly Signature Event"

    status = (data.get("status") or "PLANNING").upper()
    if status not in VALID_STATUSES:
        status = "PLANNING"

    with conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO events (
                id, name, date, category, status, start_time, end_time, timezone,
                meeting_point, venue, district, sponsor, partners, event_lead,
                planned_activities, description, distance, route_stops, notes,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event_id,
            data.get("name", "Untitled Run").strip(),
            date_val,
            category,
            status,
            start_time.strip(),
            end_time.strip(),
            timezone.strip(),
            (data.get("meeting_point") or "").strip(),
            (data.get("venue") or "").strip(),
            (data.get("district") or "").strip(),
            (data.get("sponsor") or "").strip(),
            (data.get("partners") or "").strip(),
            (data.get("event_lead") or "").strip(),
            (data.get("planned_activities") or "").strip(),
            (data.get("description") or "").strip(),
            (data.get("distance") or "").strip(),
            (data.get("route_stops") or "").strip(),
            (data.get("notes") or "").strip(),
            now_iso,
            now_iso
        ))

    event = get_event_by_id(event_id, conn)

    if close_conn:
        conn.close()

    return event


def update_event(event_id, data, conn=None):
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    now_iso = datetime.now().isoformat()
    existing = get_event_by_id(event_id, conn)
    if not existing:
        if close_conn:
            conn.close()
        return None

    name = data.get("name", existing["name"]).strip()
    date_val = data.get("date", existing["date"]).strip()
    category = data.get("category", existing["category"]).strip()
    status = (data.get("status", existing["status"])).strip().upper()
    start_time = data.get("start_time", existing["start_time"]).strip()
    end_time = data.get("end_time", existing["end_time"]).strip()
    timezone = data.get("timezone", existing["timezone"]).strip()
    meeting_point = data.get("meeting_point", existing["meeting_point"] or "").strip()
    venue = data.get("venue", existing["venue"] or "").strip()
    district = data.get("district", existing["district"] or "").strip()
    sponsor = data.get("sponsor", existing["sponsor"] or "").strip()
    partners = data.get("partners", existing["partners"] or "").strip()
    event_lead = data.get("event_lead", existing["event_lead"] or "").strip()
    planned_activities = data.get("planned_activities", existing["planned_activities"] or "").strip()
    description = data.get("description", existing["description"] or "").strip()
    distance = data.get("distance", existing["distance"] or "").strip()
    route_stops = data.get("route_stops", existing["route_stops"] or "").strip()
    notes = data.get("notes", existing["notes"] or "").strip()

    with conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE events SET
                name = ?, date = ?, category = ?, status = ?, start_time = ?, end_time = ?,
                timezone = ?, meeting_point = ?, venue = ?, district = ?, sponsor = ?,
                partners = ?, event_lead = ?, planned_activities = ?, description = ?,
                distance = ?, route_stops = ?, notes = ?, updated_at = ?
            WHERE id = ?
        """, (
            name, date_val, category, status, start_time, end_time, timezone,
            meeting_point, venue, district, sponsor, partners, event_lead,
            planned_activities, description, distance, route_stops, notes,
            now_iso, event_id
        ))

    updated = get_event_by_id(event_id, conn)
    if close_conn:
        conn.close()

    return updated


def duplicate_event(event_id, conn=None):
    """
    Duplicates an existing event with a new ID, setting status to PLANNING.
    """
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    existing = get_event_by_id(event_id, conn)
    if not existing:
        if close_conn:
            conn.close()
        return None

    new_data = dict(existing)
    new_data["name"] = f"{existing['name']} (Copy)"
    new_data["status"] = "PLANNING"
    new_data.pop("id", None)
    new_data.pop("created_at", None)
    new_data.pop("updated_at", None)

    created = create_event(new_data, conn)
    if close_conn:
        conn.close()
    return created


def delete_event(event_id, conn=None):
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    with conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM events WHERE id = ?", (event_id,))
        count = cursor.rowcount

    if close_conn:
        conn.close()

    return count > 0


def update_event_status(event_id, new_status, conn=None):
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    status_clean = new_status.upper().strip()
    now_iso = datetime.now().isoformat()

    with conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE events SET status = ?, updated_at = ? WHERE id = ?", (status_clean, now_iso, event_id))
        count = cursor.rowcount

    updated = get_event_by_id(event_id, conn)
    if close_conn:
        conn.close()
    return updated


def get_stats(conn=None):
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN UPPER(status) = 'CONFIRMED' THEN 1 ELSE 0 END) as confirmed,
            SUM(CASE WHEN UPPER(status) = 'PLANNING' THEN 1 ELSE 0 END) as planning,
            SUM(CASE WHEN UPPER(status) = 'TBC' THEN 1 ELSE 0 END) as tbc,
            SUM(CASE WHEN UPPER(status) = 'CANCELLED' THEN 1 ELSE 0 END) as cancelled
        FROM events
    """)
    row = cursor.fetchone()
    
    # Next upcoming confirmed event
    today_str = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("""
        SELECT * FROM events
        WHERE UPPER(status) = 'CONFIRMED' AND date >= ?
        ORDER BY date ASC, start_time ASC
        LIMIT 1
    """, (today_str,))
    next_event_row = cursor.fetchone()

    stats = {
        "total": row["total"] or 0,
        "confirmed": row["confirmed"] or 0,
        "planning": row["planning"] or 0,
        "tbc": row["tbc"] or 0,
        "cancelled": row["cancelled"] or 0,
        "next_event": row_to_dict(next_event_row)
    }

    if close_conn:
        conn.close()

    return stats


def get_setting(key, default=None, conn=None):
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    cursor = conn.cursor()
    cursor.execute("SELECT value FROM club_settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    val = row["value"] if row else default

    if close_conn:
        conn.close()
    return val


def set_setting(key, value, conn=None):
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    now_iso = datetime.now().isoformat()
    with conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO club_settings (key, value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
        """, (key, str(value), now_iso))

    if close_conn:
        conn.close()
    return value


def export_events_json(conn=None):
    """
    Exports all events and settings as a clean, serializable JSON dictionary.
    """
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    events = get_all_events(conn=conn)
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM club_settings")
    settings = {r["key"]: r["value"] for r in cursor.fetchall()}

    backup_data = {
        "version": "1.0",
        "exported_at": datetime.now().isoformat(),
        "club": "BEKSCITY RUN CLUB",
        "settings": settings,
        "events": events
    }

    if close_conn:
        conn.close()

    return backup_data


def import_events_json(backup_data, mode="merge", conn=None):
    """
    Imports events from a JSON backup.
    mode='merge': updates existing events by ID and adds new ones.
    mode='replace': clears current events and replaces with the backup.
    """
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    events = backup_data.get("events", [])
    now_iso = datetime.now().isoformat()

    with conn:
        cursor = conn.cursor()
        if mode == "replace":
            cursor.execute("DELETE FROM events")

        for ev in events:
            ev_id = ev.get("id") or generate_event_id(ev.get("date", "2026-01-01"), conn)
            cursor.execute("""
                INSERT INTO events (
                    id, name, date, category, status, start_time, end_time, timezone,
                    meeting_point, venue, district, sponsor, partners, event_lead,
                    planned_activities, description, distance, route_stops, notes,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    date = excluded.date,
                    category = excluded.category,
                    status = excluded.status,
                    start_time = excluded.start_time,
                    end_time = excluded.end_time,
                    timezone = excluded.timezone,
                    meeting_point = excluded.meeting_point,
                    venue = excluded.venue,
                    district = excluded.district,
                    sponsor = excluded.sponsor,
                    partners = excluded.partners,
                    event_lead = excluded.event_lead,
                    planned_activities = excluded.planned_activities,
                    description = excluded.description,
                    distance = excluded.distance,
                    route_stops = excluded.route_stops,
                    notes = excluded.notes,
                    updated_at = excluded.updated_at
            """, (
                ev_id,
                ev.get("name", "Untitled Run"),
                ev.get("date"),
                ev.get("category", "Monthly Signature Event"),
                ev.get("status", "PLANNING"),
                ev.get("start_time", "06:45"),
                ev.get("end_time", "08:30"),
                ev.get("timezone", "Africa/Lagos"),
                ev.get("meeting_point", ""),
                ev.get("venue", ""),
                ev.get("district", ""),
                ev.get("sponsor", ""),
                ev.get("partners", ""),
                ev.get("event_lead", ""),
                ev.get("planned_activities", ""),
                ev.get("description", ""),
                ev.get("distance", ""),
                ev.get("route_stops", ""),
                ev.get("notes", ""),
                ev.get("created_at", now_iso),
                now_iso
            ))

        if "settings" in backup_data and isinstance(backup_data["settings"], dict):
            for k, v in backup_data["settings"].items():
                set_setting(k, v, conn=conn)

    if close_conn:
        conn.close()

    return len(events)


def parse_json_safely(val, default):
    if not val:
        return default
    if isinstance(val, (list, dict)):
        return val
    try:
        return json.loads(val)
    except Exception:
        return default


def seed_default_itineraries(conn=None):
    """
    Seeds default operational run sheets/itineraries for marquee BCRC events.
    """
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    now_iso = datetime.now().isoformat()
    cursor = conn.cursor()

    # Find event ID for Run and Rumble (2026-10-24)
    cursor.execute("SELECT id FROM events WHERE date = '2026-10-24' LIMIT 1")
    ev1 = cursor.fetchone()
    ev1_id = ev1["id"] if ev1 else "BCRC-20261024-01"

    cursor.execute("SELECT id FROM events WHERE date = '2026-10-31' LIMIT 1")
    ev2 = cursor.fetchone()
    ev2_id = ev2["id"] if ev2 else "BCRC-20261031-01"

    itineraries_seed = [
        {
            "id": "ITIN-20261024-01",
            "event_id": ev1_id,
            "title": "Run and Rumble Official Run Sheet & Operations Itinerary",
            "date": "2026-10-24",
            "lead_organizer": "Oladipupo Abdulazeez (08101674646)",
            "meeting_point": "Moore Junction, Mile District",
            "route_summary": "Moore Junction -> Ibara Roundabout -> Panseke Skating Ground -> Kemta Junction -> Moore Junction",
            "distance": "7 km",
            "timeline": json.dumps([
                {"time": "15:30", "activity": "Marshals & Pacing Crew Arrival & Radio Check", "location": "Moore Junction", "lead": "Adebanjo O."},
                {"time": "16:00", "activity": "Runner Check-in, Bib collection & Audio Setup", "location": "Moore Junction Hub", "lead": "Secretariat"},
                {"time": "16:30", "activity": "Dynamic Mobility & Warm-up Session", "location": "Main Stage / Moore", "lead": "Fitness Lead"},
                {"time": "16:45", "activity": "Safety Briefing, Route Protocol & District Calls", "location": "Starting Line", "lead": "Shittu O."},
                {"time": "17:00", "activity": "Run Gun-Start (7 km Group Waves)", "location": "Moore Junction Outbound", "lead": "Pacing Team"},
                {"time": "17:35", "activity": "Stop 1: Panseke Skating Ground (Hydration & Regroup)", "location": "Panseke Hub", "lead": "Hydration Crew A"},
                {"time": "18:10", "activity": "Stop 2: Kemta Junction / Pharmafit (Energy gels & Electrolytes)", "location": "Pharmafit Hub", "lead": "Hydration Crew B"},
                {"time": "18:40", "activity": "Stop 3: Ibara Underpass (Final regroup before sprint finish)", "location": "Ibara Hub", "lead": "Safety Marshals"},
                {"time": "19:15", "activity": "Finish Line Arrival & Medals / Hydration", "location": "Moore Junction Arena", "lead": "Volunteer Lead"},
                {"time": "19:30 - 21:00", "activity": "Run and Rumble Evening Games & Social Festival with Archers Live", "location": "Festival Grounds", "lead": "All Co-Founders"}
            ]),
            "route_checkpoints": json.dumps([
                {"name": "Start / Finish Gate", "location": "Moore Junction", "distance_mark": "0.0 km / 7.0 km", "notes": "Medical station, DJ booth, baggage drop"},
                {"name": "Checkpoint 1 - Water Station", "location": "Panseke Skating Ground", "distance_mark": "2.4 km", "notes": "Water pouches, trash collection baskets"},
                {"name": "Checkpoint 2 - Electrolyte Hub", "location": "Kemta Junction", "distance_mark": "4.8 km", "notes": "First aid kit, glucose, electrolyte mix"},
                {"name": "Checkpoint 3 - Regroup Point", "location": "Ibara Underpass", "distance_mark": "6.1 km", "notes": "Whistles, glow batons, high-vis marshals"}
            ]),
            "volunteer_roles": json.dumps([
                {"role": "Lead Cyclist / Pacer", "assignee": "Shittu Oluwadamilare (08168120117)", "contact": "08168120117", "duty": "Front convoy pace setter and route clearance"},
                {"role": "Sweeper & Rear Safety Escort", "assignee": "Oladipupo Abdulazeez (08101674646)", "contact": "08101674646", "duty": "Ensure no runner is left behind, emergency liaison"},
                {"role": "Hydration Lead", "assignee": "Adebanjo Oluwatobiloba (07069582118)", "contact": "07069582118", "duty": "Supply distribution across all 3 checkpoints"},
                {"role": "Event Logistics & Media", "assignee": "BCRC Media Crew", "contact": "@jughead_x3 / @sweetboycoal", "duty": "Photo, video coverage, sound setup"}
            ]),
            "logistics_items": json.dumps([
                "500 BCRC Hydration Water Pouches",
                "12 Traffic Cones & Safety Reflective Batons",
                "First Aid Bag & Cold Sprays",
                "2 Mega-phones for Safety Marshals",
                "PA Sound System & Generator for Finish Games",
                "Event Arch & Finish Banners"
            ]),
            "safety_plan": "All runners must wear reflective gear or high-vis club shirts. Emergency ambulance vehicle on standby along Ibara corridor. Sweep vehicle follows 50m behind final walking group. Emergency hotlines: 08101674646 / 08168120117."
        },
        {
            "id": "ITIN-20261031-01",
            "event_id": ev2_id,
            "title": "OOPL Morning Social Run & Breakfast Itinerary",
            "date": "2026-10-31",
            "lead_organizer": "Adebanjo Oluwatobiloba (07069582118)",
            "meeting_point": "OOPL (Olusegun Obasanjo Presidential Library grounds)",
            "route_summary": "OOPL Main Gate -> Presidential Boulevard -> Cultural Center Loop -> OOPL Amphitheater",
            "distance": "5 km",
            "timeline": json.dumps([
                {"time": "06:30", "activity": "Organisers and Breakfast Crew Setup", "location": "OOPL Grounds", "lead": "Breakfast Club & BCRC"},
                {"time": "06:45", "activity": "Runner Assembly & Sign-in", "location": "OOPL Gate 1", "lead": "Secretariat"},
                {"time": "07:00", "activity": "Warm-up & Joint Mobility Session", "location": "Courtyard", "lead": "Fitness Lead"},
                {"time": "07:15", "activity": "5 km Social Run Kickoff", "location": "OOPL Boulevard", "lead": "Pacers (6:00 / 7:00 / Walkers)"},
                {"time": "08:00", "activity": "Cool-down Stretches & Group Photo", "location": "OOPL Amphitheater", "lead": "Shittu O."},
                {"time": "08:15 - 09:30", "activity": "Breakfast Club Social, Networking & Smoothies", "location": "OOPL Garden", "lead": "Breakfast Club Sponsor"}
            ]),
            "route_checkpoints": json.dumps([
                {"name": "Start & Finish Hub", "location": "OOPL Gate 1", "distance_mark": "0.0 km / 5.0 km", "notes": "Registration desk & water dispenser"},
                {"name": "Turnaround Loop", "location": "Cultural Center Roundabout", "distance_mark": "2.5 km", "notes": "Marshal with water dispenser"}
            ]),
            "volunteer_roles": json.dumps([
                {"role": "Pace Coordinator", "assignee": "Oladipupo Abdulazeez", "contact": "08101674646", "duty": "Coordinate 3 pace groups (fast, steady, walk/jog)"},
                {"role": "Breakfast Liaison", "assignee": "Adebanjo Oluwatobiloba", "contact": "07069582118", "duty": "Coordinate catering setup with Breakfast Club sponsor"},
                {"role": "First Aid & Sweeper", "assignee": "Shittu Oluwadamilare", "contact": "08168120117", "duty": "Monitor course safety and provide hydration"}
            ]),
            "logistics_items": json.dumps([
                "Breakfast Club Catering Tables & Napkins",
                "Ice Chests & Chilled Water Dispenser",
                "Course Directional Arrows (10x)",
                "BCRC Welcome Banner",
                "First Aid Kit"
            ]),
            "safety_plan": "Protected route inside private OOPL grounds and boulevard. Low vehicular traffic. Marshals stationed at road intersections."
        }
    ]

    with conn:
        for it in itineraries_seed:
            cursor.execute("SELECT id FROM itineraries WHERE id = ?", (it["id"],))
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO itineraries (
                        id, event_id, title, date, lead_organizer, meeting_point,
                        route_summary, distance, timeline, route_checkpoints,
                        volunteer_roles, logistics_items, safety_plan,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    it["id"], it["event_id"], it["title"], it["date"],
                    it["lead_organizer"], it["meeting_point"], it["route_summary"],
                    it["distance"], it["timeline"], it["route_checkpoints"],
                    it["volunteer_roles"], it["logistics_items"], it["safety_plan"],
                    now_iso, now_iso
                ))

    if close_conn:
        conn.close()


def seed_default_proposals(conn=None):
    """
    Seeds default sponsorship & partnership proposals.
    """
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    now_iso = datetime.now().isoformat()
    cursor = conn.cursor()

    proposals_seed = [
        {
            "id": "PROP-2026-001",
            "brand_name": "Breakfast Club Africa",
            "event_id": "BCRC-20261031-01",
            "event_name": "Social Run & Breakfast Series",
            "partnership_tier": "Gold Nutrition Partner",
            "status": "ACCEPTED",
            "value_amount": "₦750,000 + In-Kind Refreshments",
            "pitch_hook": "Powering Abeokuta's premier urban running community with healthy morning nutrition and high-engagement brand activations.",
            "deliverables": "Exclusive post-run breakfast branding\nPop-up sampling station at OOPL\nLogo on digital event flyers and monthly calendar PDF\nDedicated social media feature reel and newsletter sponsor highlight\nOpportunity to offer discount coupons to 300+ active club members",
            "brand_benefits": "Direct access to health-conscious young professionals and sports enthusiasts\nHigh digital impressions across Instagram and WhatsApp channels\nPhysical experiential touchpoint with targeted demographics",
            "contact_person": "Kemi Adeleke (Head of Partnerships)",
            "contact_email": "partnerships@breakfastclub.ng",
            "contact_phone": "08031234567",
            "notes": "Confirmed sponsorship for October 31 Social Run. Deliverables reviewed and locked in."
        },
        {
            "id": "PROP-2026-002",
            "brand_name": "Archers Live Entertainment",
            "event_id": "BCRC-20261024-01",
            "event_name": "Run and Rumble Evening Festival",
            "partnership_tier": "Headline Experience Partner",
            "status": "ACCEPTED",
            "value_amount": "₦1,200,000 Joint Co-Promotion",
            "pitch_hook": "Merging fitness and nightlife: Bringing the ultimate interactive game experience and sound stage to the finish line of Run and Rumble.",
            "deliverables": "Co-branded event identity ('Run and Rumble powered by Archers Live')\nInteractive gaming arena setup at Moore Junction venue\nDJ equipment, sound system, lighting, and stage production\nInclusion in official calendar and press release",
            "brand_benefits": "Brand integration with Abeokuta's largest fitness-social event\n500+ live participants and spectators\nMassive viral user-generated content from event games",
            "contact_person": "Tunde Balogun (Creative Director)",
            "contact_email": "hello@archerslive.com",
            "contact_phone": "08099887766",
            "notes": "Signed agreement. Sound checks and stage logistics set for 3:00 PM on Oct 24."
        },
        {
            "id": "PROP-2026-003",
            "brand_name": "Soakers Hydration & Energy",
            "event_id": "BCRC-20261107-01",
            "event_name": "Run and Splash Water Festival",
            "partnership_tier": "Official Hydration Sponsor",
            "status": "UNDER_REVIEW",
            "value_amount": "₦500,000 + 1,000 Beverage Units",
            "pitch_hook": "Hydrate over 400 runners during the most refreshing community water run in Ogun State.",
            "deliverables": "Branded hydration stations at KM 2.5 and finish line\nProduct sampling to every finisher\nLogo placement on bibs and event banner\nSocial media shoutouts across Instagram (@bekscityrunclub)",
            "brand_benefits": "Zero-waste sampling opportunity\nAssociation with high-energy youth movement\nBrand loyalty among active runners",
            "contact_person": "Femi Sowande",
            "contact_email": "sponsorships@soakersenergy.com",
            "contact_phone": "08023456789",
            "notes": "Proposal pitch deck sent. Follow-up meeting scheduled with brand manager."
        }
    ]

    with conn:
        for pr in proposals_seed:
            cursor.execute("SELECT id FROM proposals WHERE id = ?", (pr["id"],))
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO proposals (
                        id, brand_name, event_id, event_name, partnership_tier,
                        status, value_amount, pitch_hook, deliverables,
                        brand_benefits, contact_person, contact_email,
                        contact_phone, notes, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    pr["id"], pr["brand_name"], pr["event_id"], pr["event_name"],
                    pr["partnership_tier"], pr["status"], pr["value_amount"],
                    pr["pitch_hook"], pr["deliverables"], pr["brand_benefits"],
                    pr["contact_person"], pr["contact_email"], pr["contact_phone"],
                    pr["notes"], now_iso, now_iso
                ))

    if close_conn:
        conn.close()


def get_all_itineraries(conn=None):
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM itineraries ORDER BY date ASC, created_at DESC")
    rows = cursor.fetchall()
    res = []
    for r in rows:
        d = dict(r)
        d["timeline"] = parse_json_safely(d.get("timeline"), [])
        d["route_checkpoints"] = parse_json_safely(d.get("route_checkpoints"), [])
        d["volunteer_roles"] = parse_json_safely(d.get("volunteer_roles"), [])
        d["logistics_items"] = parse_json_safely(d.get("logistics_items"), [])
        res.append(d)
    if close_conn:
        conn.close()
    return res


def get_itinerary_by_id(itin_id, conn=None):
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM itineraries WHERE id = ?", (itin_id,))
    row = cursor.fetchone()
    if not row:
        if close_conn:
            conn.close()
        return None
    d = dict(row)
    d["timeline"] = parse_json_safely(d.get("timeline"), [])
    d["route_checkpoints"] = parse_json_safely(d.get("route_checkpoints"), [])
    d["volunteer_roles"] = parse_json_safely(d.get("volunteer_roles"), [])
    d["logistics_items"] = parse_json_safely(d.get("logistics_items"), [])
    if close_conn:
        conn.close()
    return d


def get_itinerary_by_event_id(event_id, conn=None):
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM itineraries WHERE event_id = ? ORDER BY created_at DESC LIMIT 1", (event_id,))
    row = cursor.fetchone()
    if not row:
        if close_conn:
            conn.close()
        return None
    d = dict(row)
    d["timeline"] = parse_json_safely(d.get("timeline"), [])
    d["route_checkpoints"] = parse_json_safely(d.get("route_checkpoints"), [])
    d["volunteer_roles"] = parse_json_safely(d.get("volunteer_roles"), [])
    d["logistics_items"] = parse_json_safely(d.get("logistics_items"), [])
    if close_conn:
        conn.close()
    return d


def create_itinerary(data, conn=None):
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    now_iso = datetime.now().isoformat()
    itin_date = data.get("date", datetime.now().strftime("%Y-%m-%d"))
    clean_date = itin_date.replace("-", "")
    prefix = f"ITIN-{clean_date}-"

    cursor = conn.cursor()
    cursor.execute("SELECT id FROM itineraries WHERE id LIKE ? ORDER BY id DESC LIMIT 1", (f"{prefix}%",))
    row = cursor.fetchone()
    seq = 1
    if row:
        parts = row["id"].split("-")
        if len(parts) >= 3 and parts[-1].isdigit():
            seq = int(parts[-1]) + 1
    itin_id = data.get("id") or f"{prefix}{seq:02d}"

    def ensure_json(v):
        if isinstance(v, (list, dict)):
            return json.dumps(v)
        return str(v or "[]")

    timeline_val = ensure_json(data.get("timeline", []))
    checkpoints_val = ensure_json(data.get("route_checkpoints", []))
    volunteers_val = ensure_json(data.get("volunteer_roles", []))
    logistics_val = ensure_json(data.get("logistics_items", []))

    with conn:
        cursor.execute("""
            INSERT INTO itineraries (
                id, event_id, title, date, lead_organizer, meeting_point,
                route_summary, distance, timeline, route_checkpoints,
                volunteer_roles, logistics_items, safety_plan,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            itin_id,
            data.get("event_id", ""),
            data.get("title", "Event Run Sheet"),
            itin_date,
            data.get("lead_organizer", ""),
            data.get("meeting_point", ""),
            data.get("route_summary", ""),
            data.get("distance", ""),
            timeline_val,
            checkpoints_val,
            volunteers_val,
            logistics_val,
            data.get("safety_plan", ""),
            now_iso,
            now_iso
        ))

    created = get_itinerary_by_id(itin_id, conn=conn)
    if close_conn:
        conn.close()
    return created


def update_itinerary(itin_id, data, conn=None):
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    now_iso = datetime.now().isoformat()
    def ensure_json(v):
        if isinstance(v, (list, dict)):
            return json.dumps(v)
        return str(v or "[]")

    fields = []
    params = []
    for k in ["title", "date", "lead_organizer", "meeting_point", "route_summary", "distance", "safety_plan", "event_id"]:
        if k in data:
            fields.append(f"{k} = ?")
            params.append(data[k])
    for k in ["timeline", "route_checkpoints", "volunteer_roles", "logistics_items"]:
        if k in data:
            fields.append(f"{k} = ?")
            params.append(ensure_json(data[k]))

    if not fields:
        if close_conn:
            conn.close()
        return get_itinerary_by_id(itin_id)

    fields.append("updated_at = ?")
    params.append(now_iso)
    params.append(itin_id)

    with conn:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE itineraries SET {', '.join(fields)} WHERE id = ?", params)

    updated = get_itinerary_by_id(itin_id, conn=conn)
    if close_conn:
        conn.close()
    return updated


def delete_itinerary(itin_id, conn=None):
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True
    with conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM itineraries WHERE id = ?", (itin_id,))
        count = cursor.rowcount
    if close_conn:
        conn.close()
    return count > 0


def get_all_proposals(status=None, search=None, conn=None):
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    query = "SELECT * FROM proposals WHERE 1=1"
    params = []
    if status:
        query += " AND UPPER(status) = UPPER(?)"
        params.append(status)
    if search:
        s = f"%{search}%"
        query += " AND (brand_name LIKE ? OR event_name LIKE ? OR partnership_tier LIKE ? OR pitch_hook LIKE ?)"
        params.extend([s, s, s, s])

    query += " ORDER BY created_at DESC"
    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    res = [dict(r) for r in rows]
    if close_conn:
        conn.close()
    return res


def get_proposal_by_id(prop_id, conn=None):
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM proposals WHERE id = ?", (prop_id,))
    row = cursor.fetchone()
    if not row:
        if close_conn:
            conn.close()
        return None
    res = dict(row)
    if close_conn:
        conn.close()
    return res


def create_proposal(data, conn=None):
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    now_iso = datetime.now().isoformat()
    year = datetime.now().strftime("%Y")
    prefix = f"PROP-{year}-"

    cursor = conn.cursor()
    cursor.execute("SELECT id FROM proposals WHERE id LIKE ? ORDER BY id DESC LIMIT 1", (f"{prefix}%",))
    row = cursor.fetchone()
    seq = 1
    if row:
        parts = row["id"].split("-")
        if len(parts) >= 3 and parts[-1].isdigit():
            seq = int(parts[-1]) + 1
    prop_id = data.get("id") or f"{prefix}{seq:03d}"

    with conn:
        cursor.execute("""
            INSERT INTO proposals (
                id, brand_name, event_id, event_name, partnership_tier,
                status, value_amount, pitch_hook, deliverables,
                brand_benefits, contact_person, contact_email,
                contact_phone, notes, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            prop_id,
            data.get("brand_name", "Brand Partner"),
            data.get("event_id", ""),
            data.get("event_name", ""),
            data.get("partnership_tier", "Headline Sponsor"),
            data.get("status", "DRAFT").upper(),
            data.get("value_amount", ""),
            data.get("pitch_hook", ""),
            data.get("deliverables", ""),
            data.get("brand_benefits", ""),
            data.get("contact_person", ""),
            data.get("contact_email", ""),
            data.get("contact_phone", ""),
            data.get("notes", ""),
            now_iso,
            now_iso
        ))

    created = get_proposal_by_id(prop_id, conn=conn)
    if close_conn:
        conn.close()
    return created


def update_proposal(prop_id, data, conn=None):
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    now_iso = datetime.now().isoformat()
    valid_cols = [
        "brand_name", "event_id", "event_name", "partnership_tier",
        "status", "value_amount", "pitch_hook", "deliverables",
        "brand_benefits", "contact_person", "contact_email",
        "contact_phone", "notes"
    ]
    fields = []
    params = []
    for k in valid_cols:
        if k in data:
            fields.append(f"{k} = ?")
            val = data[k]
            if k == "status" and val:
                val = str(val).upper()
            params.append(val)

    if not fields:
        if close_conn:
            conn.close()
        return get_proposal_by_id(prop_id)

    fields.append("updated_at = ?")
    params.append(now_iso)
    params.append(prop_id)

    with conn:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE proposals SET {', '.join(fields)} WHERE id = ?", params)

    updated = get_proposal_by_id(prop_id, conn=conn)
    if close_conn:
        conn.close()
    return updated


def delete_proposal(prop_id, conn=None):
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True
    with conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM proposals WHERE id = ?", (prop_id,))
        count = cursor.rowcount
    if close_conn:
        conn.close()
    return count > 0


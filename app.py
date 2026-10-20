"""
BEKSCITY RUN CLUB — Event Manager Web Application Server
Provides RESTful APIs for event management, calendar generation,
PDF generation, JSON backup/restore, and interactive web dashboard.
"""

import os
import io
import json
import calendar
from datetime import datetime
from flask import (
    Flask, render_template, request, jsonify, send_file, Response, abort
)

from database import (
    init_db, get_all_events, get_event_by_id, create_event, update_event,
    duplicate_event, delete_event, update_event_status, get_stats,
    get_setting, set_setting, export_events_json, import_events_json,
    get_all_itineraries, get_itinerary_by_id, get_itinerary_by_event_id,
    create_itinerary, update_itinerary, delete_itinerary,
    get_all_proposals, get_proposal_by_id, create_proposal,
    update_proposal, delete_proposal,
    VALID_CATEGORIES, VALID_STATUSES, VALID_DISTRICTS
)
from ics_exporter import (
    generate_ics_calendar, generate_event_vevent, generate_google_calendar_url
)
from calendar_pdf import (
    build_calendar_pdf, validate_hex_color, DATE_TEXT_COLOR
)
from itinerary_pdf import build_itinerary_pdf
from proposal_pdf import build_proposal_pdf
import tempfile

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["JSON_SORT_KEYS"] = False

# Ensure DB is initialized
init_db()


@app.route("/")
def index():
    """Serves the main BEKSCITY RUN CLUB Event Manager dashboard."""
    return render_template("index.html")


# -----------------------------------------------------------------------------
# REST API: EVENTS CRUD & MANAGEMENT
# -----------------------------------------------------------------------------
@app.route("/api/events", methods=["GET"])
def api_get_events():
    status = request.args.get("status")
    category = request.args.get("category")
    district = request.args.get("district")
    month = request.args.get("month")
    search = request.args.get("search")

    events = get_all_events(
        status=status,
        category=category,
        district=district,
        month=month,
        search=search
    )

    # Attach computed Google Calendar URL for convenience
    for ev in events:
        ev["google_calendar_url"] = generate_google_calendar_url(ev)

    return jsonify({"success": True, "count": len(events), "events": events})


@app.route("/api/events/<event_id>", methods=["GET"])
def api_get_event(event_id):
    ev = get_event_by_id(event_id)
    if not ev:
        return jsonify({"success": False, "error": "Event not found"}), 404

    ev["google_calendar_url"] = generate_google_calendar_url(ev)
    return jsonify({"success": True, "event": ev})


@app.route("/api/events", methods=["POST"])
def api_create_event():
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"success": False, "error": "Invalid JSON payload"}), 400

    name = data.get("name", "").strip()
    date_val = data.get("date", "").strip()

    if not name:
        return jsonify({"success": False, "error": "Event name is required."}), 400
    if not date_val:
        return jsonify({"success": False, "error": "Event date is required."}), 400

    try:
        created = create_event(data)
        created["google_calendar_url"] = generate_google_calendar_url(created)
        return jsonify({"success": True, "event": created, "message": "Event created successfully."}), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/events/<event_id>", methods=["PUT"])
def api_update_event(event_id):
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"success": False, "error": "Invalid JSON payload"}), 400

    existing = get_event_by_id(event_id)
    if not existing:
        return jsonify({"success": False, "error": "Event not found."}), 404

    try:
        updated = update_event(event_id, data)
        updated["google_calendar_url"] = generate_google_calendar_url(updated)
        return jsonify({"success": True, "event": updated, "message": "Event saved permanently to database."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/events/<event_id>/duplicate", methods=["POST"])
def api_duplicate_event(event_id):
    cloned = duplicate_event(event_id)
    if not cloned:
        return jsonify({"success": False, "error": "Event not found to duplicate."}), 404

    cloned["google_calendar_url"] = generate_google_calendar_url(cloned)
    return jsonify({
        "success": True,
        "event": cloned,
        "message": f"Event duplicated successfully with ID {cloned['id']}."
    }), 201


@app.route("/api/events/<event_id>", methods=["DELETE"])
def api_delete_event(event_id):
    success = delete_event(event_id)
    if not success:
        return jsonify({"success": False, "error": "Event not found or could not be deleted."}), 404

    return jsonify({"success": True, "message": f"Event {event_id} deleted permanently."})


@app.route("/api/events/<event_id>/status", methods=["PATCH"])
def api_update_status(event_id):
    data = request.get_json(force=True, silent=True) or {}
    new_status = data.get("status", "").upper()

    if new_status not in VALID_STATUSES:
        return jsonify({
            "success": False,
            "error": f"Invalid status. Choose from: {', '.join(VALID_STATUSES)}"
        }), 400

    updated = update_event_status(event_id, new_status)
    if not updated:
        return jsonify({"success": False, "error": "Event not found."}), 404

    return jsonify({
        "success": True,
        "event": updated,
        "message": f"Status updated to {new_status} and saved."
    })


@app.route("/api/stats", methods=["GET"])
def api_stats():
    stats = get_stats()
    return jsonify({"success": True, "stats": stats})


# -----------------------------------------------------------------------------
# CALENDAR EXPORTS: .ICS & GOOGLE CALENDAR
# -----------------------------------------------------------------------------
@app.route("/api/calendar.ics", methods=["GET"])
def api_export_confirmed_ics():
    """
    Master .ics calendar feed containing all confirmed Saturday runs.
    """
    confirmed_events = get_all_events(status="CONFIRMED")
    ics_text = generate_ics_calendar(
        confirmed_events,
        calendar_name="BEKSCITY RUN CLUB — Confirmed Runs"
    )

    response = Response(ics_text, mimetype="text/calendar")
    response.headers["Content-Disposition"] = "attachment; filename=bekscity_confirmed_runs.ics"
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response


@app.route("/api/events/<event_id>/calendar.ics", methods=["GET"])
def api_export_single_ics(event_id):
    """
    Individual event .ics download with multiple reminders.
    """
    ev = get_event_by_id(event_id)
    if not ev:
        abort(404)

    ics_text = generate_ics_calendar([ev], calendar_name=f"BEKSCITY — {ev['name']}")
    safe_name = "".join([c if c.isalnum() else "_" for c in ev["name"]]).strip("_")

    response = Response(ics_text, mimetype="text/calendar")
    response.headers["Content-Disposition"] = f"attachment; filename=bekscity_{safe_name}.ics"
    return response


# -----------------------------------------------------------------------------
# PDF CALENDAR GENERATION (REPORTLAB)
# -----------------------------------------------------------------------------
@app.route("/api/calendar/pdf", methods=["GET"])
def api_generate_pdf():
    """
    Dynamically generates the official BEKSCITY RUN CLUB Calendar PDF from saved records.
    Query params:
      - year (int, default 2026)
      - month (int, default 10)
      - date_color (hex color, e.g. #D9A441)
      - category_accents (boolean, default false)
    """
    year = int(request.args.get("year", 2026))
    month_arg = request.args.get("month", "all")
    date_color = request.args.get("date_color") or get_setting("date_text_color", DATE_TEXT_COLOR)
    use_category_accents = request.args.get("category_accents", "false").lower() in ("true", "1")

    # Validate hex color
    try:
        validated_color = validate_hex_color(date_color, "date_color")
    except ValueError as ve:
        return jsonify({"success": False, "error": str(ve)}), 400

    month_val = None
    if month_arg and month_arg.lower() not in ("all", "quarter", ""):
        try:
            month_val = int(month_arg)
        except ValueError:
            month_val = None

    tmp_pdf_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "generated_pdfs")
    os.makedirs(tmp_pdf_dir, exist_ok=True)

    if month_val is None:
        filename = f"bekscity_run_club_calendar_Oct-Dec_{year}.pdf"
    else:
        filename = f"bekscity_run_club_calendar_{year}_{month_val:02d}.pdf"

    pdf_path = os.path.join(tmp_pdf_dir, filename)

    try:
        build_calendar_pdf(
            pdf_path,
            year=year,
            month=month_val,
            date_text_color_override=validated_color,
            use_category_accents=use_category_accents,
            include_cover_pages=True
        )
        return send_file(
            pdf_path,
            as_attachment=True,
            download_name=filename,
            mimetype="application/pdf"
        )
    except Exception as e:
        return jsonify({"success": False, "error": f"PDF Generation Error: {str(e)}"}), 500


# -----------------------------------------------------------------------------
# REST API: RUN ITINERARIES & OPERATIONS
# -----------------------------------------------------------------------------
@app.route("/api/itineraries", methods=["GET"])
def api_get_itineraries():
    event_id = request.args.get("event_id")
    if event_id:
        itin = get_itinerary_by_event_id(event_id)
        return jsonify({"success": True, "itineraries": [itin] if itin else []})
    itins = get_all_itineraries()
    return jsonify({"success": True, "count": len(itins), "itineraries": itins})


@app.route("/api/itineraries/<itin_id>", methods=["GET"])
def api_get_itinerary(itin_id):
    itin = get_itinerary_by_id(itin_id)
    if not itin:
        return jsonify({"success": False, "error": "Itinerary not found"}), 404
    return jsonify({"success": True, "itinerary": itin})


@app.route("/api/itineraries", methods=["POST"])
def api_create_itinerary():
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"success": False, "error": "Invalid JSON payload"}), 400
    if not data.get("title"):
        return jsonify({"success": False, "error": "Title is required"}), 400
    try:
        created = create_itinerary(data)
        return jsonify({"success": True, "itinerary": created, "message": "Itinerary created successfully."}), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/itineraries/<itin_id>", methods=["PUT"])
def api_update_itinerary(itin_id):
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"success": False, "error": "Invalid JSON payload"}), 400
    try:
        updated = update_itinerary(itin_id, data)
        if not updated:
            return jsonify({"success": False, "error": "Itinerary not found"}), 404
        return jsonify({"success": True, "itinerary": updated, "message": "Itinerary updated successfully."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/itineraries/<itin_id>", methods=["DELETE"])
def api_delete_itinerary(itin_id):
    deleted = delete_itinerary(itin_id)
    if not deleted:
        return jsonify({"success": False, "error": "Itinerary not found"}), 404
    return jsonify({"success": True, "message": f"Itinerary {itin_id} deleted successfully."})


@app.route("/api/itineraries/<itin_id>/pdf", methods=["GET"])
def api_download_itinerary_pdf(itin_id):
    itin = get_itinerary_by_id(itin_id)
    if not itin:
        return jsonify({"success": False, "error": "Itinerary not found"}), 404

    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    tmp_path = tmp.name
    tmp.close()

    try:
        build_itinerary_pdf(tmp_path, itin)
        filename = f"BCRC_Itinerary_{itin.get('date', 'run')}_{itin.get('id', 'sheet')}.pdf"
        return send_file(
            tmp_path,
            as_attachment=True,
            download_name=filename,
            mimetype="application/pdf"
        )
    except Exception as e:
        return jsonify({"success": False, "error": f"Itinerary PDF Error: {str(e)}"}), 500


# -----------------------------------------------------------------------------
# REST API: SPONSORSHIP & BRAND PROPOSALS
# -----------------------------------------------------------------------------
@app.route("/api/proposals", methods=["GET"])
def api_get_proposals():
    status = request.args.get("status")
    search = request.args.get("search")
    props = get_all_proposals(status=status, search=search)
    return jsonify({"success": True, "count": len(props), "proposals": props})


@app.route("/api/proposals/<prop_id>", methods=["GET"])
def api_get_proposal(prop_id):
    prop = get_proposal_by_id(prop_id)
    if not prop:
        return jsonify({"success": False, "error": "Proposal not found"}), 404
    return jsonify({"success": True, "proposal": prop})


@app.route("/api/proposals", methods=["POST"])
def api_create_proposal():
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"success": False, "error": "Invalid JSON payload"}), 400
    if not data.get("brand_name"):
        return jsonify({"success": False, "error": "Brand name is required"}), 400
    try:
        created = create_proposal(data)
        return jsonify({"success": True, "proposal": created, "message": "Proposal created successfully."}), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/proposals/<prop_id>", methods=["PUT"])
def api_update_proposal(prop_id):
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"success": False, "error": "Invalid JSON payload"}), 400
    try:
        updated = update_proposal(prop_id, data)
        if not updated:
            return jsonify({"success": False, "error": "Proposal not found"}), 404
        return jsonify({"success": True, "proposal": updated, "message": "Proposal updated successfully."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/proposals/<prop_id>", methods=["DELETE"])
def api_delete_proposal(prop_id):
    deleted = delete_proposal(prop_id)
    if not deleted:
        return jsonify({"success": False, "error": "Proposal not found"}), 404
    return jsonify({"success": True, "message": f"Proposal {prop_id} deleted successfully."})


@app.route("/api/proposals/<prop_id>/pdf", methods=["GET"])
def api_download_proposal_pdf(prop_id):
    prop = get_proposal_by_id(prop_id)
    if not prop:
        return jsonify({"success": False, "error": "Proposal not found"}), 404

    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    tmp_path = tmp.name
    tmp.close()

    try:
        build_proposal_pdf(tmp_path, prop)
        clean_brand = "".join(c for c in prop.get("brand_name", "Brand") if c.isalnum() or c in " _-").strip().replace(" ", "_")
        filename = f"BCRC_Proposal_{clean_brand}_{prop.get('id', 'deck')}.pdf"
        return send_file(
            tmp_path,
            as_attachment=True,
            download_name=filename,
            mimetype="application/pdf"
        )
    except Exception as e:
        return jsonify({"success": False, "error": f"Proposal PDF Error: {str(e)}"}), 500


# -----------------------------------------------------------------------------
# REST API: CLUB INFO & COMMAND CENTER
# -----------------------------------------------------------------------------
@app.route("/api/club-info", methods=["GET"])
def api_get_club_info():
    return jsonify({
        "success": True,
        "club_name": "BEKSCITY RUN CLUB",
        "tagline": "Run. Improve. Connect.",
        "co_founders": [
            {
                "name": "Oladipupo Abdulazeez",
                "phone": "08101674646",
                "handle": "jughead_x3",
                "instagram_link": "https://instagram.com/jughead_x3",
                "role": "Co-Founder & Route / Sweeper Operations Lead"
            },
            {
                "name": "Shittu Oluwadamilare",
                "phone": "08168120117",
                "handle": "sweetboycoal",
                "instagram_link": "https://instagram.com/sweetboycoal",
                "role": "Co-Founder & Logistics / Pacing Convoy Lead"
            },
            {
                "name": "Adebanjo Oluwatobiloba",
                "phone": "07069582118",
                "handle": "tobenzin",
                "instagram_link": "https://instagram.com/tobenzin",
                "role": "Co-Founder & Community / Hydration Lead"
            }
        ],
        "districts": [
            {
                "name": "Mile District",
                "meeting_point": "Moore junction",
                "description": "Historic central hub of Abeokuta; meeting point for premier signature events like Run and Rumble."
            },
            {
                "name": "Pharmafit District",
                "meeting_point": "Kemta junction",
                "description": "Hill terrain district focused on elevation conditioning, hill repeats, and endurance stamina."
            },
            {
                "name": "Panseke District",
                "meeting_point": "Skating ground, panseke/",
                "description": "Vibrant commercial and youth activity sector; high-energy regrouping and sprint checkpoints."
            },
            {
                "name": "Funaab District",
                "meeting_point": "Funaab gate",
                "description": "Collegiate gateway for long-distance tempo training and student athletic integration."
            }
        ]
    })


# -----------------------------------------------------------------------------
# SETTINGS & DATA BACKUP / RESTORE
# -----------------------------------------------------------------------------
@app.route("/api/settings", methods=["GET"])
def api_get_settings():
    return jsonify({
        "success": True,
        "settings": {
            "date_text_color": get_setting("date_text_color", DATE_TEXT_COLOR),
            "club_name": get_setting("club_name", "BEKSCITY RUN CLUB"),
            "club_tagline": get_setting("club_tagline", "Run. Improve. Connect."),
            "default_timezone": get_setting("default_timezone", "Africa/Lagos")
        }
    })


@app.route("/api/settings", methods=["POST"])
def api_update_settings():
    data = request.get_json(force=True, silent=True) or {}
    
    if "date_text_color" in data:
        try:
            val = validate_hex_color(data["date_text_color"])
            set_setting("date_text_color", val)
        except ValueError as ve:
            return jsonify({"success": False, "error": str(ve)}), 400

    for k in ["club_name", "club_tagline", "default_timezone"]:
        if k in data:
            set_setting(k, data[k])

    return jsonify({"success": True, "message": "Settings updated permanently."})


@app.route("/api/backup", methods=["GET"])
def api_backup():
    """Exports full database as a downloadable JSON file."""
    backup_data = export_events_json()
    now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"bekscity_backup_{now_str}.json"
    
    response = Response(
        json.dumps(backup_data, indent=2),
        mimetype="application/json"
    )
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    return response


@app.route("/api/restore", methods=["POST"])
def api_restore():
    """Imports events from a JSON payload or uploaded backup file."""
    if "file" in request.files:
        uploaded = request.files["file"]
        try:
            data = json.load(uploaded)
        except Exception as e:
            return jsonify({"success": False, "error": f"Invalid JSON file: {str(e)}"}), 400
    else:
        data = request.get_json(force=True, silent=True)

    if not data or "events" not in data:
        return jsonify({"success": False, "error": "Invalid backup data structure."}), 400

    mode = request.args.get("mode", "merge")
    imported_count = import_events_json(data, mode=mode)

    return jsonify({
        "success": True,
        "message": f"Successfully imported {imported_count} events (mode: {mode})."
    })


@app.route("/api/health")
def api_health():
    return jsonify({"status": "healthy", "service": "BEKSCITY RUN CLUB Event Manager"})


if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5050))
    print(f"Starting BEKSCITY RUN CLUB Event Manager on http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)

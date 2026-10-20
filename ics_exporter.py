"""
BEKSCITY RUN CLUB — Calendar Export Module (.ics & Google Calendar)
Compliant with RFC 5545 iCalendar specification.
Supports Africa/Lagos timezone, multiple reminders/alarms (1 day, 2 hours, 15 minutes),
and single or bulk event exports.
"""

import urllib.parse
from datetime import datetime
import re

VTIMEZONE_AFRICA_LAGOS = """BEGIN:VTIMEZONE
TZID:Africa/Lagos
LAST-MODIFIED:20260101T000000Z
TZURL:http://tzurl.org/zoneinfo-outlook/Africa/Lagos
X-LIC-LOCATION:Africa/Lagos
BEGIN:STANDARD
TZNAME:WAT
TZOFFSETFROM:+0100
TZOFFSETTO:+0100
DTSTART:19700101T000000
END:STANDARD
END:VTIMEZONE"""


def format_ics_datetime(date_str, time_str):
    """
    Given YYYY-MM-DD and HH:MM, returns formatted YYYYMMDDTHHMMSS.
    """
    clean_date = date_str.replace("-", "")
    
    # Handle time if format is 12-hour or contains AM/PM
    time_str = time_str.strip()
    if " " in time_str or "AM" in time_str.upper() or "PM" in time_str.upper():
        try:
            dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %I:%M %p")
            clean_time = dt.strftime("%H%M%S")
        except Exception:
            clean_time = "064500"
    else:
        parts = time_str.split(":")
        hh = int(parts[0]) if len(parts) > 0 and parts[0].isdigit() else 6
        mm = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 45
        clean_time = f"{hh:02d}{mm:02d}00"

    return f"{clean_date}T{clean_time}"


def format_utc_timestamp(dt=None):
    if dt is None:
        dt = datetime.utcnow()
    return dt.strftime("%Y%m%dT%H%M%SZ")


def escape_ics_text(text):
    if not text:
        return ""
    # RFC 5545 escaping
    t = text.replace("\\", "\\\\")
    t = t.replace(";", "\\;")
    t = t.replace(",", "\\,")
    t = t.replace("\r\n", "\\n").replace("\n", "\\n").replace("\r", "\\n")
    return t


def build_event_description(event):
    lines = []
    lines.append(f"BEKSCITY RUN CLUB — {event.get('name', 'Weekly Run')}")
    lines.append(f"Category: {event.get('category', 'Community Improvement')}")
    
    district = event.get('district') or 'ALL DISTRICTS'
    lines.append(f"District: {district}")
    
    if event.get('meeting_point'):
        lines.append(f"Meeting Point: {event.get('meeting_point')}")
    if event.get('venue') and event.get('venue') != event.get('meeting_point'):
        lines.append(f"Venue: {event.get('venue')}")
    if event.get('distance'):
        lines.append(f"Distance: {event.get('distance')}")
    if event.get('route_stops'):
        lines.append(f"Route Stops: {event.get('route_stops')}")
    if event.get('sponsor'):
        lines.append(f"Sponsor: {event.get('sponsor')}")
    if event.get('partners'):
        lines.append(f"Partners: {event.get('partners')}")
    if event.get('event_lead'):
        lines.append(f"Event Lead: {event.get('event_lead')}")
        
    lines.append("")
    if event.get('planned_activities'):
        lines.append("PLANNED ACTIVITIES:")
        lines.append(event.get('planned_activities'))
        lines.append("")

    if event.get('description'):
        lines.append("ABOUT THIS RUN:")
        lines.append(event.get('description'))
        lines.append("")

    # Standard Saturday schedule note
    if event.get('date') != "2026-10-24":
        lines.append("STANDARD SCHEDULE:")
        lines.append("• 06:45 AM — Check-in and gathering")
        lines.append("• 07:00 AM — Warm-up session")
        lines.append("• 07:15 AM — Group run departs")
        lines.append("• 08:15 AM — Cooldown & stretching")
        lines.append("• 08:30 AM — Refreshments & community social")
    else:
        lines.append("SPECIAL EVENING SCHEDULE:")
        lines.append("• 04:00 PM — Gathering & pre-run excitement at Moore Junction")
        lines.append("• 04:30 PM — Run and Rumble 7 km run (3 stops)")
        lines.append("• 06:30 PM — Post-run games, social bonding, and celebrations")
        lines.append("• 09:00 PM — Event close")

    lines.append("")
    lines.append("BEKSCITY RUN CLUB | Keep Moving Forward")
    return "\n".join(lines)


def generate_event_vevent(event):
    """
    Builds a single VEVENT string with multiple VALARM reminders.
    """
    dtstamp = format_utc_timestamp()
    dtstart = format_ics_datetime(event["date"], event.get("start_time", "06:45"))
    dtend = format_ics_datetime(event["date"], event.get("end_time", "08:30"))
    uid = f"{event.get('id', 'BCRC-EVENT')}@bekscity.run"
    summary = escape_ics_text(f"BEKSCITY Run: {event.get('name', 'Weekly Run')}")
    
    location_parts = []
    if event.get("meeting_point"):
        location_parts.append(event["meeting_point"])
    if event.get("venue") and event.get("venue") != event.get("meeting_point"):
        location_parts.append(event["venue"])
    if event.get("district") and event.get("district") != "ALL DISTRICTS":
        location_parts.append(event["district"])
    location_parts.append("Abeokuta, Ogun State, Nigeria")
    location = escape_ics_text(", ".join(location_parts))

    description = escape_ics_text(build_event_description(event))

    vevent = f"""BEGIN:VEVENT
UID:{uid}
DTSTAMP:{dtstamp}
DTSTART;TZID=Africa/Lagos:{dtstart}
DTEND;TZID=Africa/Lagos:{dtend}
SUMMARY:{summary}
LOCATION:{location}
DESCRIPTION:{description}
STATUS:CONFIRMED
CATEGORIES:{escape_ics_text(event.get('category', 'Running'))}
TRANSP:OPAQUE
SEQUENCE:0
BEGIN:VALARM
TRIGGER:-P1D
ACTION:DISPLAY
DESCRIPTION:Reminder: BEKSCITY Run '{summary}' is tomorrow!
END:VALARM
BEGIN:VALARM
TRIGGER:-PT2H
ACTION:DISPLAY
DESCRIPTION:Reminder: BEKSCITY Run '{summary}' starts in 2 hours!
END:VALARM
BEGIN:VALARM
TRIGGER:-PT15M
ACTION:DISPLAY
DESCRIPTION:Alert: BEKSCITY Run '{summary}' gathers in 15 minutes!
END:VALARM
END:VEVENT"""

    return vevent


def generate_ics_calendar(events, calendar_name="BEKSCITY RUN CLUB Confirmed Runs"):
    """
    Generates a full RFC 5545 .ics calendar content containing all given events.
    """
    vevents = [generate_event_vevent(ev) for ev in events]
    vevents_str = "\n".join(vevents)

    ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//BEKSCITY RUN CLUB//Event Calendar 2.0//EN
CALSCALE:GREGORIAN
METHOD:PUBLISH
X-WR-CALNAME:{calendar_name}
X-WR-TIMEZONE:Africa/Lagos
X-WR-CALDESC:Official confirmed Saturday runs and community fitness events for BEKSCITY RUN CLUB.
{VTIMEZONE_AFRICA_LAGOS}
{vevents_str}
END:VCALENDAR"""

    # Normalize line endings to RFC standard CRLF
    ics_lines = [line.strip("\r") for line in ics_content.split("\n")]
    return "\r\n".join(ics_lines) + "\r\n"


def generate_google_calendar_url(event):
    """
    Generates a direct Google Calendar 'Create Event' URL.
    Format: https://calendar.google.com/calendar/render?action=TEMPLATE&text=...&dates=YYYYMMDDTHHMMSSZ/YYYYMMDDTHHMMSSZ...
    Times in Africa/Lagos are UTC+1.
    """
    start_iso = format_ics_datetime(event["date"], event.get("start_time", "06:45"))
    end_iso = format_ics_datetime(event["date"], event.get("end_time", "08:30"))
    
    # Convert Africa/Lagos (UTC+1) to UTC for google calendar dates param
    # start_iso is YYYYMMDDTHHMMSS
    dt_s = datetime.strptime(start_iso, "%Y%m%dT%H%M%S")
    dt_e = datetime.strptime(end_iso, "%Y%m%dT%H%M%S")
    
    # Subtract 1 hour to get UTC
    import datetime as dt_module
    dt_s_utc = dt_s - dt_module.timedelta(hours=1)
    dt_e_utc = dt_e - dt_module.timedelta(hours=1)
    
    dates_param = f"{dt_s_utc.strftime('%Y%m%dT%H%M%SZ')}/{dt_e_utc.strftime('%Y%m%dT%H%M%SZ')}"

    title = f"BEKSCITY Run: {event.get('name', 'Saturday Run')}"
    
    location_parts = []
    if event.get("meeting_point"):
        location_parts.append(event["meeting_point"])
    if event.get("venue") and event.get("venue") != event.get("meeting_point"):
        location_parts.append(event["venue"])
    location_parts.append("Abeokuta, Nigeria")
    location = ", ".join(location_parts)

    details = build_event_description(event)

    params = {
        "action": "TEMPLATE",
        "text": title,
        "dates": dates_param,
        "details": details,
        "location": location,
        "ctz": "Africa/Lagos"
    }

    return "https://calendar.google.com/calendar/render?" + urllib.parse.urlencode(params)

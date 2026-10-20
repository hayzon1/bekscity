"""
BEKSCITY RUN CLUB — Comprehensive Test Suite
Validates database persistence, duplicate prevention, seed data,
RFC 5545 calendar export with reminders, and ReportLab PDF generation.
"""

import os
import sys
import tempfile
import unittest
from datetime import datetime

# Add project root to sys.path
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_DIR)

import database
import ics_exporter
import calendar_pdf


class TestBekscitySystem(unittest.TestCase):

    def setUp(self):
        # Create a fresh temporary database for testing
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.temp_db_fd)
        database.init_db(self.temp_db_path)

    def tearDown(self):
        if os.path.exists(self.temp_db_path):
            os.remove(self.temp_db_path)

    def test_seed_events_loaded_and_no_duplicates(self):
        """Verifies that the 6 confirmed events are seeded properly and duplicate seeding does not create extra events."""
        events = database.get_all_events(conn=database.get_connection(self.temp_db_path))
        self.assertEqual(len(events), 6, "Expected exactly 6 seed events.")

        # Re-run seeding
        conn = database.get_connection(self.temp_db_path)
        database.seed_default_events(conn)
        conn.close()

        events_after = database.get_all_events(conn=database.get_connection(self.temp_db_path))
        self.assertEqual(len(events_after), 6, "Seeding again should NOT create duplicate events.")

    def test_event_1_run_and_rumble_details(self):
        """Validates Event 1 (Run and Rumble) details per spec: 4:00 PM to 9:00 PM, 7km, 3 stops, Moore Junction."""
        conn = database.get_connection(self.temp_db_path)
        events = database.get_all_events(search="Run and Rumble", conn=conn)
        conn.close()

        self.assertEqual(len(events), 1)
        ev = events[0]
        self.assertEqual(ev["date"], "2026-10-24")
        self.assertEqual(ev["status"], "CONFIRMED")
        self.assertEqual(ev["start_time"], "16:00")
        self.assertEqual(ev["end_time"], "21:00")
        self.assertEqual(ev["meeting_point"], "Moore Junction")
        self.assertIn("Archers Live", ev["partners"])
        self.assertIn("7 km", ev["distance"])
        self.assertIn("3 stops", ev["route_stops"])

    def test_event_2_to_6_presence(self):
        """Validates Events 2 to 6 exist with confirmed statuses."""
        conn = database.get_connection(self.temp_db_path)
        
        # Event 2: Social Run (Oct 31, 2026, Breakfast Club)
        e2 = database.get_all_events(search="Social Run", conn=conn)
        self.assertTrue(len(e2) >= 1)
        self.assertEqual(e2[0]["date"], "2026-10-31")
        self.assertEqual(e2[0]["sponsor"], "Breakfast Club")

        # Event 3: Run and Splash (Nov 7, 2026, Soakers)
        e3 = database.get_all_events(search="Run and Splash", conn=conn)
        self.assertTrue(len(e3) >= 1)
        self.assertEqual(e3[0]["date"], "2026-11-07")
        self.assertIn("Soakers", e3[0]["partners"])

        # Event 4: Signature Run (Nov 14, 2026, MKO Stadium)
        e4 = database.get_all_events(search="Signature Run", conn=conn)
        self.assertTrue(len(e4) >= 1)
        self.assertEqual(e4[0]["date"], "2026-11-14")
        self.assertEqual(e4[0]["meeting_point"], "MKO Stadium")

        # Event 5: Hill Run (Nov 21, 2026, Pharmafit District)
        e5 = database.get_all_events(search="Hill Run", conn=conn)
        self.assertTrue(len(e5) >= 1)
        self.assertEqual(e5[0]["date"], "2026-11-21")
        self.assertEqual(e5[0]["district"], "PHARMAFIT DISTRICT")

        # Event 6: Social Day (Nov 28, 2026, Fruit Oasis)
        e6 = database.get_all_events(search="Social Day", conn=conn)
        self.assertTrue(len(e6) >= 1)
        self.assertEqual(e6[0]["date"], "2026-11-28")
        self.assertEqual(e6[0]["venue"], "Fruit Oasis")

        conn.close()

    def test_crud_and_persistence(self):
        """Tests creating, updating, duplicating, and deleting an event."""
        conn = database.get_connection(self.temp_db_path)

        new_ev_data = {
            "name": "Community PB Time Trial",
            "date": "2026-12-05",
            "category": "Community Improvement",
            "status": "PLANNING",
            "start_time": "06:45",
            "end_time": "08:30",
            "district": "MILE DISTRICT",
            "meeting_point": "Mile 2 Terminal",
            "planned_activities": "Pacing drills and 5K PB time trials.",
            "distance": "5 km"
        }

        created = database.create_event(new_ev_data, conn=conn)
        self.assertIsNotNone(created["id"])
        self.assertTrue(created["id"].startswith("BCRC-20261205-"))
        self.assertEqual(created["name"], "Community PB Time Trial")

        # Update event
        updated = database.update_event(created["id"], {"status": "CONFIRMED", "notes": "Route verified"}, conn=conn)
        self.assertEqual(updated["status"], "CONFIRMED")
        self.assertEqual(updated["notes"], "Route verified")

        # Duplicate event
        duplicated = database.duplicate_event(created["id"], conn=conn)
        self.assertNotEqual(duplicated["id"], created["id"])
        self.assertEqual(duplicated["status"], "PLANNING")
        self.assertIn("(Copy)", duplicated["name"])

        # Delete event
        deleted = database.delete_event(duplicated["id"], conn=conn)
        self.assertTrue(deleted)
        self.assertIsNone(database.get_event_by_id(duplicated["id"], conn=conn))

        conn.close()

    def test_ics_export_with_reminders_and_wat_timezone(self):
        """Validates that .ics calendar generation conforms to RFC 5545 and contains 3 VALARM triggers."""
        conn = database.get_connection(self.temp_db_path)
        events = database.get_all_events(conn=conn)
        conn.close()

        ics_content = ics_exporter.generate_ics_calendar(events)
        self.assertIn("BEGIN:VCALENDAR", ics_content)
        self.assertIn("TZID:Africa/Lagos", ics_content)
        self.assertIn("BEGIN:VEVENT", ics_content)
        
        # Verify multiple alarms
        self.assertIn("TRIGGER:-P1D", ics_content, "Missing 1-day reminder")
        self.assertIn("TRIGGER:-PT2H", ics_content, "Missing 2-hour reminder")
        self.assertIn("TRIGGER:-PT15M", ics_content, "Missing 15-minute reminder")

        # Verify Google Calendar URL generator
        gcal_url = ics_exporter.generate_google_calendar_url(events[0])
        self.assertTrue(gcal_url.startswith("https://calendar.google.com/calendar/render?"))
        self.assertIn("ctz=Africa%2FLagos", gcal_url)

    def test_date_text_color_validation(self):
        """Verifies DATE_TEXT_COLOR hex validation and error handling."""
        valid_colors = ["#D9A441", "#252525", "#287D58", "#fff", "#123456"]
        for c in valid_colors:
            val = calendar_pdf.validate_hex_color(c)
            self.assertTrue(val.startswith("#"))

        invalid_colors = ["red", "123456", "#ZZZZZZ", "", None, "#12"]
        for inv in invalid_colors:
            with self.assertRaises(ValueError):
                calendar_pdf.validate_hex_color(inv)

    def test_reportlab_pdf_generation(self):
        """Tests that the PDF calendar is dynamically generated without errors."""
        conn = database.get_connection(self.temp_db_path)
        events = database.get_all_events(month="2026-10", conn=conn)
        conn.close()

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_pdf_path = tmp.name

        try:
            pdf_result = calendar_pdf.build_calendar_pdf(
                tmp_pdf_path,
                events=events,
                year=2026,
                month=10,
                date_text_color_override="#D9A441"
            )
            self.assertTrue(os.path.exists(pdf_result))
            self.assertGreater(os.path.getsize(pdf_result), 1000, "PDF file is too small or empty.")
        finally:
            if os.path.exists(tmp_pdf_path):
                os.remove(tmp_pdf_path)

    def test_json_backup_and_restore(self):
        """Verifies that full JSON backup and restore round-trips correctly."""
        conn = database.get_connection(self.temp_db_path)
        backup = database.export_events_json(conn=conn)
        self.assertEqual(len(backup["events"]), 6)
        self.assertEqual(backup["club"], "BEKSCITY RUN CLUB")

        # Clear and restore in replace mode
        imported_count = database.import_events_json(backup, mode="replace", conn=conn)
        self.assertEqual(imported_count, 6)

        events_restored = database.get_all_events(conn=conn)
        self.assertEqual(len(events_restored), 6)
        conn.close()


if __name__ == "__main__":
    unittest.main()

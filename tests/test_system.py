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

    def test_cofounders_districts_and_clean_page2(self):
        """Verifies cofounder details, district meet-up points, and that Page 2 is free of unwanted boxes."""
        import pypdf
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_pdf_path = tmp.name

        try:
            conn = database.get_connection(self.temp_db_path)
            events = database.get_all_events(conn=conn)
            conn.close()

            calendar_pdf.build_calendar_pdf(tmp_pdf_path, events=events, include_cover_pages=True)
            reader = pypdf.PdfReader(tmp_pdf_path)
            
            # Check Page 1 annots (cofounders and districts)
            p1_annots = {}
            for a in reader.pages[0].get("/Annots") or []:
                obj = a.get_object()
                t = obj.get("/T")
                v = obj.get("/V")
                if t:
                    p1_annots[str(t)] = str(v)

            self.assertIn("Oladipupo Abdulazeez", p1_annots.get("cof1_name", ""))
            self.assertIn("08101674646", p1_annots.get("cof1_phone", ""))
            self.assertIn("jughead_x3", p1_annots.get("cof1_social", ""))
            self.assertIn("Shittu Oluwadamilare", p1_annots.get("cof2_name", ""))
            self.assertIn("08168120117", p1_annots.get("cof2_phone", ""))
            self.assertIn("sweetboycoal", p1_annots.get("cof2_social", ""))
            self.assertIn("Adebanjo Oluwatobiloba", p1_annots.get("cof3_name", ""))
            self.assertIn("07069582118", p1_annots.get("cof3_phone", ""))
            self.assertIn("tobenzin", p1_annots.get("cof3_social", ""))

            self.assertEqual(p1_annots.get("dist_0_spot"), "Moore junction")
            self.assertEqual(p1_annots.get("dist_1_spot"), "Kemta junction")
            self.assertEqual(p1_annots.get("dist_2_spot"), "Skating ground, Panseke")
            self.assertEqual(p1_annots.get("dist_3_spot"), "Funaab gate")

            # Check Page 2 clean content
            p2_text = reader.pages[1].extract_text()
            self.assertNotIn("CONFIRMING OR ADDING AN EVENT", p2_text)
            self.assertNotIn("MONTHS WITH FIVE SATURDAYS", p2_text)
            self.assertIn("COMMUNITY IMPROVEMENT", p2_text)
            self.assertIn("SPONSOR RUN", p2_text)
            self.assertIn("SIGNATURE EVENT", p2_text)
            self.assertIn("COMMUNITY CHALLENGE", p2_text)
        finally:
            if os.path.exists(tmp_pdf_path):
                os.remove(tmp_pdf_path)

    def test_itineraries_crud_and_pdf(self):
        """Validates itinerary storage, CRUD, and PDF generation."""
        import itinerary_pdf
        conn = database.get_connection(self.temp_db_path)
        
        # Test default seeded itineraries
        itins = database.get_all_itineraries(conn=conn)
        self.assertTrue(len(itins) >= 2)
        itin1 = database.get_itinerary_by_id("ITIN-20261024-01", conn=conn)
        self.assertIsNotNone(itin1)
        self.assertIn("Run and Rumble", itin1["title"])
        self.assertTrue(len(itin1["timeline"]) >= 5)
        self.assertIn("Moore Junction", itin1["meeting_point"])

        # Test creating new itinerary
        new_itin_data = {
            "title": "Abeokuta Sunrise 10K",
            "date": "2026-12-05",
            "lead_organizer": "Shittu Oluwadamilare",
            "meeting_point": "Skating ground, Panseke",
            "distance": "10 km",
            "route_summary": "Panseke -> Omida -> Ibara -> Panseke",
            "timeline": [{"time": "06:00", "activity": "Gather", "location": "Panseke", "lead": "Shittu O."}],
            "route_checkpoints": [{"name": "CP1", "distance_mark": "5.0 km", "notes": "Water station"}],
            "volunteer_roles": [{"role": "Pacer", "assignee": "Abdulazeez", "contact": "08101674646", "duty": "6:00/km"}],
            "logistics_items": ["Cones", "Water"],
            "safety_plan": "First aid on site"
        }
        created = database.create_itinerary(new_itin_data, conn=conn)
        self.assertIsNotNone(created)
        self.assertEqual(created["title"], "Abeokuta Sunrise 10K")
        self.assertEqual(len(created["timeline"]), 1)

        # Test updating itinerary
        updated = database.update_itinerary(created["id"], {"title": "Abeokuta Sunrise 12K", "distance": "12 km"}, conn=conn)
        self.assertEqual(updated["title"], "Abeokuta Sunrise 12K")
        self.assertEqual(updated["distance"], "12 km")

        # Test PDF build
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_pdf = tmp.name
        try:
            itinerary_pdf.build_itinerary_pdf(tmp_pdf, updated)
            self.assertTrue(os.path.exists(tmp_pdf))
            self.assertTrue(os.path.getsize(tmp_pdf) > 1000)
        finally:
            if os.path.exists(tmp_pdf):
                os.remove(tmp_pdf)

        # Test deleting itinerary
        deleted = database.delete_itinerary(created["id"], conn=conn)
        self.assertTrue(deleted)
        self.assertIsNone(database.get_itinerary_by_id(created["id"], conn=conn))
        conn.close()

    def test_proposals_crud_and_pdf(self):
        """Validates proposals pipeline, CRUD, and formal proposal PDF generation."""
        import proposal_pdf
        conn = database.get_connection(self.temp_db_path)

        # Test default seeded proposals
        props = database.get_all_proposals(conn=conn)
        self.assertTrue(len(props) >= 3)
        p1 = database.get_proposal_by_id("PROP-2026-001", conn=conn)
        self.assertIsNotNone(p1)
        self.assertEqual(p1["brand_name"], "Breakfast Club Africa")
        self.assertEqual(p1["status"], "ACCEPTED")

        # Test creating new proposal
        new_prop_data = {
            "brand_name": "Peak Milk Nigeria",
            "event_name": "Family Fun Run",
            "partnership_tier": "Nutrition Sponsor",
            "status": "DRAFT",
            "value_amount": "₦1,500,000",
            "pitch_hook": "Power your mornings with Peak Milk",
            "deliverables": "Sampling booth\nSocial media feature",
            "brand_benefits": "Direct family reach",
            "contact_person": "Grace Obi",
            "contact_email": "grace@peakmilk.ng",
            "contact_phone": "08012345678"
        }
        created = database.create_proposal(new_prop_data, conn=conn)
        self.assertIsNotNone(created)
        self.assertEqual(created["brand_name"], "Peak Milk Nigeria")
        self.assertEqual(created["status"], "DRAFT")

        # Test updating proposal status
        updated = database.update_proposal(created["id"], {"status": "SENT", "value_amount": "₦2,000,000"}, conn=conn)
        self.assertEqual(updated["status"], "SENT")
        self.assertEqual(updated["value_amount"], "₦2,000,000")

        # Test Proposal PDF build
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_pdf = tmp.name
        try:
            proposal_pdf.build_proposal_pdf(tmp_pdf, updated)
            self.assertTrue(os.path.exists(tmp_pdf))
            self.assertTrue(os.path.getsize(tmp_pdf) > 1000)
        finally:
            if os.path.exists(tmp_pdf):
                os.remove(tmp_pdf)

        # Test deleting proposal
        deleted = database.delete_proposal(created["id"], conn=conn)
        self.assertTrue(deleted)
        self.assertIsNone(database.get_proposal_by_id(created["id"], conn=conn))
        conn.close()

    def test_flask_handling_page_api_endpoints(self):
        """Tests the Flask REST API endpoints for handling page operations."""
        from app import app
        client = app.test_client()

        # 1. Club info
        res = client.get("/api/club-info")
        self.assertEqual(res.status_code, 200)
        info = res.get_json()
        self.assertEqual(len(info["co_founders"]), 3)
        self.assertEqual(info["co_founders"][0]["name"], "Oladipupo Abdulazeez")
        self.assertEqual(info["co_founders"][1]["name"], "Shittu Oluwadamilare")
        self.assertEqual(info["co_founders"][2]["name"], "Adebanjo Oluwatobiloba")
        self.assertEqual(len(info["districts"]), 4)

        # 2. Itineraries endpoints
        res = client.get("/api/itineraries")
        self.assertEqual(res.status_code, 200)
        itins = res.get_json()["itineraries"]
        self.assertTrue(len(itins) >= 1)
        first_itin_id = itins[0]["id"]

        pdf_res = client.get(f"/api/itineraries/{first_itin_id}/pdf")
        self.assertEqual(pdf_res.status_code, 200)
        self.assertEqual(pdf_res.mimetype, "application/pdf")
        self.assertTrue(len(pdf_res.data) > 1000)

        # 3. Proposals endpoints
        res = client.get("/api/proposals")
        self.assertEqual(res.status_code, 200)
        props = res.get_json()["proposals"]
        self.assertTrue(len(props) >= 1)
        first_prop_id = props[0]["id"]

        prop_pdf_res = client.get(f"/api/proposals/{first_prop_id}/pdf")
        self.assertEqual(prop_pdf_res.status_code, 200)
        self.assertEqual(prop_pdf_res.mimetype, "application/pdf")
        self.assertTrue(len(prop_pdf_res.data) > 1000)


if __name__ == "__main__":
    unittest.main()


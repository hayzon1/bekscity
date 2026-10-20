# BEKSCITY RUN CLUB — Calendar Management System

The **BEKSCITY RUN CLUB Calendar Management System** is a full-stack club operations and event scheduling platform. It provides persistent storage (SQLite), an interactive dashboard for managing weekly Saturday runs, automatic ReportLab PDF calendar generation, RFC 5545 `.ics` feeds with multiple alarms, and direct Google/Apple Calendar integrations.

---

## 🏃 Key Features

1. **Event Management Dashboard (`BEKSCITY RUN CLUB — EVENT MANAGER`)**:
   - Monthly calendar grid view with visual Saturday badges and fifth-Saturday planning opportunity alerts.
   - Comprehensive event list view filterable by Status, Category, District, and live text search.
   - Live counters for Confirmed Runs, Planning, Cancelled, and Total Events.
   - Full CRUD: Create, Edit, Save, Duplicate, Quick Confirm, Quick Cancel, and Delete.
   - Unsaved changes dirty state detection: alerts the user if navigating away before saving.

2. **Persistent Storage & Architecture**:
   - SQLite (`bekscity.db`) in WAL mode guarantees changes are never lost when the application is closed or restarted.
   - Changes made in the dashboard are the single source of truth; PDF generation is derived from the latest database state.
   - Seeded with the 6 confirmed events without duplicate creation on restarts.
   - Full JSON Backup & Restore capability.

3. **ReportLab Professional PDF Calendar Generator**:
   - Branded layout with BEKSCITY RUN CLUB identity, district administration, and operations checklist.
   - **`DATE_TEXT_COLOR = "#D9A441"`**: Top-level configurable setting accepting hex values (e.g. `#D9A441`, `#252525`, `#287D58`), with validation and clear error reporting.
   - Automatic text wrapping on all event descriptions, activities, and metadata.
   - Clickable Add to Calendar links inside the generated PDF.
   - Fillable interactive form fields for personal member notes.

4. **Add to Calendar & Integrations**:
   - One primary **Add All Confirmed Runs to Calendar** hero action.
   - Master `.ics` feed with RFC 5545 compliance and `Africa/Lagos` (WAT, UTC+1) timezone.
   - **Multiple Reminders**:
     - 5 days before (`-P5D`)
     - 3 days before (`-P3D`)
     - 7 hours before (`-PT7H`)
   - One-click Google Calendar URLs for individual runs.

5. **District Management & Club Operations**:
   - Four permanent districts: **MILE DISTRICT**, **PHARMAFIT DISTRICT**, **PANSHEKE DISTRICT**, and **FUNAAB DISTRICT**.
   - Standard Saturday Morning Schedule (6:45 AM Gathering, 7:00 AM Warm-up, 7:15 AM Run, 8:15 AM Cooldown, 8:30 AM Social).
   - Event-specific override support (e.g. *Run and Rumble* evening schedule: 4:00 PM – 9:00 PM).

---

## 🛠️ Project Structure

```
bekscity-run-club/
├── .venv/                      # Python virtual environment
├── bekscity.db                 # SQLite persistent database (WAL mode)
├── app.py                      # Flask application server & REST APIs
├── database.py                 # SQLite database schema, CRUD, seeds & migrations
├── calendar_pdf.py             # ReportLab PDF calendar generation engine
├── ics_exporter.py             # RFC 5545 iCalendar & Google Calendar exporter
├── templates/
│   └── index.html              # Responsive dashboard UI (Tailwind CSS)
├── tests/
│   └── test_system.py          # Comprehensive automated unit & integration test suite
├── requirements.txt            # Python dependencies
└── README.md                   # System documentation
```

---

## 🚀 Getting Started

### 1. Activate Environment & Run Application
```bash
cd /Users/mac/.gemini/antigravity/scratch/bekscity-run-club
.venv/bin/python app.py
```
Open your browser to: **`http://localhost:5050`**

### 2. Run Standalone PDF Generator
```bash
.venv/bin/python calendar_pdf.py
```

### 3. Run Automated Test Suite
```bash
.venv/bin/python tests/test_system.py
```

---

## ⚙️ Configuration

In `calendar_pdf.py`, configure the date text color at the top:
```python
DATE_TEXT_COLOR = "#D9A441"
```
Or customize it dynamically in the web UI via the **Download PDF Calendar** settings modal.

# 🏃 BEKSCITY RUN CLUB — Open Source Club Operating System

[![License: MIT](https://img.shields.io/badge/License-MIT-gold.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![Framework: Flask](https://img.shields.io/badge/Framework-Flask-black.svg)](https://flask.palletsprojects.com/)
[![PDF Engine: ReportLab](https://img.shields.io/badge/Engine-ReportLab-red.svg)](https://www.reportlab.com/)
[![Tests](https://img.shields.io/badge/Tests-18%20Passed-brightgreen.svg)]()

**BEKSCITY RUN CLUB OS** is an end-to-end event management, calendar publishing, and brand partnership operating system built for modern athletic communities and running clubs. 

Originally created for the **BEKSCITY RUN CLUB** (operating across 4 districts in Ogun State, Nigeria: Mile, Pharmafit, Panseke, and FUNAAB), this platform automates the operational pipeline of running clubs—from weekly Saturday run coordination and multi-alarm calendar subscriptions to publication-grade PDF itineraries, AI-assisted brand sponsorship pitch decks, and community directories.

---

## ⚡ Core Modules

### 1. 📅 Event Management Matrix
- **Interactive Calendar & Matrix View**: Complete monthly schedule view with Saturday badges, fifth-Saturday planning opportunity alerts, and instant CRUD operations.
- **District Multi-Tenant Operations**: Native support for district-level scheduling (Mile, Pharmafit, Panseke, FUNAAB) or unified all-district signature events.
- **Status Lifecycle Tracking**: Dynamic state transitions across `PLANNING`, `TBC`, `CONFIRMED`, and `CANCELLED`.
- **Zero-Data-Loss Architecture**: SQLite persistent storage in WAL (Write-Ahead Logging) mode with automatic table initialization and seed data on initial launch.

### 2. 📲 Multi-Alarm Calendar Feeds (`RFC 5545`)
- **Native iOS & Android Subscription**: Master `.ics` feed automatically hosted via GitHub Pages over HTTPS with correct `text/calendar` MIME type handling, bypassing mobile browser SSL / security certificate warnings.
- **3-Tier Smart Alarms**: Each confirmed event includes automated alerts:
  - 🔔 **5 Days Before** (`-P5D`) — Route prep & gear readiness.
  - 🔔 **3 Days Before** (`-P3D`) — District turnout reminder.
  - 🔔 **7 Hours Before** (`-PT7H`) — Morning race-day alarm (11:45 PM WAT Friday evening).
- **One-Click Google Calendar**: Pre-formatted, URL-encoded Google Calendar event generation with full route itineraries and meeting point coordinates.

### 3. 📄 Publication-Ready PDF Calendar Engine
- **ReportLab Vector Rendering**: Generates clean, high-resolution printable calendars for community distribution.
- **Dynamic Hex Color Theming**: Top-level configurable brand colors (`DATE_TEXT_COLOR = "#D9A441"`, supporting custom team palettes like `#287D58`, `#1E3A8A`, etc.).
- **Clickable Mobile Action Links**: Embedded vector links inside the PDF for one-tap calendar syncing on mobile devices.
- **Fillable Member Notes**: Interactive PDF form fields allowing athletes to type their target pace, notes, and milestones directly into the PDF.

### 4. 💼 Brand Sponsorship & Pitch Deck Studio
- **Automated Brand Research**: Fetches and standardizes brand identities, partner logos (Wikimedia / Wikipedia SVG & PNG APIs with transparent alpha conversion), and marketing highlights.
- **Multi-Format Deck Export**:
  - **Executive PDF Decks**: Branded ReportLab pitch decks complete with executive summaries, demographic reach, activation ideas, and commercial tiers.
  - **Editable PowerPoint (`.pptx`)**: Generates 16:9 widescreen presentation slides for co-founders to pitch corporate sponsors.
- **Redaction & Partner Privacy**: Intelligent redaction filters ensure sensitive sponsor assets and partner materials are protected.

### 5. 🗺️ District Itinerary & Safety Dispatches
- Detailed Saturday run timelines (Gathering, Warm-up, Step-off, Cooldown, Socializing).
- Water stop coordination, checkpoint logging, volunteer role assignments, and safety contingency plans.
- Downloadable single-event PDF dispatches ready for print or WhatsApp broadcast.

### 6. 👥 Community Directory & Outbound Dispatcher
- Member database segmented by residential district.
- Built-in SMTP email dispatch service for distributing newly published calendars and event updates directly to registered athletes.

---

## 🏗️ Architecture

```
bekscity-run-club/
├── app.py                      # Flask Application Server & REST APIs
├── database.py                 # SQLite WAL Layer, Schema Migrations & Auto-Seeds
├── calendar_pdf.py             # ReportLab Vector PDF Calendar Engine
├── itinerary_pdf.py            # Event Day Itinerary & Safety PDF Engine
├── proposal_pdf.py             # ReportLab Brand Sponsorship Pitch Deck Generator
├── proposal_pptx.py            # PowerPoint (.pptx) Widescreen Pitch Deck Generator
├── brand_researcher.py         # Brand Asset Retrieval & Image Preprocessing Engine
├── ics_exporter.py             # RFC 5545 iCalendar & Google Calendar Generator
├── email_service.py            # SMTP Dispatch Service for Member Broadcasts
├── templates/                  # Responsive Tailwind CSS Dashboards
├── tests/
│   └── test_system.py          # Comprehensive 18-Test Automated Test Suite
├── bekscity_saturdays_Oct-Dec.ics # Static master calendar feed for GitHub Pages
├── requirements.txt            # Production dependencies (Gunicorn, ReportLab, etc.)
└── LICENSE                     # MIT Open Source License
```

---

## 🚀 Quick Start (Local Development)

### Prerequisites
- Python 3.9, 3.10, 3.11, or 3.12
- Git

### 1. Clone & Set Up Environment
```bash
git clone https://github.com/hayzon1/bekscity.git
cd bekscity

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment (Optional)
```bash
cp .env.example .env
```
*(The system works out-of-the-box with zero configuration using SQLite defaults!)*

### 3. Launch Application
```bash
python app.py
```
Open **`http://localhost:5050`** in your browser.

### 4. Run Automated Tests
```bash
python -m unittest tests/test_system.py
```
*(All 18 system and integration tests run in under 12 seconds).*

---

## 🌐 Deploy to Render (Cloud Hosting)

Deploy the system as a 24/7 cloud service in 2 minutes:

1. Go to [Render Dashboard](https://dashboard.render.com/) and click **New +** > **Web Service**.
2. Connect your GitHub repository: `hayzon1/bekscity`.
3. Set the following settings:
   - **Name**: `bekscity-run-club`
   - **Region**: Closest to your users (e.g., Frankfurt or Oregon)
   - **Branch**: `feat/calendar-management-system` (or `main`)
   - **Root Directory**: *(Leave empty)*
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Instance Type**: Free
4. Click **Deploy Web Service**.

> [!NOTE]
> `app.py` automatically binds to Render's dynamic `$PORT` environment variable and host `0.0.0.0`.

---

## 🔒 Privacy & Open-Source Security

This repository is strictly configured to protect member privacy and confidential commercial discussions:
- **Zero Committed Databases**: `bekscity.db` and all SQLite journals (`*.db-wal`, `*.db-shm`) are excluded via `.gitignore`.
- **Zero Hardcoded Secrets**: Secrets and local `.env` files are ignored from version control.
- **Self-Seeding Engine**: When deployed on a fresh environment, `database.py` automatically initializes the schema and baseline templates without exposing any private club member contacts or unannounced sponsorship contracts.

---

## 🤝 Contributing

Contributions are warmly welcomed! To contribute:
1. Fork the repository.
2. Create a dedicated branch: `git checkout -b feat/your-improvement`.
3. Ensure all tests pass: `python -m unittest tests/test_system.py`.
4. Commit your changes: `git commit -m "Add descriptive feature summary"`.
5. Push to your branch and open a Pull Request.

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

Developed with ❤️ for **BEKSCITY RUN CLUB** and community runners everywhere.

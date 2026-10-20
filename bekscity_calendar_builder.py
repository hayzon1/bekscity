#!/usr/bin/env python3
"""
BEKSCITY RUN CLUB calendar builder
Setup once:   pip install reportlab pypdf
Run:          python bekscity_calendar_builder.py
Makes:        bekscity_run_club_calendar_Oct-Dec_2026.pdf   (interactive, fillable, wrapped text)
              bekscity_saturdays_Oct-Dec.ics                (master file, CONFIRMED events only, 30-min reminders)
              individual_events/<date>_<name>.ics           (one file per CONFIRMED event)

HOW TO REUSE
1. Add or change events in the Event Manager dashboard at http://localhost:5050 (or in the SQLite database).
   An event only gets an ADD TO CALENDAR link, a Google Calendar link and an .ics entry when its
   status is "Confirmed".
2. Run this script to generate all PDF, Master .ICS, and individual .ICS files.
3. Everything is regenerated synchronously from the persistent database!
"""

import sys
import os

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from calendar_pdf import generate_all_outputs

if __name__ == "__main__":
    generate_all_outputs()

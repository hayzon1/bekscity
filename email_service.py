"""
BEKSCITY RUN CLUB — Community Email Dispatch Service
Handles assembling and sending official Run Calendar PDFs to community members
via SMTP or simulated dispatch with full audit tracking.
"""

import os
import smtplib
import mimetypes
from email.message import EmailMessage
from datetime import datetime
from database import (
    get_setting,
    get_connection,
    record_email_dispatch,
    get_community_members,
    COFOUNDERS_DEFAULT,
    DISTRICTS_DEFAULT
)

HERE = os.path.dirname(os.path.abspath(__file__))
DISPATCH_PREVIEW_DIR = os.path.join(HERE, "email_dispatches")


def get_smtp_config():
    """Retrieves current SMTP server configuration from club_settings or env."""
    return {
        "host": get_setting("smtp_host", os.environ.get("BCRC_SMTP_HOST", "")),
        "port": int(get_setting("smtp_port", os.environ.get("BCRC_SMTP_PORT", "587")) or 587),
        "user": get_setting("smtp_user", os.environ.get("BCRC_SMTP_USER", "")),
        "password": get_setting("smtp_password", os.environ.get("BCRC_SMTP_PASSWORD", "")),
        "from_email": get_setting("smtp_from_email", os.environ.get("BCRC_SMTP_FROM", "club@bekscity.com")),
        "from_name": get_setting("smtp_from_name", "BEKSCITY RUN CLUB"),
        "use_tls": get_setting("smtp_use_tls", "true").lower() in ("true", "1", "yes")
    }


def build_community_email_html(recipient_name, custom_note=None, event_summary=None, sync_url=None):
    """Builds a responsive, gold & charcoal branded HTML email for BCRC runners."""
    greeting_name = recipient_name if recipient_name else "Runner"
    note_html = ""
    if custom_note:
        clean_note = custom_note.replace("\n", "<br>")
        note_html = f"""
        <div style="background-color: #FEF3C7; border-left: 4px solid #D9A441; padding: 14px 18px; border-radius: 8px; margin: 20px 0;">
            <p style="margin: 0; font-size: 13px; line-height: 1.5; color: #78350F; font-weight: 500;">
                {clean_note}
            </p>
        </div>
        """

    # Districts spot table
    districts_rows = ""
    for d in DISTRICTS_DEFAULT:
        districts_rows += f"""
        <tr>
            <td style="padding: 8px 12px; font-weight: bold; color: #1A1D20; border-bottom: 1px solid #E2E8F0; font-size: 12px;">{d['name']}</td>
            <td style="padding: 8px 12px; color: #287D58; font-weight: 600; border-bottom: 1px solid #E2E8F0; font-size: 12px;">📍 {d['spot']}</td>
        </tr>
        """

    # Co-founders details
    cofounders_html = ""
    for c in COFOUNDERS_DEFAULT:
        cofounders_html += f"""
        <div style="display: inline-block; width: 31%; min-width: 150px; vertical-align: top; margin: 4px; padding: 10px; background: #F8FAFC; border-radius: 8px; border: 1px solid #E2E8F0; text-align: left;">
            <p style="margin: 0; font-weight: bold; color: #1A1D20; font-size: 12px;">{c['name']}</p>
            <p style="margin: 2px 0; color: #B88628; font-weight: 600; font-size: 11px;">📞 {c['phone']}</p>
            <p style="margin: 0; color: #64748B; font-size: 10px;">📸 @{c['social']}</p>
        </div>
        """

    sync_link = sync_url or "https://bekscity.com/api/calendar.ics"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>BEKSCITY RUN CLUB Calendar</title>
    </head>
    <body style="margin: 0; padding: 0; background-color: #F1F5F9; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #0F172A;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #F1F5F9; padding: 30px 10px;">
            <tr>
                <td align="center">
                    <table width="600" cellpadding="0" cellspacing="0" style="background-color: #FFFFFF; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.08); border: 1px solid #E2E8F0;">
                        <!-- Header -->
                        <tr>
                            <td style="background-color: #1A1D20; padding: 28px 32px; text-align: center; border-bottom: 4px solid #D9A441;">
                                <span style="background-color: #D9A441; color: #1A1D20; font-size: 10px; font-weight: 800; padding: 4px 10px; border-radius: 20px; text-transform: uppercase; letter-spacing: 1px;">
                                    Official Run Club Calendar
                                </span>
                                <h1 style="margin: 12px 0 4px 0; color: #FFFFFF; font-size: 24px; font-weight: 800; letter-spacing: 0.5px;">
                                    BEKSCITY RUN CLUB
                                </h1>
                                <p style="margin: 0; color: #D9A441; font-size: 12px; font-weight: 600;">
                                    Run. Improve. Connect. • Every Saturday at 06:45 AM (WAT)
                                </p>
                            </td>
                        </tr>

                        <!-- Body -->
                        <tr>
                            <td style="padding: 32px;">
                                <h2 style="margin: 0 0 12px 0; font-size: 18px; color: #1A1D20; font-weight: 700;">
                                    Hello {greeting_name}, 👋
                                </h2>
                                <p style="margin: 0 0 16px 0; font-size: 14px; line-height: 1.6; color: #334155;">
                                    We are thrilled to share the official <strong>BEKSCITY RUN CLUB Calendar</strong> for the upcoming quarter. 
                                    Your interactive calendar PDF is attached directly to this email for instant download, offline viewing, and printing.
                                </p>

                                {note_html}

                                <!-- Calendar Sync & Reminder Callout -->
                                <div style="background-color: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 12px; padding: 18px; margin: 24px 0;">
                                    <div style="font-weight: 700; color: #166534; font-size: 14px; margin-bottom: 6px;">
                                        🔔 Automated Calendar Reminders Included
                                    </div>
                                    <p style="margin: 0 0 12px 0; font-size: 12px; color: #15803D; line-height: 1.5;">
                                        Stay locked in! All confirmed Saturday runs sync with 3 automatic calendar alerts:
                                        <strong>5 days before</strong>, <strong>3 days before</strong>, and <strong>7 hours before</strong> the run.
                                    </p>
                                    <div style="text-align: center; margin-top: 10px;">
                                        <a href="{sync_link}" style="display: inline-block; background-color: #287D58; color: #FFFFFF; text-decoration: none; padding: 10px 20px; border-radius: 8px; font-weight: bold; font-size: 12px; margin: 4px;">
                                            📅 Sync Confirmed Runs to Calendar (.ics)
                                        </a>
                                    </div>
                                </div>

                                <!-- District Meetup Spots -->
                                <h3 style="margin: 24px 0 10px 0; font-size: 14px; color: #1A1D20; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 800;">
                                    📍 4 District Meet-Up Spots (06:45 AM WAT)
                                </h3>
                                <table width="100%" cellpadding="0" cellspacing="0" style="border: 1px solid #E2E8F0; border-radius: 8px; overflow: hidden; margin-bottom: 24px;">
                                    <tr style="background-color: #F8FAFC;">
                                        <th align="left" style="padding: 8px 12px; font-size: 11px; color: #64748B; border-bottom: 1px solid #E2E8F0;">DISTRICT</th>
                                        <th align="left" style="padding: 8px 12px; font-size: 11px; color: #64748B; border-bottom: 1px solid #E2E8F0;">EXACT LOCATION</th>
                                    </tr>
                                    {districts_rows}
                                </table>

                                <!-- Attachment Highlight -->
                                <div style="background-color: #F8FAFC; border: 2px dashed #CBD5E1; border-radius: 12px; padding: 16px; text-align: center; margin-bottom: 24px;">
                                    <p style="margin: 0; font-size: 13px; font-weight: 700; color: #1E293B;">
                                        📎 Attached File: Official BCRC Calendar PDF
                                    </p>
                                    <p style="margin: 4px 0 0 0; font-size: 11px; color: #64748B;">
                                        Open the attachment to view the full interactive schedule, tap any confirmed run to add to calendar, or inspect operational route maps.
                                    </p>
                                </div>

                                <!-- Co-Founders Contact -->
                                <h3 style="margin: 20px 0 10px 0; font-size: 13px; color: #1A1D20; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 800;">
                                    🤝 Co-Founders & Organizers
                                </h3>
                                <div style="text-align: center; margin-bottom: 20px;">
                                    {cofounders_html}
                                </div>

                                <p style="margin: 24px 0 0 0; font-size: 13px; color: #64748B; line-height: 1.5;">
                                    See you at the starting line this Saturday! 🏃‍♂️💨<br>
                                    <strong>BEKSCITY RUN CLUB Organizers</strong>
                                </p>
                            </td>
                        </tr>

                        <!-- Footer -->
                        <tr>
                            <td style="background-color: #F8FAFC; padding: 20px 32px; border-top: 1px solid #E2E8F0; text-align: center; font-size: 11px; color: #94A3B8;">
                                <p style="margin: 0;">
                                    © 2026 BEKSCITY RUN CLUB • Abeokuta, Ogun State, Nigeria.
                                </p>
                                <p style="margin: 4px 0 0 0;">
                                    You received this email because you are a registered runner or partner in the BCRC Community.
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    return html


def send_calendar_pdf_email(
    recipients,
    pdf_path,
    subject=None,
    custom_note=None,
    sync_url=None,
    image_paths=None
):
    """
    Sends the generated Calendar PDF and optional images to one or multiple recipients.
    
    If SMTP server credentials are valid in settings, dispatches real emails.
    Otherwise, runs in simulation/audit mode, saving the formatted email preview
    and logging all dispatches.
    
    Returns a dict with overall summary and per-recipient results.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"Calendar PDF not found at {pdf_path}")

    pdf_filename = os.path.basename(pdf_path)
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    config = get_smtp_config()
    default_subject = f"🏃 Official BEKSCITY RUN CLUB Calendar & Schedule — {pdf_filename.replace('.pdf', '')}"
    email_subject = subject or default_subject

    results = []
    is_live_smtp = bool(config["host"] and config["user"] and config["password"])

    smtp_conn = None
    if is_live_smtp:
        try:
            if config["use_tls"]:
                smtp_conn = smtplib.SMTP(config["host"], config["port"], timeout=15)
                smtp_conn.ehlo()
                smtp_conn.starttls()
                smtp_conn.ehlo()
            else:
                smtp_conn = smtplib.SMTP_SSL(config["host"], config["port"], timeout=15)
            smtp_conn.login(config["user"], config["password"])
        except Exception as e:
            # If SMTP connection fails, log error and fall back to simulation with warning
            smtp_conn = None
            is_live_smtp = False
            connection_error = str(e)
        else:
            connection_error = None
    else:
        connection_error = "SMTP not configured. Dispatched in safe simulation mode."

    os.makedirs(DISPATCH_PREVIEW_DIR, exist_ok=True)

    for r in recipients:
        r_email = r.get("email") if isinstance(r, dict) else str(r)
        r_name = r.get("name", "") if isinstance(r, dict) else ""
        if not r_email or "@" not in r_email:
            continue

        msg = EmailMessage()
        msg["Subject"] = email_subject
        msg["From"] = f"{config['from_name']} <{config['from_email']}>"
        msg["To"] = f"{r_name} <{r_email}>" if r_name else r_email

        # Body
        html_content = build_community_email_html(
            recipient_name=r_name,
            custom_note=custom_note,
            sync_url=sync_url
        )
        plain_text = f"Hello {r_name or 'Runner'},\n\nPlease find attached the official BEKSCITY RUN CLUB Calendar ({pdf_filename}).\n\nRun. Improve. Connect.\nEvery Saturday 06:45 AM WAT.\n\nBEKSCITY RUN CLUB"
        
        msg.set_content(plain_text)
        msg.add_alternative(html_content, subtype="html")

        # Attach PDF
        msg.add_attachment(
            pdf_bytes,
            maintype="application",
            subtype="pdf",
            filename=pdf_filename
        )

        # Attach optional images (e.g. race day flyers, brand sponsor logos, route maps)
        if image_paths:
            for img_p in image_paths:
                if img_p and os.path.exists(img_p):
                    img_fn = os.path.basename(img_p)
                    mime_type, _ = mimetypes.guess_type(img_p)
                    subtype = mime_type.split("/")[1] if mime_type and "/" in mime_type else "jpeg"
                    with open(img_p, "rb") as imf:
                        img_data = imf.read()
                    msg.add_attachment(
                        img_data,
                        maintype="image",
                        subtype=subtype,
                        filename=img_fn
                    )

        status = "SENT"
        err_msg = ""

        if is_live_smtp and smtp_conn:
            try:
                smtp_conn.send_message(msg)
                status = "SENT"
            except Exception as se:
                status = "FAILED"
                err_msg = str(se)
        else:
            status = "SIMULATED"
            err_msg = connection_error
            # Save a preview file for inspection
            preview_file = os.path.join(DISPATCH_PREVIEW_DIR, f"preview_{r_email.replace('@', '_at_')}.html")
            try:
                with open(preview_file, "w", encoding="utf-8") as pf:
                    pf.write(html_content)
            except Exception:
                pass

        disp_id = record_email_dispatch(
            recipient_email=r_email,
            recipient_name=r_name,
            subject=email_subject,
            pdf_filename=pdf_filename,
            status=status,
            error_message=err_msg
        )

        results.append({
            "dispatch_id": disp_id,
            "recipient_email": r_email,
            "recipient_name": r_name,
            "status": status,
            "error": err_msg
        })

    if smtp_conn:
        try:
            smtp_conn.quit()
        except Exception:
            pass

    success_count = sum(1 for item in results if item["status"] in ("SENT", "SIMULATED"))
    
    return {
        "success": True,
        "total_attempted": len(results),
        "dispatched_count": success_count,
        "mode": "LIVE_SMTP" if is_live_smtp else "SIMULATED",
        "pdf_filename": pdf_filename,
        "results": results,
        "message": f"Successfully sent calendar PDF to {success_count} recipient(s) ({'Live SMTP' if is_live_smtp else 'Simulation Mode — email preview logged'})."
    }

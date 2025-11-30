import os, csv, json, smtplib
import time
import requests
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from datetime import datetime
from celery import shared_task
from flask import current_app
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
 
from models import db, User, Reservation, ExportJob, ReservationStatus, create_notification

EXPORT_DIR = os.path.join(os.path.dirname(__file__), 'exports')
REPORT_DIR = os.path.join(EXPORT_DIR, 'reports')
os.makedirs(EXPORT_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)

GCHAT_WEBHOOK_URL = os.getenv('GCHAT_WEBHOOK_URL')  # Optional Google Chat Incoming Webhook

def _smtp_send(to_email, subject, html_body, attachments=None, retries=2, base_delay=2.0):
    """Send an email with simple retry/backoff on Mailtrap rate limits (550)."""
    host = os.getenv('SMTP_HOST')
    port = int(os.getenv('SMTP_PORT', '587'))
    user = os.getenv('SMTP_USER')
    pwd = os.getenv('SMTP_PASS')
    if not all([host, user, pwd, to_email]):
        print(f"[EMAIL-FAKE] To={to_email} Subj={subject}")
        return False
    last_exc = None
    for attempt in range(retries + 1):
        try:
            msg = MIMEMultipart()
            msg['From'] = user
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(html_body, 'html'))
            for path in (attachments or []):
                if not os.path.isfile(path):
                    print(f"[EMAIL] Attachment missing, skip: {path}")
                    continue
                with open(path, 'rb') as f:
                    part = MIMEApplication(f.read(), Name=os.path.basename(path))
                part['Content-Disposition'] = f'attachment; filename="{os.path.basename(path)}"'
                msg.attach(part)
            with smtplib.SMTP(host, port) as s:
                s.starttls()
                s.login(user, pwd)
                s.send_message(msg)
            return True
        except Exception as e:
            last_exc = e
            # Detect Mailtrap rate limit 550 specifically
            if hasattr(e, 'smtp_code') and e.smtp_code == 550 or ('550' in str(e) and 'Too many emails' in str(e)):
                print(f"[EMAIL][RATE_LIMIT] attempt={attempt} user={to_email} -> {e}")
                if attempt < retries:
                    sleep_for = base_delay * (attempt + 1)
                    time.sleep(sleep_for)
                    continue
            else:
                print("Email send failed:", e)
                break
    print(f"[EMAIL][FAILED] user={to_email} after {retries+1} attempts: {last_exc}")
    return False

def _gchat_send(text):
    """Send a message to Google Chat via Incoming Webhook."""
    # Read at call time to ensure environment from .env is loaded
    url = os.getenv('GCHAT_WEBHOOK_URL') or GCHAT_WEBHOOK_URL
    if not url:
        return False
    try:
        resp = requests.post(url, json={"text": text}, timeout=10)
        if 200 <= resp.status_code < 300:
            return True
        print(f"[GCHAT] send failed status={resp.status_code} body={resp.text}")
        return False
    except Exception as e:
        print("[GCHAT] exception:", e)
        return False

def _write_job_status(job_id, status, extra=None):
    data = {'job_id': job_id, 'status': status}
    if extra:
        data.update(extra)
    try:
        r = getattr(current_app, 'redis', None)
        if r:
            r.setex(f"job:{job_id}", 3600, json.dumps(data))
    except Exception:
        pass

@shared_task(name='tasks.send_daily_reminders')
def send_daily_reminders():
    # Fetch users then order by total reservations ascending so zero-reservation users (like user2) are attempted first.
    users = User.query.filter_by(role='user').all()
    users_with_counts = []
    for u in users:
        total_res = Reservation.query.filter_by(user_id=u.id).count()
        users_with_counts.append((u, total_res))
    users_with_counts.sort(key=lambda t: t[1])  # lowest reservation count first
    ordered_users = [t[0] for t in users_with_counts]
    reminders_sent = []
    skipped_active = []
    diagnostics = []
    for u in ordered_users:
        active = Reservation.query.filter_by(user_id=u.id, status=ReservationStatus.ACTIVE.value).first()
        if active:
            print(f"[REMINDER] Skip user={u.username} (ACTIVE reservation id={active.id})")
            skipped_active.append(u.username)
            diagnostics.append({'user': u.username, 'active': True, 'total_reservations': Reservation.query.filter_by(user_id=u.id).count(), 'action': 'SKIP_ACTIVE'})
            continue
        # send users with zero reservations a reminder
        total_reservations = Reservation.query.filter_by(user_id=u.id).count()
        reason = 'NO_RESERVATIONS' if total_reservations == 0 else 'NO_ACTIVE'
        title = "Daily Parking Reminder"
        msg = "You have no active parking reservation today. Book early to ensure availability."
        note = create_notification(u.id, 'REMINDER', title, msg)
        db.session.flush()
        html = (
            f"<h3>{title}</h3>"
            f"<p>{msg}</p>"
            f"<p>User: {u.username}</p>"
            f"<p>Reason: {reason}</p>"
        )
        gchat_text = f"Daily Parking Reminder\nUser: {u.username}\nReason: {reason}"
        # Prefer Chat for daily reminders; do NOT use Mailtrap when webhook is set
        webhook = os.getenv('GCHAT_WEBHOOK_URL') or GCHAT_WEBHOOK_URL
        if webhook:
            ok = _gchat_send(gchat_text)
        else:
            print("[REMINDER] GCHAT webhook not set; falling back to email.")
            ok = _smtp_send(u.email, title, html)
        if ok:
            note.mark_sent()
            reminders_sent.append(u.username)
            diagnostics.append({'user': u.username, 'active': False, 'total_reservations': total_reservations, 'action': 'SENT', 'reason': reason})
            print(f"[REMINDER] Sent to user={u.username} reason={reason}")
        else:
            if webhook:
                print(f"[REMINDER] GChat send failed for user={u.username}")
            else:
                print(f"[REMINDER] Email send failed or SMTP not configured for user={u.username}")
            diagnostics.append({'user': u.username, 'active': False, 'total_reservations': total_reservations, 'action': 'FAILED_SEND', 'reason': reason})
        # end loop
    db.session.commit()
    # Final diagnostics summary print for easy visibility in worker console
    print(f"[REMINDER][SUMMARY] processed={len(ordered_users)} sent={len(reminders_sent)} skipped_active={len(skipped_active)}")
    for row in diagnostics:
        print(f"[REMINDER][DIAG] {row}")
    return {
        'processed': len(ordered_users),
        'sent_count': len(reminders_sent),
        'sent_users': reminders_sent,
        'skipped_active_users': skipped_active,
        'diagnostics': diagnostics
    }

def _generate_pdf_report(user, rows, out_path):
    c = canvas.Canvas(out_path, pagesize=A4)
    w, h = A4
    y = h - 50
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, f"Monthly Parking Report - {user.full_name}")
    y -= 30
    c.setFont("Helvetica", 10)
    c.drawString(40, y, f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    y -= 40
    headers = ["ID", "Lot", "Spot", "Start", "End", "Hours", "Cost"]
    c.setFont("Helvetica-Bold", 10)
    c.drawString(40, y, " | ".join(headers))
    y -= 20
    c.setFont("Helvetica", 9)
    for r in rows:
        if y < 60:
            c.showPage()
            y = h - 60
        line = f"{r['id']} | {r['lot']} | {r['spot']} | {r['start']} | {r['end']} | {r['hours']} | {r['cost']}"
        c.drawString(40, y, line)
        y -= 14
    c.showPage()
    c.save()

@shared_task(name='tasks.generate_monthly_reports')
def generate_monthly_reports():
    users = User.query.filter_by(role='user').all()
    generated = 0
    for u in users:
        reservations = Reservation.query.filter_by(user_id=u.id, status=ReservationStatus.COMPLETED.value).order_by(Reservation.parking_timestamp.desc()).all()
        rows = []
        for r in reservations:
            lot = r.parking_spot.parking_lot if r.parking_spot else None
            rows.append({
                'id': r.id,
                'lot': lot.prime_location_name if lot else '',
                'spot': r.parking_spot.spot_number if r.parking_spot else '',
                'start': r.parking_timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'end': r.leaving_timestamp.strftime('%Y-%m-%d %H:%M:%S') if r.leaving_timestamp else '',
                'hours': r.duration_hours,
                'cost': r.final_cost
            })
        if not rows:
            continue
        pdf_name = f"monthly_report_{u.username}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
        pdf_path = os.path.join(REPORT_DIR, pdf_name)
        _generate_pdf_report(u, rows, pdf_path)
        total_cost = sum([r['cost'] or 0 for r in rows])
        title = "Monthly Parking Activity Report"
        msg = f"Dear {u.full_name}, your monthly activity summary is attached. Total spent: ₹{total_cost:.2f}."
        note = create_notification(u.id, 'REPORT', title, msg, file_path=pdf_path)
        db.session.flush()
        html = f"<h3>{title}</h3><p>Total Reservations: {len(rows)}</p><p>Total Spent: ₹{total_cost:.2f}</p>"
        ok = _smtp_send(u.email, title, html, attachments=[pdf_path])
        if ok:
            note.mark_sent(pdf_path)
            generated += 1
    db.session.commit()
    return {'users_processed': len(users), 'reports_sent': generated}

@shared_task(name='tasks.export_user_history')
def export_user_history(job_id):
    job = ExportJob.query.get(job_id)
    if not job:
        return
    job.mark('RUNNING'); db.session.commit()
    _write_job_status(job_id, 'RUNNING')
    try:
        user = job.user
        reservations = Reservation.query.filter_by(user_id=user.id).order_by(Reservation.created_at.desc()).all()
        filename = f"user_history_{user.username}_{job_id}.csv"
        path = os.path.join(EXPORT_DIR, filename)
        with open(path, 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            w.writerow(['ReservationID','Lot','Spot','Vehicle','Start','End','Status','FinalCost'])
            for r in reservations:
                spot = r.parking_spot
                lot = spot.parking_lot if spot else None
                w.writerow([
                    r.id,
                    lot.prime_location_name if lot else '',
                    spot.spot_number if spot else '',
                    r.vehicle_number,
                    r.parking_timestamp.strftime('%Y-%m-%d %H:%M:%S') if r.parking_timestamp else '',
                    r.leaving_timestamp.strftime('%Y-%m-%d %H:%M:%S') if r.leaving_timestamp else '',
                    r.status,
                    r.final_cost
                ])
        job.mark('COMPLETED', path); db.session.commit()
        _write_job_status(job_id, 'COMPLETED', {'file': filename})
    except Exception as e:
        job.mark('FAILED'); db.session.commit()
        _write_job_status(job_id, 'FAILED', {'error': str(e)})

@shared_task(name='tasks.export_admin_all')
def export_admin_all(job_id):
    job = ExportJob.query.get(job_id)
    if not job:
        return
    job.mark('RUNNING'); db.session.commit()
    _write_job_status(job_id, 'RUNNING')
    try:
        reservations = Reservation.query.order_by(Reservation.created_at.desc()).all()
        filename = f"all_reservations_{job_id}.csv"
        path = os.path.join(EXPORT_DIR, filename)
        with open(path, 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            w.writerow(['ReservationID','User','Lot','Spot','Vehicle','Start','End','Status','FinalCost'])
            for r in reservations:
                spot = r.parking_spot
                lot = spot.parking_lot if spot else None
                w.writerow([
                    r.id,
                    r.user.username,
                    lot.prime_location_name if lot else '',
                    spot.spot_number if spot else '',
                    r.vehicle_number,
                    r.parking_timestamp.strftime('%Y-%m-%d %H:%M:%S') if r.parking_timestamp else '',
                    r.leaving_timestamp.strftime('%Y-%m-%d %H:%M:%S') if r.leaving_timestamp else '',
                    r.status,
                    r.final_cost
                ])
        job.mark('COMPLETED', path); db.session.commit()
        _write_job_status(job_id, 'COMPLETED', {'file': filename})
    except Exception as e:
        job.mark('FAILED'); db.session.commit()
        _write_job_status(job_id, 'FAILED', {'error': str(e)})

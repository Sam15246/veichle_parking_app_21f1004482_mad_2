import os, csv, json, smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from datetime import datetime
from celery import shared_task
from flask import current_app
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from sqlalchemy import func
from models import db, User, Reservation, ParkingSpot, ParkingLot, ExportJob, ReservationStatus, Notification, create_notification

EXPORT_DIR = os.path.join(os.path.dirname(__file__), 'exports')
REPORT_DIR = os.path.join(EXPORT_DIR, 'reports')
os.makedirs(EXPORT_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)

def _smtp_send(to_email, subject, html_body, attachments=None):
    host = os.getenv('SMTP_HOST')
    port = int(os.getenv('SMTP_PORT', '587'))
    user = os.getenv('SMTP_USER')
    pwd = os.getenv('SMTP_PASS')
    if not all([host, user, pwd, to_email]):
        # Fallback: print to console
        print(f"[EMAIL-FAKE] To={to_email} Subj={subject}")
        return False
    try:
        msg = MIMEMultipart()
        msg['From'] = user
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(html_body, 'html'))
        for path in (attachments or []):
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
        print("Email send failed:", e)
        return False

def _write_job_status(job_id, status, extra=None):
    key = f"job:{job_id}"
    data = {'job_id': job_id, 'status': status}
    if extra:
        data.update(extra)
    try:
        current_app.redis.setex(key, 3600, json.dumps(data))
    except:
        pass

@shared_task(name='tasks.send_daily_reminders')
def send_daily_reminders():
    users = User.query.filter_by(role='user').all()
    sent = 0
    for u in users:
        active = Reservation.query.filter_by(user_id=u.id, status=ReservationStatus.ACTIVE.value).first()
        if active:
            continue  # skip users already parked
        title = "Daily Parking Reminder"
        msg = "You have no active parking reservation today. Book early to ensure availability."
        note = create_notification(u.id, 'REMINDER', title, msg)
        db.session.flush()
        html = f"<h3>{title}</h3><p>{msg}</p><p>User: {u.username}</p>"
        ok = _smtp_send(u.email, title, html)
        if ok:
            note.mark_sent()
            sent += 1
    db.session.commit()
    return {'processed': len(users), 'sent': sent}

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
                'start': r.parking_timestamp.strftime('%Y-%m-%d %H:%M'),
                'end': r.leaving_timestamp.strftime('%Y-%m-%d %H:%M') if r.leaving_timestamp else '',
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
                    r.parking_timestamp,
                    r.leaving_timestamp,
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
                    r.parking_timestamp,
                    r.leaving_timestamp,
                    r.status,
                    r.final_cost
                ])
        job.mark('COMPLETED', path); db.session.commit()
        _write_job_status(job_id, 'COMPLETED', {'file': filename})
    except Exception as e:
        job.mark('FAILED'); db.session.commit()
        _write_job_status(job_id, 'FAILED', {'error': str(e)})

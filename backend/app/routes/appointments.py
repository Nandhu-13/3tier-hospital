from flask import Blueprint, request, jsonify
from ..database import DBConnection
from datetime import date, datetime, time, timedelta

appointments_bp = Blueprint('appointments', __name__)


# ✅ Updated serializer (handles ALL cases)
def serialize(row):
    """Convert DB row values into JSON-safe formats."""
    for k, v in row.items():
        if isinstance(v, (date, datetime)):
            row[k] = v.isoformat()
        elif isinstance(v, time):
            row[k] = v.strftime("%H:%M:%S")   # clean time format
        elif isinstance(v, timedelta):
            # Convert timedelta to HH:MM format
            total_seconds = int(v.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            row[k] = f"{hours:02}:{minutes:02}"
    return row


# ✅ GET all appointments
@appointments_bp.route('/', methods=['GET'])
def get_appointments():
    try:
        with DBConnection() as (conn, cur):
            cur.execute("""
                SELECT
                    a.id, a.patient_id, a.doctor_id,
                    a.appointment_date, a.appointment_time,
                    a.status, a.notes, a.created_at,
                    p.name  AS patient_name,
                    d.name  AS doctor_name,
                    d.specialization
                FROM appointments a
                JOIN patients p ON a.patient_id = p.id
                JOIN doctors  d ON a.doctor_id  = d.id
                ORDER BY a.appointment_date DESC, a.appointment_time DESC
            """)
            rows = cur.fetchall()
            return jsonify([serialize(dict(r)) for r in rows])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ✅ ADD new appointment
@appointments_bp.route('/', methods=['POST'])
def add_appointment():
    data = request.get_json()

    required = ['patient_id', 'doctor_id', 'appointment_date', 'appointment_time']
    if not all(data.get(f) for f in required):
        return jsonify({'error': 'patient_id, doctor_id, date, time are required'}), 400

    try:
        with DBConnection() as (conn, cur):
            cur.execute(
                """INSERT INTO appointments
                   (patient_id, doctor_id, appointment_date, appointment_time, notes)
                   VALUES (%s, %s, %s, %s, %s)""",
                (
                    data['patient_id'],
                    data['doctor_id'],
                    data['appointment_date'],
                    data['appointment_time'],
                    data.get('notes')
                )
            )
            new_id = cur.lastrowid

        # Fetch inserted record
        with DBConnection() as (conn, cur):
            cur.execute("""
                SELECT
                    a.id, a.patient_id, a.doctor_id,
                    a.appointment_date, a.appointment_time,
                    a.status, a.notes, a.created_at,
                    p.name AS patient_name,
                    d.name AS doctor_name,
                    d.specialization
                FROM appointments a
                JOIN patients p ON a.patient_id = p.id
                JOIN doctors  d ON a.doctor_id  = d.id
                WHERE a.id = %s
            """, (new_id,))
            row = cur.fetchone()
            return jsonify(serialize(dict(row))), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ✅ UPDATE appointment status
@appointments_bp.route('/<int:appt_id>/status', methods=['PUT'])
def update_status(appt_id):
    data = request.get_json()
    status = data.get('status')

    if status not in ('Scheduled', 'Completed', 'Cancelled'):
        return jsonify({'error': 'Invalid status value'}), 400

    try:
        with DBConnection() as (conn, cur):
            cur.execute(
                "UPDATE appointments SET status = %s WHERE id = %s",
                (status, appt_id)
            )

            if cur.rowcount == 0:
                return jsonify({'error': 'Appointment not found'}), 404

            return jsonify({'message': f'Status updated to {status}'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ✅ DELETE appointment
@appointments_bp.route('/<int:appt_id>', methods=['DELETE'])
def delete_appointment(appt_id):
    try:
        with DBConnection() as (conn, cur):
            cur.execute("DELETE FROM appointments WHERE id = %s", (appt_id,))

            if cur.rowcount == 0:
                return jsonify({'error': 'Appointment not found'}), 404

            return jsonify({'message': 'Appointment deleted'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500
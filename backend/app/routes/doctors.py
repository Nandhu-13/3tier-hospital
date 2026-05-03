from flask import Blueprint, request, jsonify
from ..database import DBConnection

doctors_bp = Blueprint('doctors', __name__)


@doctors_bp.route('/', methods=['GET'])
def get_doctors():
    try:
        with DBConnection() as (conn, cur):
            cur.execute("SELECT * FROM doctors ORDER BY created_at DESC")
            rows = cur.fetchall()
            for r in rows:
                r['created_at'] = str(r['created_at']) if r.get('created_at') else None
            return jsonify(rows)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@doctors_bp.route('/', methods=['POST'])
def add_doctor():
    data = request.get_json()
    if not all(data.get(f) for f in ['name', 'specialization']):
        return jsonify({'error': 'name and specialization are required'}), 400
    try:
        with DBConnection() as (conn, cur):
            cur.execute(
                """INSERT INTO doctors (name, specialization, phone, email, availability)
                   VALUES (%s, %s, %s, %s, %s)""",
                (data['name'], data['specialization'], data.get('phone'),
                 data.get('email'), data.get('availability', 'Available'))
            )
            new_id = cur.lastrowid
        with DBConnection() as (conn, cur):
            cur.execute("SELECT * FROM doctors WHERE id = %s", (new_id,))
            row = cur.fetchone()
            row['created_at'] = str(row['created_at']) if row.get('created_at') else None
            return jsonify(row), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@doctors_bp.route('/<int:doctor_id>', methods=['PUT'])
def update_doctor(doctor_id):
    data = request.get_json()
    try:
        with DBConnection() as (conn, cur):
            cur.execute(
                """UPDATE doctors SET name=%s, specialization=%s, phone=%s,
                   email=%s, availability=%s WHERE id=%s""",
                (data['name'], data['specialization'], data.get('phone'),
                 data.get('email'), data.get('availability', 'Available'), doctor_id)
            )
            if cur.rowcount == 0:
                return jsonify({'error': 'Doctor not found'}), 404
        with DBConnection() as (conn, cur):
            cur.execute("SELECT * FROM doctors WHERE id = %s", (doctor_id,))
            row = cur.fetchone()
            row['created_at'] = str(row['created_at']) if row.get('created_at') else None
            return jsonify(row)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@doctors_bp.route('/<int:doctor_id>', methods=['DELETE'])
def delete_doctor(doctor_id):
    try:
        with DBConnection() as (conn, cur):
            cur.execute("DELETE FROM doctors WHERE id = %s", (doctor_id,))
            if cur.rowcount == 0:
                return jsonify({'error': 'Doctor not found'}), 404
            return jsonify({'message': 'Doctor deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

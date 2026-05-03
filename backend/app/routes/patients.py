from flask import Blueprint, request, jsonify
from ..database import DBConnection

patients_bp = Blueprint('patients', __name__)


@patients_bp.route('/', methods=['GET'])
def get_patients():
    try:
        with DBConnection() as (conn, cur):
            cur.execute("SELECT * FROM patients ORDER BY created_at DESC")
            rows = cur.fetchall()
            # Convert datetime to string
            for r in rows:
                r['created_at'] = str(r['created_at']) if r.get('created_at') else None
            return jsonify(rows)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@patients_bp.route('/', methods=['POST'])
def add_patient():
    data = request.get_json()
    if not all(data.get(f) for f in ['name', 'age', 'gender']):
        return jsonify({'error': 'name, age, gender are required'}), 400
    try:
        with DBConnection() as (conn, cur):
            cur.execute(
                """INSERT INTO patients (name, age, gender, phone, email, address, blood_group)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (data['name'], data['age'], data['gender'],
                 data.get('phone'), data.get('email'),
                 data.get('address'), data.get('blood_group'))
            )
            new_id = cur.lastrowid
        with DBConnection() as (conn, cur):
            cur.execute("SELECT * FROM patients WHERE id = %s", (new_id,))
            row = cur.fetchone()
            row['created_at'] = str(row['created_at']) if row.get('created_at') else None
            return jsonify(row), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@patients_bp.route('/<int:patient_id>', methods=['PUT'])
def update_patient(patient_id):
    data = request.get_json()
    try:
        with DBConnection() as (conn, cur):
            cur.execute(
                """UPDATE patients SET name=%s, age=%s, gender=%s, phone=%s,
                   email=%s, address=%s, blood_group=%s WHERE id=%s""",
                (data['name'], data['age'], data['gender'], data.get('phone'),
                 data.get('email'), data.get('address'), data.get('blood_group'), patient_id)
            )
            if cur.rowcount == 0:
                return jsonify({'error': 'Patient not found'}), 404
        with DBConnection() as (conn, cur):
            cur.execute("SELECT * FROM patients WHERE id = %s", (patient_id,))
            row = cur.fetchone()
            row['created_at'] = str(row['created_at']) if row.get('created_at') else None
            return jsonify(row)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@patients_bp.route('/<int:patient_id>', methods=['DELETE'])
def delete_patient(patient_id):
    try:
        with DBConnection() as (conn, cur):
            cur.execute("DELETE FROM patients WHERE id = %s", (patient_id,))
            if cur.rowcount == 0:
                return jsonify({'error': 'Patient not found'}), 404
            return jsonify({'message': 'Patient deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

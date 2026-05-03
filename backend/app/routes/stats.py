from flask import Blueprint, jsonify
from ..database import DBConnection

stats_bp = Blueprint('stats', __name__)


@stats_bp.route('/stats', methods=['GET'])
def get_stats():
    try:
        with DBConnection() as (conn, cur):
            cur.execute("SELECT COUNT(*) AS cnt FROM patients")
            patients = cur.fetchone()['cnt']

            cur.execute("SELECT COUNT(*) AS cnt FROM doctors")
            doctors = cur.fetchone()['cnt']

            cur.execute("SELECT COUNT(*) AS cnt FROM appointments WHERE status = 'Scheduled'")
            scheduled = cur.fetchone()['cnt']

            cur.execute("SELECT COUNT(*) AS cnt FROM departments")
            departments = cur.fetchone()['cnt']

        return jsonify({
            'totalPatients':         patients,
            'totalDoctors':          doctors,
            'scheduledAppointments': scheduled,
            'totalDepartments':      departments,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

from flask import Blueprint, jsonify
from ..database import DBConnection

departments_bp = Blueprint('departments', __name__)


@departments_bp.route('/', methods=['GET'])
def get_departments():
    try:
        with DBConnection() as (conn, cur):
            cur.execute("SELECT * FROM departments ORDER BY id")
            return jsonify(cur.fetchall())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

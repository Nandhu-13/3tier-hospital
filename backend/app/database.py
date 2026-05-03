import os
import pymysql
import pymysql.cursors
from pymysql import OperationalError
import threading
import logging

logger = logging.getLogger(__name__)

# ── Simple thread-safe connection pool ────────────────────────
_lock = threading.Lock()
_pool = []
MAX_POOL = 10


def _new_conn():
    """Create a new Azure MySQL connection with SSL."""
    conn = pymysql.connect(
        host=os.environ.get('DB_HOST'),
        port=int(os.environ.get('DB_PORT', 3306)),
        database=os.environ.get('DB_NAME'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASSWORD'),
        ssl={'ssl': {'ca': os.environ.get('DB_SSL_CA', '')} if os.environ.get('DB_SSL_CA') else True},
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,   # Returns rows as dicts
        connect_timeout=10,
        autocommit=False,
    )
    return conn


def get_db():
    """Get a connection — reuse from pool or create new."""
    with _lock:
        while _pool:
            conn = _pool.pop()
            try:
                conn.ping(reconnect=True)
                return conn
            except Exception:
                pass
    return _new_conn()


def release_db(conn):
    """Return connection to pool."""
    with _lock:
        if len(_pool) < MAX_POOL:
            _pool.append(conn)
        else:
            try:
                conn.close()
            except Exception:
                pass


# ── Context manager ────────────────────────────────────────────
class DBConnection:
    def __enter__(self):
        self.conn = get_db()
        self.cur  = self.conn.cursor()
        return self.conn, self.cur

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.conn.rollback()
            logger.error(f"DB error, rolled back: {exc_val}")
        else:
            self.conn.commit()
        self.cur.close()
        release_db(self.conn)


# ── Schema + seed ──────────────────────────────────────────────
def init_db():
    with DBConnection() as (conn, cur):

        # MySQL uses backticks, AUTO_INCREMENT, and DATETIME
        cur.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                id          INT AUTO_INCREMENT PRIMARY KEY,
                name        VARCHAR(100) NOT NULL,
                age         INT NOT NULL,
                gender      VARCHAR(10)  NOT NULL,
                phone       VARCHAR(20),
                email       VARCHAR(100),
                address     TEXT,
                blood_group VARCHAR(5),
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS doctors (
                id             INT AUTO_INCREMENT PRIMARY KEY,
                name           VARCHAR(100) NOT NULL,
                specialization VARCHAR(100) NOT NULL,
                phone          VARCHAR(20),
                email          VARCHAR(100),
                availability   VARCHAR(50) DEFAULT 'Available',
                created_at     DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS departments (
                id               INT AUTO_INCREMENT PRIMARY KEY,
                name             VARCHAR(100) NOT NULL,
                head_doctor      VARCHAR(100),
                capacity         INT DEFAULT 0,
                current_patients INT DEFAULT 0
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS appointments (
                id               INT AUTO_INCREMENT PRIMARY KEY,
                patient_id       INT,
                doctor_id        INT,
                appointment_date DATE NOT NULL,
                appointment_time TIME NOT NULL,
                status           VARCHAR(20) DEFAULT 'Scheduled',
                notes            TEXT,
                created_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
                FOREIGN KEY (doctor_id)  REFERENCES doctors(id)  ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        # Seed only if empty
        cur.execute("SELECT COUNT(*) AS cnt FROM doctors")
        if cur.fetchone()['cnt'] == 0:
            cur.execute("""
                INSERT INTO departments (name, head_doctor, capacity, current_patients) VALUES
                    ('Cardiology',  'Dr. Arjun Sharma', 50, 32),
                    ('Neurology',   'Dr. Priya Reddy',  40, 28),
                    ('Orthopedics', 'Dr. Vikram Singh', 45, 19),
                    ('Pediatrics',  'Dr. Sunita Rao',   60, 41),
                    ('Emergency',   'Dr. Kiran Kumar',  30, 22);
            """)
            cur.execute("""
                INSERT INTO doctors (name, specialization, phone, email, availability) VALUES
                    ('Dr. Arjun Sharma', 'Cardiologist',        '9876543210', 'arjun@hospital.com',  'Available'),
                    ('Dr. Priya Reddy',  'Neurologist',         '9876543211', 'priya@hospital.com',  'Available'),
                    ('Dr. Vikram Singh', 'Orthopedic Surgeon',  '9876543212', 'vikram@hospital.com', 'Busy'),
                    ('Dr. Sunita Rao',   'Pediatrician',        '9876543213', 'sunita@hospital.com', 'Available'),
                    ('Dr. Kiran Kumar',  'Emergency Physician', '9876543214', 'kiran@hospital.com',  'Available');
            """)
            cur.execute("""
                INSERT INTO patients (name, age, gender, phone, email, blood_group) VALUES
                    ('Ramesh Patel', 45, 'Male',   '9123456789', 'ramesh@gmail.com',  'O+'),
                    ('Suman Devi',   32, 'Female', '9123456790', 'suman@gmail.com',   'A+'),
                    ('Manoj Kumar',  58, 'Male',   '9123456791', 'manoj@gmail.com',   'B+'),
                    ('Lakshmi Nair', 28, 'Female', '9123456792', 'lakshmi@gmail.com', 'AB+'),
                    ('Anil Gupta',   67, 'Male',   '9123456793', 'anil@gmail.com',    'O-');
            """)
            logger.info("✅ Seed data inserted")

    logger.info("✅ MySQL schema ready")

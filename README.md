# 🏥 Hospital Management System
### Python Flask · Azure Database for MySQL · Kubernetes 3-Tier Architecture

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     KUBERNETES CLUSTER                          │
│  Namespace: hospital-system                                     │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  TIER 3 — PRESENTATION  (Nginx pods, x2 replicas)        │   │
│  │  Serves HTML · Proxies /api/* → backend-service          │   │
│  │           frontend-service  (LoadBalancer :80)           │   │
│  └─────────────────────┬────────────────────────────────────┘   │
│                        │ HTTP /api/*                            │
│  ┌─────────────────────▼────────────────────────────────────┐   │
│  │  TIER 2 — APPLICATION  (Flask + Gunicorn pods, x2)       │   │
│  │  Python Flask REST API · PyMySQL · HPA: 2–6 pods         │   │
│  │           backend-service  (ClusterIP :5000)             │   │
│  └─────────────────────┬────────────────────────────────────┘   │
│                        │ SSL :3306                              │
└────────────────────────┼────────────────────────────────────────┘
                         │
          ┌──────────────▼──────────────────────────┐
          │  ☁  AZURE DATABASE FOR MYSQL             │
          │     Flexible Server (managed)            │
          │     Port 3306 · SSL · Auto-backups       │
          └─────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
hospital-mysql/
├── backend/
│   ├── app/
│   │   ├── __init__.py          # Flask app factory
│   │   ├── database.py          # PyMySQL connection pool + Azure SSL
│   │   └── routes/
│   │       ├── patients.py      # CRUD /api/patients/
│   │       ├── doctors.py       # CRUD /api/doctors/
│   │       ├── appointments.py  # CRUD /api/appointments/
│   │       ├── departments.py   # GET  /api/departments/
│   │       └── stats.py         # GET  /api/stats
│   ├── wsgi.py                  # Gunicorn entry point
│   ├── gunicorn.conf.py         # Production Gunicorn config
│   ├── requirements.txt         # Flask, gunicorn, PyMySQL, cryptography
│   ├── .env.example             # Environment variable template
│   └── Dockerfile               # Multi-stage Python build
│
├── frontend/
│   ├── src/index.html           # Full HMS UI
│   ├── nginx.conf               # Nginx + /api/ proxy
│   └── Dockerfile
│
└── k8s/
    ├── namespace/namespace.yaml
    ├── secrets/azure-mysql-secret.yaml
    ├── configmaps/config.yaml       # DB_PORT=3306
    ├── backend/backend.yaml         # Deployment + HPA + ClusterIP
    ├── frontend/frontend.yaml       # Deployment + HPA + LoadBalancer
    └── ingress/network-policy.yaml
```

---

## 🐍 Python Libraries

| Library       | Version | Purpose                              |
|---------------|---------|--------------------------------------|
| Flask         | 3.0.2   | Web framework                        |
| flask-cors    | 4.0.0   | Cross-origin request support         |
| gunicorn      | 21.2.0  | Production WSGI server               |
| PyMySQL       | 1.1.0   | Pure-Python MySQL driver (Azure-ready)|
| cryptography  | 42.0.5  | SSL authentication for PyMySQL       |
| python-dotenv | 1.0.1   | .env file support                    |

---

## ☁️ Step 1 — Create Azure Database for MySQL

### In Azure Portal:
1. **Create Resource** → Search **"Azure Database for MySQL"**
2. Choose **Flexible Server** → Click Create
3. Fill in:
   - **Server name**: `hospital-mysql-server` (must be unique globally)
   - **Region**: Choose nearest to you
   - **MySQL version**: `8.0`
   - **Admin username**: `hospitaladmin`
   - **Password**: `YourStrongPassword123!`
4. Under **Networking**:
   - Allow public access ✅
   - Add your current IP to firewall rules ✅
   - Check **Allow public access from Azure services** ✅
5. Click **Review + Create** → **Create**

### After deployment, create the database:
```
Connection details from Azure Portal:
  Host:     hospital-mysql-server.mysql.database.azure.com
  Port:     3306
  User:     hospitaladmin
  Password: YourStrongPassword123!
```

Connect using MySQL Workbench or CLI and run:
```sql
CREATE DATABASE hospitaldb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

---

## 🐍 Step 2 — Test Backend Locally (Windows)

### Install Python
- Download: https://www.python.org/downloads/
- ✅ Check **"Add Python to PATH"** during install

### Setup virtual environment
```powershell
cd hospital-mysql\backend

python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt
```

### Set environment variables
```powershell
$env:DB_HOST     = "hospital-mysql-server.mysql.database.azure.com"
$env:DB_PORT     = "3306"
$env:DB_NAME     = "hospitaldb"
$env:DB_USER     = "hospitaladmin"
$env:DB_PASSWORD = "YourStrongPassword123!"
$env:FLASK_ENV   = "development"
```

### Run the Flask backend
```powershell
python wsgi.py
```

You should see:
```
✅ MySQL schema ready
✅ Seed data inserted
🏥 Hospital Backend running on port 5000
```

---

## 🌐 Step 3 — Serve Frontend Locally

```powershell
# Install serve (one-time)
npm install -g serve

# Serve the frontend
cd hospital-mysql\frontend\src
serve -p 3000
```

Open: **http://localhost:3000**

---

## 🧪 Step 4 — Test REST API (PowerShell)

```powershell
# Health check
Invoke-RestMethod http://localhost:5000/api/health

# Dashboard stats
Invoke-RestMethod http://localhost:5000/api/stats

# List patients
Invoke-RestMethod http://localhost:5000/api/patients/

# Add a patient
$body = @{
  name="Test Patient"; age=30; gender="Male"
  phone="9999999999"; blood_group="O+"
} | ConvertTo-Json
Invoke-RestMethod -Uri http://localhost:5000/api/patients/ -Method POST -Body $body -ContentType "application/json"

# List doctors
Invoke-RestMethod http://localhost:5000/api/doctors/

# Add a doctor
$doc = @{name="Dr. Test";specialization="Cardiologist";availability="Available"} | ConvertTo-Json
Invoke-RestMethod -Uri http://localhost:5000/api/doctors/ -Method POST -Body $doc -ContentType "application/json"

# List appointments
Invoke-RestMethod http://localhost:5000/api/appointments/

# List departments
Invoke-RestMethod http://localhost:5000/api/departments/
```

---

## 🐳 Step 5 — Build Docker Images

```powershell
# Build backend image
docker build -t hospital-backend:latest .\backend\

# Build frontend image
docker build -t hospital-frontend:latest .\frontend\

# Test backend container locally
docker run -d -p 5000:5000 `
  -e DB_HOST=hospital-mysql-server.mysql.database.azure.com `
  -e DB_PORT=3306 `
  -e DB_USER=hospitaladmin `
  -e DB_PASSWORD=YourStrongPassword123! `
  -e DB_NAME=hospitaldb `
  --name hms-backend hospital-backend:latest

# Test frontend container
docker run -d -p 3000:80 --name hms-frontend hospital-frontend:latest
```

---

## ☸️ Step 6 — Deploy to Kubernetes

```bash
# 1. Create namespace
kubectl apply -f k8s/namespace/namespace.yaml

# 2. Create Azure MySQL secret (replace values)
kubectl create secret generic azure-mysql-secret \
  --namespace=hospital-system \
  --from-literal=DB_HOST=hospital-mysql-server.mysql.database.azure.com \
  --from-literal=DB_USER=hospitaladmin \
  --from-literal=DB_PASSWORD=YourStrongPassword123! \
  --from-literal=DB_NAME=hospitaldb

# 3. Apply ConfigMap
kubectl apply -f k8s/configmaps/config.yaml

# 4. Deploy backend (Flask + Gunicorn)
kubectl apply -f k8s/backend/backend.yaml

# 5. Deploy frontend (Nginx)
kubectl apply -f k8s/frontend/frontend.yaml

# 6. Apply network policies
kubectl apply -f k8s/ingress/network-policy.yaml

# 7. Check everything
kubectl get all -n hospital-system
kubectl logs -f deployment/backend -n hospital-system
```

---

## 📡 REST API Reference

| Method | Endpoint                       | Description           |
|--------|--------------------------------|-----------------------|
| GET    | /api/health                    | Health check          |
| GET    | /api/stats                     | Dashboard stats       |
| GET    | /api/patients/                 | List patients         |
| POST   | /api/patients/                 | Add patient           |
| PUT    | /api/patients/:id              | Update patient        |
| DELETE | /api/patients/:id              | Delete patient        |
| GET    | /api/doctors/                  | List doctors          |
| POST   | /api/doctors/                  | Add doctor            |
| PUT    | /api/doctors/:id               | Update doctor         |
| DELETE | /api/doctors/:id               | Delete doctor         |
| GET    | /api/appointments/             | List appointments     |
| POST   | /api/appointments/             | Schedule appointment  |
| PUT    | /api/appointments/:id/status   | Update status         |
| DELETE | /api/appointments/:id          | Delete appointment    |
| GET    | /api/departments/              | List departments      |

---

## ⚠️ Key Differences: MySQL vs PostgreSQL

| | PostgreSQL | MySQL (this project) |
|---|---|---|
| Driver | psycopg2 | **PyMySQL** |
| Port | 5432 | **3306** |
| Auto-increment | SERIAL | **AUTO_INCREMENT** |
| Cursor result | Tuple | **Dict (DictCursor)** |
| SSL mode env | DB_SSL_MODE | Built-in via PyMySQL |
| Last insert ID | RETURNING id | **cursor.lastrowid** |

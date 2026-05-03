# gunicorn.conf.py  – production configuration
import multiprocessing

# Server socket
bind        = "0.0.0.0:5000"
backlog     = 2048

# Worker processes
workers     = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout     = 30
keepalive   = 2

# Logging
accesslog   = "-"       # stdout
errorlog    = "-"       # stderr
loglevel    = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name   = "hospital-backend"

# Restart workers after this many requests (memory leak prevention)
max_requests        = 1000
max_requests_jitter = 100

# Graceful timeout
graceful_timeout = 30

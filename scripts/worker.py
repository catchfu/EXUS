import time
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from core.db import SessionLocal
from core.models import Job
from core.jobs import process_mining_job

def run_worker():
    while True:
        db = SessionLocal()
        try:
            jobs = db.query(Job).filter_by(status='queued').limit(5).all()
            for j in jobs:
                process_mining_job(j.id, os.getenv('WORKER_USERNAME') or 'demo_user')
        finally:
            db.close()
        time.sleep(1)

if __name__ == '__main__':
    run_worker()

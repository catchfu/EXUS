import os
import logging

def enqueue_or_thread(func, *args, **kwargs):
    redis_url = os.getenv('REDIS_URL')
    if redis_url:
        try:
            from rq import Queue
            from redis import Redis
            conn = Redis.from_url(redis_url)
            q = Queue('nexus', connection=conn)
            job = q.enqueue(func, *args, **kwargs)
            return {"mode": "rq", "id": job.id}
        except Exception as e:
            logging.error(f"rq_enqueue_failed: {e}")
    import threading
    t = threading.Thread(target=func, args=args, kwargs=kwargs, daemon=True)
    t.start()
    return {"mode": "thread"}


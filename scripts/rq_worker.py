import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from rq import Worker, Queue, Connection
from redis import Redis

def main():
    url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    conn = Redis.from_url(url)
    with Connection(conn):
        w = Worker(['nexus'])
        w.work()

if __name__ == '__main__':
    main()

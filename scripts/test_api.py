import requests, time

BASE = "http://127.0.0.1:5000"

def main():
    s = requests.Session()
    r = s.post(f"{BASE}/api/login/dev", json={"username":"tester"})
    print("login:", r.status_code, r.text)

    r = s.post(f"{BASE}/api/mine/job", json={"username":"tester"})
    print("queue:", r.status_code, r.text)
    job_id = r.json()["job_id"]

    for _ in range(30):
        time.sleep(0.5)
        jr = s.get(f"{BASE}/api/job/{job_id}")
        print("job:", jr.status_code)
        j = jr.json()
        if j.get("status") == "completed":
            print("result keys:", list(j["result"].keys()))
            break

    print("cnft list:", s.get(f"{BASE}/api/cnft/list").status_code)
    print("chain stats:", s.get(f"{BASE}/api/chain/stats").json())
    print("market:", s.get(f"{BASE}/api/market/data").json())

if __name__ == "__main__":
    main()


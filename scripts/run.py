import subprocess, sys, time

def run():
    ui = subprocess.Popen([sys.executable, "-m", "ui.app"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print("http://localhost:5000/")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        ui.terminate()

if __name__ == "__main__":
    run()


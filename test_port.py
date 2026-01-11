import socket
import time

def check_port(host, port, timeout=2):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    result = sock.connect_ex((host, port))
    sock.close()
    return result == 0

print("Testing connectivity to localhost:8000...")
for i in range(10):
    if check_port("127.0.0.1", 8000):
        print("✅ Port 8000 is OPEN on 127.0.0.1")
        break
    else:
        print(f"❌ Attempt {i+1}: Port 8000 is CLOSED")
        time.sleep(1)
else:
    print("❌ Failed to connect after 10 attempts")

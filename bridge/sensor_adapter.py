from v_bridge import VBridge
import random

bridge = VBridge()

def simulate_pressure():
    pressure = random.uniform(0.3, 0.9)
    future = random.uniform(0.4, 0.8)

    bridge.update_flower({
        "pressure": pressure,
        "future": future
    })

    print("SENSOR UPDATE:", pressure, future)

if __name__ == "__main__":
    simulate_pressure()

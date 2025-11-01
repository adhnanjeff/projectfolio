import can
import time
import random
import asyncio
from config import *

async def main():
    bus = can.interface.Bus(channel=CAN_CHANNEL, interface=CAN_INTERFACE)
    print("🚗 Starting normal CAN traffic generator...")

    try:
        while True:
            # Simulate speed (0–120 km/h)
            speed = random.randint(0, 120)
            speed_msg = can.Message(arbitration_id=CAN_IDS['SPEED'], data=[speed], is_extended_id=False)
            bus.send(speed_msg)
            print(f"🚗 Sent Speed: {speed} km/h")

            # Simulate RPM (800–4000)
            rpm = random.randint(800, 4000)
            rpm_bytes = rpm.to_bytes(2, byteorder='big')
            rpm_msg = can.Message(arbitration_id=CAN_IDS['RPM'], data=rpm_bytes, is_extended_id=False)
            bus.send(rpm_msg)
            print(f"⚙️ Sent RPM: {rpm}")

            # Simulate engine temperature
            temp = random.randint(80, 95)
            temp_msg = can.Message(arbitration_id=CAN_IDS['ENGINE_TEMP'], data=[temp], is_extended_id=False)
            bus.send(temp_msg)
            print(f"🌡️ Sent Temp: {temp}°C")

            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Traffic generator stopped")

if __name__ == "__main__":
    asyncio.run(main())

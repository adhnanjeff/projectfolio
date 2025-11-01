import can
import pandas as pd
import joblib
import csv
import time
import numpy as np
from datetime import datetime
from collections import defaultdict
from config import *

class AdvancedIDS:
    def __init__(self):
        self.model = None
        self.bus = None
        self.load_model()
        self.setup_bus()
        self.message_patterns = {}
        self.attack_signatures = self._init_attack_signatures()
        self.message_history = defaultdict(list)
        self.last_timestamps = {}
        self.window_size = 5.0
        
    def load_model(self):
        """Load the trained IDS model"""
        try:
            self.model = joblib.load(MODEL_FILE)
            print("✅ IDS model loaded successfully.")
        except Exception as e:
            print(f"❌ ERROR loading model: {e}")
            raise
    
    def setup_bus(self):
        """Setup CAN bus connection"""
        try:
            self.bus = can.interface.Bus(channel=CAN_CHANNEL, interface=CAN_INTERFACE)
            print(f"🔗 Connected to CAN bus: {CAN_CHANNEL}")
        except Exception as e:
            print(f"❌ ERROR connecting to CAN bus: {e}")
            raise
    
    def _init_attack_signatures(self):
        """Initialize attack detection signatures"""
        return {
            'DOS': {
                'high_frequency': lambda msgs: len(msgs) > 50,  # >50 msgs in window
                'repeated_id': lambda msgs: self._check_repeated_ids(msgs, threshold=20)
            },
            'FUZZING': {
                'random_ids': lambda msgs: self._check_random_ids(msgs),
                'invalid_data': lambda msgs: self._check_invalid_data(msgs)
            },
            'REPLAY': {
                'exact_duplicates': lambda msgs: self._check_exact_duplicates(msgs),
                'burst_pattern': lambda msgs: self._check_burst_pattern(msgs)
            },
            'SPOOFING': {
                'unrealistic_values': lambda msgs: self._check_unrealistic_values(msgs),
                'value_jumps': lambda msgs: self._check_value_jumps(msgs)
            },
            'FLOODING': {
                'high_rate': lambda msgs: len(msgs) > 30,  # >30 msgs in window
                'multiple_ids': lambda msgs: len(set(m['id'] for m in msgs)) > 5
            }
        }
    
    def extract_features(self, msg):
        """Extract 9 features compatible with simple model"""
        data_bytes = list(msg.data) if msg.data else []
        data_bytes = (data_bytes + [0]*8)[:8]
        return [msg.arbitration_id] + data_bytes
    
    def detect_attack_type(self, msg, recent_messages):
        """Detect specific attack type based on message characteristics"""
        if len(recent_messages) < 2:
            return "NORMAL"
        
        # Check message characteristics for attack type
        msg_id = msg.arbitration_id
        data = list(msg.data) if msg.data else []
        
        # FUZZING: Random IDs or invalid data patterns
        if msg_id not in CAN_IDS.values() or msg_id > 0x7FF:
            return "FUZZING"
        if len(data) == 8 and all(b == 0xFF for b in data):
            return "FUZZING"
        
        # SPOOFING: Unrealistic values
        if msg_id == CAN_IDS['SPEED'] and len(data) > 0 and data[0] > 200:
            return "SPOOFING"
        if msg_id == CAN_IDS['RPM'] and len(data) >= 2:
            rpm = int.from_bytes(data[:2], byteorder='big')
            if rpm > 8000:
                return "SPOOFING"
        if msg_id == CAN_IDS['ENGINE_TEMP'] and len(data) > 0 and data[0] > 120:
            return "SPOOFING"
        
        # DOS/FLOODING: High frequency patterns
        recent_count = len([m for m in recent_messages[-20:] if m['id'] == msg_id])
        if recent_count > 5:  # More sensitive threshold
            return "FLOODING"
        
        # Check overall message rate
        if len(recent_messages) >= 15:  # High overall rate
            return "FLOODING"
        
        # REPLAY: Check for exact duplicates
        msg_signature = (msg_id, tuple(data))
        duplicate_count = len([m for m in recent_messages[-10:] 
                              if (m['id'], tuple(m['data'])) == msg_signature])
        if duplicate_count > 3:
            return "REPLAY"
        
        return "DOS"  # Default for other anomalies
    
    def _check_repeated_ids(self, msgs, threshold):
        """Check for repeated message IDs (DoS indicator)"""
        id_counts = {}
        for msg in msgs:
            id_counts[msg['id']] = id_counts.get(msg['id'], 0) + 1
        return any(count > threshold for count in id_counts.values())
    
    def _check_random_ids(self, msgs):
        """Check for random/unusual CAN IDs (Fuzzing indicator)"""
        known_ids = set(CAN_IDS.values())
        unknown_ids = [msg['id'] for msg in msgs if msg['id'] not in known_ids]
        return len(unknown_ids) > len(msgs) * 0.3  # >30% unknown IDs
    
    def _check_invalid_data(self, msgs):
        """Check for invalid/malformed data (Fuzzing indicator)"""
        invalid_count = 0
        for msg in msgs:
            # Check for all 0xFF (common fuzzing pattern)
            if all(b == 0xFF for b in msg['data']):
                invalid_count += 1
            # Check for data length anomalies
            elif len(msg['data']) not in [1, 2, 4, 8]:  # Common CAN data lengths
                invalid_count += 1
        return invalid_count > len(msgs) * 0.2  # >20% invalid
    
    def _check_exact_duplicates(self, msgs):
        """Check for exact message duplicates (Replay indicator)"""
        seen = set()
        duplicates = 0
        for msg in msgs:
            msg_signature = (msg['id'], tuple(msg['data']))
            if msg_signature in seen:
                duplicates += 1
            seen.add(msg_signature)
        return duplicates > len(msgs) * 0.4  # >40% duplicates
    
    def _check_burst_pattern(self, msgs):
        """Check for burst patterns (Replay indicator)"""
        if len(msgs) < 10:
            return False
        
        # Check for repeated sequences
        for i in range(len(msgs) - 5):
            sequence = msgs[i:i+3]
            for j in range(i+3, len(msgs) - 2):
                if msgs[j:j+3] == sequence:
                    return True
        return False
    
    def _check_unrealistic_values(self, msgs):
        """Check for unrealistic sensor values (Spoofing indicator)"""
        unrealistic_count = 0
        for msg in msgs:
            if msg['id'] == CAN_IDS['SPEED'] and len(msg['data']) > 0:
                if msg['data'][0] > 200:  # >200 km/h
                    unrealistic_count += 1
            elif msg['id'] == CAN_IDS['RPM'] and len(msg['data']) >= 2:
                rpm = int.from_bytes(msg['data'][:2], byteorder='big')
                if rpm > 8000:  # >8000 RPM
                    unrealistic_count += 1
            elif msg['id'] == CAN_IDS['ENGINE_TEMP'] and len(msg['data']) > 0:
                if msg['data'][0] > 120:  # >120°C
                    unrealistic_count += 1
        
        return unrealistic_count > len(msgs) * 0.3  # >30% unrealistic
    
    def _check_value_jumps(self, msgs):
        """Check for sudden value jumps (Spoofing indicator)"""
        # Group by message ID
        id_groups = {}
        for msg in msgs:
            if msg['id'] not in id_groups:
                id_groups[msg['id']] = []
            id_groups[msg['id']].append(msg)
        
        # Check for jumps in each group
        for msg_id, group in id_groups.items():
            if len(group) < 3:
                continue
            
            if msg_id == CAN_IDS['SPEED']:
                values = [msg['data'][0] if msg['data'] else 0 for msg in group]
                for i in range(1, len(values)):
                    if abs(values[i] - values[i-1]) > 50:  # >50 km/h jump
                        return True
        
        return False
    
    def _decode_message(self, msg):
        """Decode CAN message to semantic values"""
        decoded = {}
        data = list(msg.data) if msg.data else []
        
        if msg.arbitration_id == CAN_IDS['SPEED'] and len(data) >= 1:
            decoded['speed'] = data[0]
        elif msg.arbitration_id == CAN_IDS['RPM'] and len(data) >= 2:
            decoded['rpm'] = int.from_bytes(data[:2], byteorder='big')
        elif msg.arbitration_id == CAN_IDS['ENGINE_TEMP'] and len(data) >= 1:
            decoded['engine_temp'] = data[0]
        
        return decoded
    
    def _calc_interarrival(self, msg_id, now):
        """Calculate interarrival time"""
        if msg_id in self.last_timestamps:
            interarrival = (now - self.last_timestamps[msg_id]) * 1000
        else:
            interarrival = 0
        self.last_timestamps[msg_id] = now
        return interarrival
    
    def _calc_rate_features(self, msg_id, now):
        """Calculate message rate features"""
        recent = [m for m in self.message_history[msg_id] if now - m['timestamp'] <= 1.0]
        return {'msg_rate_1s': len(recent)}
    
    def _calc_window_stats(self, msg_id, decoded, now):
        """Calculate sliding window statistics"""
        # Add current message
        self.message_history[msg_id].append({
            'timestamp': now,
            'speed': decoded.get('speed'),
            'rpm': decoded.get('rpm')
        })
        
        # Keep only recent messages
        cutoff = now - self.window_size
        self.message_history[msg_id] = [
            m for m in self.message_history[msg_id] if m['timestamp'] > cutoff
        ]
        
        recent = self.message_history[msg_id]
        stats = {}
        
        # Speed statistics
        speeds = [m['speed'] for m in recent if m['speed'] is not None]
        if speeds:
            stats['speed_mean'] = np.mean(speeds)
            stats['speed_std'] = np.std(speeds) if len(speeds) > 1 else 0
            if len(speeds) >= 2:
                stats['delta_speed'] = speeds[-1] - speeds[-2]
        
        # RPM statistics
        rpms = [m['rpm'] for m in recent if m['rpm'] is not None]
        if rpms:
            stats['rpm_mean'] = np.mean(rpms)
            stats['rpm_std'] = np.std(rpms) if len(rpms) > 1 else 0
            if len(rpms) >= 2:
                stats['delta_rpm'] = rpms[-1] - rpms[-2]
        
        return stats
    
    def log_detection(self, msg, prediction, attack_type, confidence=None):
        """Log detection results with consistent format"""
        try:
            file_exists = False
            try:
                with open(LOG_FILE, 'r'):
                    file_exists = True
            except FileNotFoundError:
                pass
            
            with open(LOG_FILE, 'a', newline='') as f:
                writer = csv.writer(f, quoting=csv.QUOTE_ALL)
                if not file_exists:
                    headers = ['timestamp', 'id', 'data', 'prediction', 'attack_type', 'confidence']
                    writer.writerow(headers)
                
                now = time.time()
                
                writer.writerow([
                    datetime.fromtimestamp(now).isoformat(),
                    f"0x{msg.arbitration_id:03X}",
                    msg.data.hex() if msg.data else "",
                    "Anomaly" if prediction == -1 else "Normal",
                    attack_type,
                    confidence or "N/A"
                ])
        except Exception as e:
            print(f"⚠️ Logging error: {e}")
    
    def monitor(self):
        """Main monitoring loop"""
        print("🔍 Advanced IDS monitoring CAN traffic... Press Ctrl+C to stop.")
        
        recent_messages = []  # Keep last 100 messages for pattern analysis
        message_window = 100
        
        try:
            while True:
                msg = self.bus.recv(timeout=RECV_TIMEOUT)
                if msg:
                    # Add to recent messages
                    msg_data = {
                        'timestamp': time.time(),
                        'id': msg.arbitration_id,
                        'data': list(msg.data)
                    }
                    recent_messages.append(msg_data)
                    
                    # Keep only recent messages
                    if len(recent_messages) > message_window:
                        recent_messages.pop(0)
                    
                    # ML-based anomaly detection
                    features = self.extract_features(msg)
                    X = pd.DataFrame([features])
                    
                    try:
                        prediction = self.model.predict(X)[0]  # -1 = anomaly, 1 = normal
                        
                        # Pattern-based attack type detection
                        attack_type = "NORMAL"
                        if prediction == -1:
                            attack_type = self.detect_attack_type(msg, recent_messages)
                        
                        # Log the detection
                        self.log_detection(msg, prediction, attack_type)
                        
                        # Print results
                        if prediction == -1:
                            icon = ATTACK_TYPES.get(attack_type, {}).get('icon', '🚨')
                            print(f"{icon} ALERT! {attack_type} detected: ID=0x{msg.arbitration_id:03X}, Data={list(msg.data)}")
                        else:
                            print(f"✅ Normal: ID=0x{msg.arbitration_id:03X}, Data={list(msg.data)}")
                            
                    except Exception as e:
                        print(f"⚠️ Prediction error: {e}")
                        
                else:
                    print("⏳ No CAN traffic detected...")
                    
        except KeyboardInterrupt:
            print("\n🛑 IDS monitoring stopped")
        except Exception as e:
            print(f"❌ IDS error: {e}")

def main():
    try:
        ids = AdvancedIDS()
        ids.monitor()
    except Exception as e:
        print(f"❌ Failed to start IDS: {e}")

if __name__ == "__main__":
    main()



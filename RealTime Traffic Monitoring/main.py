import streamlit as st
import cv2
from ultralytics import YOLO
import cvzone
from sort import *
import time
import pandas as pd
import os
from dotenv import load_dotenv
import requests
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
class Config:
    TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
    TWILIO_FROM_NUMBER = os.getenv('TWILIO_FROM_NUMBER')
    TWILIO_TO_NUMBER = os.getenv('TWILIO_TO_NUMBER')
    YOLO_CUSTOM_MODEL = os.getenv('YOLO_CUSTOM_MODEL_PATH', '../Yolo-Weights/best-2.pt')
    YOLO_STANDARD_MODEL = os.getenv('YOLO_STANDARD_MODEL_PATH', '../Yolo-Weights/yolov8l.pt')

# Load models and assets only once
@st.cache_resource
def load_models_and_assets():
    try:
        model = YOLO(Config.YOLO_CUSTOM_MODEL)
        model2 = YOLO(Config.YOLO_STANDARD_MODEL)
        classNames = list(model.names.values())
        mask1 = cv2.imread("Masks/mask.png")
        mask2 = cv2.imread("Masks/mask3.png")
        
        if mask1 is None or mask2 is None:
            st.error("❌ Failed to load mask images. Please check Masks/ directory.")
            st.stop()
            
        return model, model2, classNames, mask1, mask2
    except Exception as e:
        st.error(f"❌ Failed to load models: {e}")
        st.stop()

# Emergency services integration
def get_location():
    """Get current location using IP geolocation"""
    try:
        response = requests.get('https://ipinfo.io/json', timeout=5)
        data = response.json()
        return {
            'coordinates': data.get('loc', ''),
            'city': data.get('city', ''),
            'region': data.get('region', ''),
            'country': data.get('country', '')
        }
    except Exception as e:
        logger.error(f"Location retrieval failed: {e}")
        return None

def send_emergency_alert(location_data):
    """Send emergency alert via Twilio"""
    if not all([Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN, 
                Config.TWILIO_FROM_NUMBER, Config.TWILIO_TO_NUMBER]):
        st.warning("⚠️ Twilio credentials not configured. Emergency alerts disabled.")
        return False
        
    try:
        client = Client(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)
        
        if location_data:
            location_text = f"{location_data['city']}, {location_data['region']}, {location_data['country']} at coordinates {location_data['coordinates']}"
        else:
            location_text = "Location unavailable"
            
        response = VoiceResponse()
        response.say(f"Emergency: Accident detected at {location_text}. Immediate assistance required.", voice='alice')
        
        call = client.calls.create(
            twiml=str(response),
            to=Config.TWILIO_TO_NUMBER,
            from_=Config.TWILIO_FROM_NUMBER
        )
        
        st.success(f"🚨 Emergency alert sent! Call SID: {call.sid}")
        logger.info(f"Emergency call initiated: {call.sid}")
        return True
        
    except Exception as e:
        st.error(f"❌ Emergency alert failed: {e}")
        logger.error(f"Twilio call failed: {e}")
        return False

model, model2, classNames, mask1, mask2 = load_models_and_assets()

# Session state initialization
if 'cap1' not in st.session_state:
    st.session_state.cap1 = cv2.VideoCapture("video/Video.mp4")
    st.session_state.cap2 = cv2.VideoCapture("video/accident.mp4")
    st.session_state.tracker1 = Sort(max_age=20, min_hits=3, iou_threshold=0.3)
    st.session_state.tracker2 = Sort(max_age=20, min_hits=3, iou_threshold=0.3)
    st.session_state.totalCount1 = []
    st.session_state.totalCount2 = []
    st.session_state.count1 = 0
    st.session_state.count2 = 0
    st.session_state.emergency_sent = False
    st.session_state.detection_stats = {'total_vehicles': 0, 'accidents': 0, 'priority_vehicles': 0}

# UI Configuration
st.set_page_config(
    page_title="Smart Traffic Management",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for enhanced UI
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .emergency-alert {
        background: linear-gradient(90deg, #ff4444, #cc0000);
        color: white;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        font-weight: bold;
        animation: pulse 2s infinite;
    }
    .priority-alert {
        background: linear-gradient(90deg, #ffaa00, #ff8800);
        color: white;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        font-weight: bold;
    }
    .normal-status {
        background: linear-gradient(90deg, #00aa44, #008833);
        color: white;
        padding: 10px;
        border-radius: 10px;
        text-align: center;
    }
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.7; }
        100% { opacity: 1; }
    }
    .stButton > button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 20px;
        padding: 0.5rem 2rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Main header
st.markdown("""
<div class="main-header">
    <h1>🚦 Smart Traffic Management & Emergency Response System</h1>
    <p>Real-time Vehicle Detection with AI-Powered Priority Lane Management</p>
</div>
""", unsafe_allow_html=True)

# Sidebar controls with enhanced styling
with st.sidebar:
    st.markdown("### 🎛️ System Controls")
    
    with st.expander("🔧 Detection Settings", expanded=True):
        detection_sensitivity = st.slider(
            "Detection Sensitivity", 
            0.1, 0.9, 0.3, 0.1,
            help="Higher values = more sensitive detection"
        )
        show_debug_info = st.checkbox("Show Debug Info", False)
        emergency_mode = st.checkbox("Emergency Alerts Enabled", True)
    
    with st.expander("📹 Video Controls", expanded=True):
        video_speed = st.selectbox(
            "Playback Speed",
            ["0.5x", "1x", "1.5x", "2x"],
            index=1
        )
        loop_video = st.checkbox("Loop Video", True)
    
    st.markdown("### 📊 Live Statistics")
    stats_placeholder = st.empty()
    
    st.markdown("### 🚨 System Status")
    status_placeholder = st.empty()

col1, col2 = st.columns(2)

# Function to process frame
def process_frame(img, tracker, totalCount, count, mask, show_lines=True, counting_enabled=True):
    mask_resized = cv2.resize(mask, (img.shape[1], img.shape[0]))
    imgRegion = cv2.bitwise_and(img, mask_resized)
    height, width = img.shape[:2]

    entry_line_y = int(height * 0.65)
    exit_line_y = int(height * 0.95)

    results1 = model(imgRegion, stream=True)
    results2 = model2(imgRegion, stream=True)

    detections = np.empty((0, 5))
    lane_priority_active = False
    accident_active = False

    for r in results1:
        for box in r.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            conf = float(box.conf[0])
            cls = int(box.cls[0])
            currentClass = classNames[cls]

            if currentClass == "accident" and conf > 0.3:
                accident_active = True
                detections = np.vstack((detections, [x1, y1, x2, y2, conf]))
            if currentClass in ["ambulance_active", "firetruck_active", "police_active"] and conf > 0.3:
                lane_priority_active = True
                detections = np.vstack((detections, [x1, y1, x2, y2, conf]))
            if currentClass in ["car", "truck", "bus", "motorbike"] and conf > 0.3:
                detections = np.vstack((detections, [x1, y1, x2, y2, conf]))

    for r in results2:
        for box in r.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            conf = float(box.conf[0])
            if conf > 0.5:
                detections = np.vstack((detections, [x1, y1, x2, y2, conf]))

    resultsTracker = tracker.update(detections)

    if show_lines:
        cv2.line(img, (0, entry_line_y), (width, entry_line_y), (255, 255, 0), 4)
        cv2.line(img, (0, exit_line_y), (width, exit_line_y), (255, 0, 255), 4)

    if counting_enabled and show_lines:
        for result in resultsTracker:
            x1, y1, x2, y2, Id = map(int, result)
            cx, cy = x1 + (x2 - x1) // 2, y1 + (y2 - y1) // 2
            cvzone.cornerRect(img, (x1, y1, x2 - x1, y2 - y1), l=9, rt=2, colorR=(0, 0, 255))
            cvzone.putTextRect(img, f'ID {Id}', (max(0, x1), max(35, y1)), scale=1, thickness=2, offset=6)

            if entry_line_y - 10 < cy < entry_line_y + 10 and Id not in totalCount:
                totalCount.append(Id)
                count += 1
                cv2.line(img, (0, entry_line_y), (width, entry_line_y), (0, 255, 0), 4)
            if exit_line_y - 10 < cy < exit_line_y + 10 and Id in totalCount:
                totalCount.remove(Id)
                count -= 1
                cv2.line(img, (0, exit_line_y), (width, exit_line_y), (0, 0, 255), 4)
    else:
        for result in resultsTracker:
            x1, y1, x2, y2, Id = map(int, result)
            cvzone.cornerRect(img, (x1, y1, x2 - x1, y2 - y1), l=9, rt=2, colorR=(0, 0, 255))
            cvzone.putTextRect(img, f'ID {Id}', (max(0, x1), max(35, y1)), scale=1, thickness=2, offset=6)

    return img, tracker, totalCount, count, lane_priority_active, accident_active

# Placeholders for live update
frame_placeholder1 = col1.empty()
frame_placeholder2 = col2.empty()
priority_placeholder1 = col1.empty()
priority_placeholder2 = col2.empty()
table_placeholder = st.empty()

# Enhanced video controls
control_col1, control_col2, control_col3 = st.columns([2, 1, 1])

with control_col1:
    play = st.button("▶️ Start Traffic Monitoring" if 'play' not in st.session_state or not st.session_state.play else "⏸️ Pause Monitoring", 
                    type="primary", use_container_width=True)
    if play:
        st.session_state.play = not st.session_state.get('play', False)

with control_col2:
    if st.button("🔄 Reset System", use_container_width=True):
        st.session_state.clear()
        st.rerun()

with control_col3:
    if st.button("📊 Export Data", use_container_width=True):
        st.info("📁 Data export feature coming soon!")

play_active = st.session_state.get('play', False)

if play_active:
    while st.session_state.cap1.isOpened() and st.session_state.cap2.isOpened():
        ret1, frame1 = st.session_state.cap1.read()
        ret2, frame2 = st.session_state.cap2.read()

        if not ret1 or not ret2:
            st.warning("🎮 End of video reached.")
            break

        frame1 = cv2.resize(frame1, (720, 640))
        frame2 = cv2.resize(frame2, (720, 640))

        img1, st.session_state.tracker1, st.session_state.totalCount1, st.session_state.count1, priority1, accident1 = process_frame(
            frame1, st.session_state.tracker1, st.session_state.totalCount1, st.session_state.count1, mask1, show_lines=True, counting_enabled=True)

        img2, st.session_state.tracker2, st.session_state.totalCount2, st.session_state.count2, priority2, accident2 = process_frame(
            frame2, st.session_state.tracker2, st.session_state.totalCount2, st.session_state.count2, mask2, show_lines=False, counting_enabled=False)

        img1 = cv2.cvtColor(img1, cv2.COLOR_BGR2RGB)
        img2 = cv2.cvtColor(img2, cv2.COLOR_BGR2RGB)

        frame_placeholder1.image(img1, channels="RGB", caption=f"Lane 1 Count: {st.session_state.count1}", use_container_width=True)
        frame_placeholder2.image(img2, channels="RGB", caption=f"Lane 2 Count: {st.session_state.count2}", use_container_width=True)

        # Handle emergency situations
        if (accident1 or accident2) and emergency_mode and not st.session_state.emergency_sent:
            location_data = get_location()
            if send_emergency_alert(location_data):
                st.session_state.emergency_sent = True
                st.session_state.detection_stats['accidents'] += 1

        # Enhanced priority/emergency alerts
        if accident1:
            priority_placeholder1.markdown(
                '<div class="emergency-alert">🆘 EMERGENCY - ACCIDENT DETECTED!</div>', 
                unsafe_allow_html=True
            )
        elif priority1:
            priority_placeholder1.markdown(
                '<div class="priority-alert">🚨 PRIORITY LANE 1 ACTIVE</div>', 
                unsafe_allow_html=True
            )
            st.session_state.detection_stats['priority_vehicles'] += 1
        else:
            priority_placeholder1.markdown(
                '<div class="normal-status">✅ Lane 1 - Normal Traffic</div>', 
                unsafe_allow_html=True
            )

        if accident2:
            priority_placeholder2.markdown(
                '<div class="emergency-alert">🆘 EMERGENCY - ACCIDENT DETECTED!</div>', 
                unsafe_allow_html=True
            )
        elif priority2:
            priority_placeholder2.markdown(
                '<div class="priority-alert">🚨 PRIORITY LANE 2 ACTIVE</div>', 
                unsafe_allow_html=True
            )
        else:
            priority_placeholder2.markdown(
                '<div class="normal-status">✅ Lane 2 - Normal Traffic</div>', 
                unsafe_allow_html=True
            )

        # Update statistics
        st.session_state.detection_stats['total_vehicles'] = st.session_state.count1 + st.session_state.count2
        
        # Enhanced metrics and status table
        st.markdown("### 📊 Traffic Management Dashboard")
        
        # Metrics row
        metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
        
        with metric_col1:
            st.metric(
                "🚗 Total Vehicles", 
                st.session_state.detection_stats['total_vehicles'],
                delta=st.session_state.count1 + st.session_state.count2 - st.session_state.detection_stats.get('prev_total', 0)
            )
        
        with metric_col2:
            st.metric(
                "🚨 Lane 1 Count", 
                st.session_state.count1,
                delta=st.session_state.count1 - st.session_state.detection_stats.get('prev_count1', 0)
            )
        
        with metric_col3:
            st.metric(
                "🚨 Lane 2 Count", 
                st.session_state.count2,
                delta=st.session_state.count2 - st.session_state.detection_stats.get('prev_count2', 0)
            )
        
        with metric_col4:
            st.metric(
                "🆘 Emergencies", 
                st.session_state.detection_stats['accidents'],
                delta=1 if (accident1 or accident2) and not st.session_state.emergency_sent else 0
            )
        
        # Enhanced status table
        priority_data = {
            "🛣️ Lane": ["Lane 1", "Lane 2"],
            "🚗 Vehicles": [st.session_state.count1, st.session_state.count2],
            "📊 Status": [
                "🆘 EMERGENCY" if accident1 else "🚨 PRIORITY" if priority1 else "✅ Normal",
                "🆘 EMERGENCY" if accident2 else "🚨 PRIORITY" if priority2 else "✅ Normal"
            ],
            "⚡ Action": [
                "🛑 Stop All Traffic" if accident1 else "⚡ Give Priority" if priority1 else "➡️ Continue",
                "🛑 Stop All Traffic" if accident2 else "⚡ Give Priority" if priority2 else "➡️ Continue"
            ],
            "⏱️ Duration": ["Real-time", "Real-time"]
        }
        
        df = pd.DataFrame(priority_data)
        table_placeholder.dataframe(
            df, 
            use_container_width=True,
            hide_index=True
        )
        
        # Update previous values for delta calculation
        st.session_state.detection_stats['prev_total'] = st.session_state.detection_stats['total_vehicles']
        st.session_state.detection_stats['prev_count1'] = st.session_state.count1
        st.session_state.detection_stats['prev_count2'] = st.session_state.count2
        
        # Update sidebar statistics with enhanced styling
        with stats_placeholder.container():
            st.markdown("#### 📈 Performance Metrics")
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("🚗 Total", st.session_state.detection_stats['total_vehicles'])
                st.metric("🚨 Priority", st.session_state.detection_stats['priority_vehicles'])
            
            with col2:
                st.metric("🆘 Accidents", st.session_state.detection_stats['accidents'])
                st.metric("⚡ Active Lanes", 2)
        
        # System status in sidebar
        with status_placeholder.container():
            if accident1 or accident2:
                st.error("🆘 EMERGENCY ACTIVE")
            elif priority1 or priority2:
                st.warning("🚨 PRIORITY MODE")
            else:
                st.success("✅ NORMAL OPERATION")
            
            st.info(f"🔄 Emergency Alerts: {'ON' if emergency_mode else 'OFF'}")
            
        if show_debug_info:
            st.sidebar.subheader("🔧 Debug Info")
            st.sidebar.json({
                "Lane 1 IDs": st.session_state.totalCount1,
                "Lane 2 IDs": st.session_state.totalCount2,
                "Emergency Sent": st.session_state.emergency_sent
            })

        time.sleep(0.03)

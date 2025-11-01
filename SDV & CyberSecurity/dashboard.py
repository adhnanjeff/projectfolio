import streamlit as st
import pandas as pd
import os
import time
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import ast
from config import *
from attack_engine_sync import AttackEngine

st.set_page_config(
    page_title=DASHBOARD_TITLE, 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize attack engine
if 'attack_engine' not in st.session_state:
    try:
        st.session_state.attack_engine = AttackEngine()
    except Exception as e:
        st.error(f"Failed to initialize attack engine: {e}")
        st.stop()

# Custom CSS for better styling
st.markdown("""
<style>
.metric-card {
    background-color: #f0f2f6;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 4px solid #1f77b4;
}
.attack-card {
    padding: 1rem;
    border-radius: 0.5rem;
    margin: 0.5rem 0;
}
.dos-card { border-left: 4px solid #FF4B4B; }
.fuzzing-card { border-left: 4px solid #FF8C00; }
.replay-card { border-left: 4px solid #9932CC; }
.spoofing-card { border-left: 4px solid #DC143C; }
.flooding-card { border-left: 4px solid #B22222; }
.normal-card { border-left: 4px solid #32CD32; }
</style>
""", unsafe_allow_html=True)

st.title(DASHBOARD_TITLE)
st.markdown("**Real-time CAN Bus Security Monitoring & Attack Simulation**")

# Sidebar for attack controls
with st.sidebar:
    st.header("🎯 Attack Control Panel")
    
    # Attack type selection
    attack_types = [k for k in ATTACK_TYPES.keys() if k not in ["NORMAL", "DOS"]]
    selected_attack = st.selectbox(
        "Select Attack Type",
        attack_types,
        format_func=lambda x: f"{ATTACK_TYPES[x]['icon']} {ATTACK_TYPES[x]['name']}"
    )
    
    # Attack duration
    duration = st.number_input("Duration (seconds)", min_value=1, max_value=300, value=30)
    
    # Attack controls
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 Start Attack", type="primary"):
            st.session_state.attack_engine.start_attack(selected_attack, duration)
            st.success(f"Started {ATTACK_TYPES[selected_attack]['name']}")
    
    with col2:
        if st.button("🛑 Stop Attack", type="secondary"):
            st.session_state.attack_engine.stop_attack()
            st.info("Attack stopped")
    
    # Attack status
    status = st.session_state.attack_engine.get_attack_status()
    if status['is_attacking']:
        st.error(f"🚨 Active: {status['current_attack']}")
        st.metric("Messages Sent", status['messages_sent'])
    else:
        st.success("✅ No active attacks")
    
    # Clear history
    if st.button("Clear History"):
        st.session_state.attack_engine.clear_history()
        st.info("History cleared")

# Main dashboard
col1, col2, col3 = st.columns([2, 2, 1])

# Wait for log file
if not os.path.exists(LOG_FILE):
    st.warning("⚠️ Waiting for IDS to create log file. Make sure `ids.py` is running.")
    time.sleep(2)
    st.rerun()

# Load and process data
try:
    # Handle inconsistent CSV format
    df = pd.read_csv(LOG_FILE, on_bad_lines='skip', low_memory=False)
    if len(df) == 0:
        raise ValueError("Empty log file")
except Exception as e:
    st.error(f"Could not read log file: {e}")
    if st.button("Clear Log File"):
        import os
        if os.path.exists(LOG_FILE):
            os.remove(LOG_FILE)
            st.success("Log file cleared. Restart IDS to create new log.")
            st.rerun()
    st.stop()

if len(df) == 0:
    st.info("No CAN data available yet. Waiting for traffic...")
    time.sleep(REFRESH_INTERVAL)
    st.rerun()

# Handle log format
if 'timestamp' in df.columns:
    df['timestamp'] = pd.to_datetime(df['timestamp'])
else:
    df['timestamp'] = pd.to_datetime(df.index)

# Ensure attack_type column exists
if 'attack_type' not in df.columns:
    df['attack_type'] = 'NORMAL'
    df.loc[df['prediction'] == 'Anomaly', 'attack_type'] = 'DOS'

df = df.sort_values('timestamp').tail(1000)

# Add attack type colors and icons
def get_attack_style(attack_type):
    return ATTACK_TYPES.get(attack_type, ATTACK_TYPES['NORMAL'])

df['color'] = df['attack_type'].apply(lambda x: get_attack_style(x)['color'])
df['icon'] = df['attack_type'].apply(lambda x: get_attack_style(x)['icon'])
df['attack_display'] = df.apply(lambda row: f"{row['icon']} {row['attack_type']}", axis=1)

# Metrics row
with col1:
    total_messages = len(df)
    anomalies = len(df[df['prediction'] == 'Anomaly'])
    st.metric("Total Messages", total_messages)

with col2:
    st.metric("Anomalies Detected", anomalies, delta=f"{(anomalies/total_messages*100):.1f}%" if total_messages > 0 else "0%")

with col3:
    recent_anomalies = len(df[(df['timestamp'] > datetime.now() - timedelta(minutes=5)) & (df['prediction'] == 'Anomaly')])
    st.metric("Recent (5min)", recent_anomalies)

# Attack type distribution
st.subheader("📈 Attack Type Distribution")
attack_counts = df['attack_type'].value_counts()

if len(attack_counts) > 0:
    # Create color mapping with fallbacks
    color_map = {k: v['color'] for k, v in ATTACK_TYPES.items()}
    for attack_type in attack_counts.index:
        if attack_type not in color_map:
            color_map[attack_type] = '#808080'
    
    fig_pie = px.pie(
        values=attack_counts.values,
        names=attack_counts.index,
        title="Attack Types Distribution",
        color=attack_counts.index,
        color_discrete_map=color_map
    )
    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig_pie, width='stretch')
else:
    st.info("No attack data available yet.")

# Timeline visualization
st.subheader("🕰️ Attack Timeline")
if len(df) > 0:
    # Group by minute for timeline
    df['minute'] = df['timestamp'].dt.floor('min')
    timeline_data = df.groupby(['minute', 'attack_type']).size().reset_index(name='count')
    
    fig_timeline = px.bar(
        timeline_data,
        x='minute',
        y='count',
        color='attack_type',
        title="Attacks Over Time",
        color_discrete_map={k: v['color'] for k, v in ATTACK_TYPES.items()}
    )
    fig_timeline.update_layout(xaxis_title="Time", yaxis_title="Message Count")
    st.plotly_chart(fig_timeline, width='stretch')

# Live traffic feed
st.subheader("📡 Live CAN Traffic Feed")

# Filter options
col1, col2, col3 = st.columns(3)
with col1:
    show_normal = st.checkbox("Show Normal Traffic", value=False)
with col2:
    selected_types = st.multiselect(
        "Filter Attack Types",
        options=list(ATTACK_TYPES.keys()),
        default=[k for k in ATTACK_TYPES.keys() if k != "NORMAL"]
    )
with col3:
    max_rows = st.slider("Max Rows", 10, 100, MAX_DISPLAY_ROWS)

# Apply filters
filtered_df = df.copy()
if not show_normal:
    filtered_df = filtered_df[filtered_df['prediction'] == 'Anomaly']
if selected_types:
    filtered_df = filtered_df[filtered_df['attack_type'].isin(selected_types)]

# Display table with styling
if len(filtered_df) > 0:
    # Use available columns
    cols_to_show = ['timestamp', 'id', 'data', 'attack_display', 'prediction']
    available_cols = [col for col in cols_to_show if col in filtered_df.columns]
    display_df = filtered_df[available_cols].tail(max_rows)
    
    # Rename columns
    col_mapping = {
        'timestamp': 'Timestamp',
        'id': 'CAN ID', 
        'data': 'Data',
        'attack_display': 'Attack Type',
        'prediction': 'Status'
    }
    display_df = display_df.rename(columns=col_mapping)
    
    # Style the dataframe
    def style_row(row):
        attack_type = row['Attack Type'].split(' ', 1)[1] if ' ' in row['Attack Type'] else 'NORMAL'
        color = ATTACK_TYPES.get(attack_type, ATTACK_TYPES['NORMAL'])['color']
        return [f'background-color: {color}20'] * len(row)  # 20 for transparency
    
    styled_df = display_df.style.apply(style_row, axis=1)
    st.dataframe(styled_df, width='stretch', height=400)
else:
    st.info("No messages match the current filters.")

# Attack details panel
if len(df[df['prediction'] == 'Anomaly']) > 0:
    st.subheader("🔍 Attack Analysis")
    
    # Recent attacks summary
    recent_df = df[df['timestamp'] > datetime.now() - timedelta(minutes=10)]
    recent_attacks = recent_df[recent_df['prediction'] == 'Anomaly']
    
    if len(recent_attacks) > 0:
        attack_summary = recent_attacks['attack_type'].value_counts()
        
        cols = st.columns(len(attack_summary))
        for i, (attack_type, count) in enumerate(attack_summary.items()):
            with cols[i % len(cols)]:
                style_info = ATTACK_TYPES.get(attack_type, ATTACK_TYPES['NORMAL'])
                st.markdown(f"""
                <div class="attack-card {attack_type.lower()}-card">
                    <h4>{style_info['icon']} {style_info['name']}</h4>
                    <p><strong>{count}</strong> attacks in last 10 min</p>
                </div>
                """, unsafe_allow_html=True)

# Auto-refresh
time.sleep(REFRESH_INTERVAL)
st.rerun()
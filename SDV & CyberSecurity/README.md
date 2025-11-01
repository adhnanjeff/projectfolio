# 🚗 Advanced CAN Bus Intrusion Detection System (IDS)

A comprehensive real-time CAN Bus security monitoring and attack simulation system with machine learning-based intrusion detection and **Simulink integration support**.

## 🌟 Features

### 🛡️ Advanced IDS Capabilities
- **Real-time Monitoring**: Continuous CAN bus traffic analysis
- **ML-based Detection**: Isolation Forest algorithm for anomaly detection
- **Attack Classification**: Identifies specific attack types (DoS, Fuzzing, Replay, Spoofing, Flooding)
- **Pattern Analysis**: Advanced signature-based attack detection
- **Performance Metrics**: Comprehensive model evaluation and statistics

### 🎯 Attack Simulation Engine
- **Multiple Attack Types**:
  - **DoS (Denial of Service)**: High-frequency message flooding
  - **Fuzzing**: Random/malformed data injection
  - **Replay**: Captured message replay attacks
  - **Spoofing**: Fake sensor value injection
  - **Flooding**: Bus overwhelming with legitimate-looking messages
- **Manual Control**: Start/stop attacks with custom duration
- **Real-time Feedback**: Live attack status and message counting

### 📊 Interactive Dashboard
- **Real-time Visualization**: Live CAN traffic monitoring
- **Attack Control Panel**: Manual attack simulation controls
- **Timeline Analysis**: Attack patterns over time
- **Attack Distribution**: Pie charts and statistics
- **Filtering Options**: Customizable data views
- **Color-coded Alerts**: Visual attack type identification

### 🔗 Simulink Integration (NEW!)
- **TCP/IP Interface**: Real-time communication with Simulink
- **Data Converters**: Seamless format conversion
- **Model Export**: Export trained ML models for Simulink
- **Hardware-in-Loop**: Support for real ECU testing
- **Vehicle Dynamics**: Integration with vehicle simulation models

## 🚀 Quick Start

### 1. Setup Virtual CAN Interface
```bash
# Create virtual CAN interface (Linux/macOS)
sudo modprobe vcan
sudo ip link add dev vcan0 type vcan
sudo ip link set up vcan0

# Verify interface
ip link show vcan0
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Train the IDS Model
```bash
python train_ids.py
```

### 4. Start the System

**Terminal 1 - Start IDS Monitoring:**
```bash
python ids.py
```

**Terminal 2 - Launch Dashboard:**
```bash
streamlit run dashboard.py
```

**Terminal 3 - Generate Normal Traffic (optional):**
```bash
python sender.py
```

**Terminal 4 - Manual Attack Control:**
```bash
python attack_engine.py
```

**Terminal 5 - Simulink Interface (optional):**
```bash
python simulink_interface.py
```

## 🎮 Usage Guide

### Dashboard Controls
1. **Attack Selection**: Choose from 5 different attack types
2. **Duration Setting**: Set attack duration (1-300 seconds)
3. **Start/Stop**: Manual attack control buttons
4. **Real-time Monitoring**: Live traffic feed with filtering
5. **Analytics**: Attack distribution and timeline charts

### Attack Engine Commands
```bash
# Start specific attack
> start DOS 30        # DoS attack for 30 seconds
> start FUZZING 60    # Fuzzing attack for 60 seconds
> start SPOOFING      # Spoofing attack (indefinite)

# Stop current attack
> stop

# Check status
> status

# Exit
> quit
```

### Simulink Integration
```matlab
% In Simulink Command Window
simulink_config  % Load configuration

% Connect to Python IDS via TCP/IP
% Use TCP/IP blocks with localhost:8888
```

### Attack Types Explained

#### 🔥 DoS (Denial of Service)
- Floods critical CAN IDs with high-priority messages
- Overwhelms ECUs with excessive traffic
- **Detection**: High message frequency, repeated IDs

#### 🎯 Fuzzing
- Sends random/malformed CAN messages
- Tests system robustness with invalid data
- **Detection**: Unknown IDs, invalid data patterns

#### 🔄 Replay
- Captures legitimate messages and replays them
- Can cause unintended system behavior
- **Detection**: Exact duplicates, burst patterns

#### 🎭 Spoofing
- Injects fake but realistic sensor values
- Dangerous speed, RPM, temperature values
- **Detection**: Unrealistic values, sudden jumps

#### 🌊 Flooding
- Overwhelms bus with legitimate-looking messages
- High-rate transmission of normal-format data
- **Detection**: High message rate, multiple IDs

## 📁 Project Structure

```
AI Agents/
├── config.py              # System configuration
├── attack_engine.py       # Advanced attack simulation
├── ids.py                 # Enhanced IDS with attack classification
├── dashboard.py           # Interactive Streamlit dashboard
├── train_ids.py           # ML model training with evaluation
├── sender.py              # Normal traffic generator
├── receiver.py            # Basic CAN message receiver
├── logger.py              # Traffic logging utility
├── simulink_interface.py  # Simulink TCP/IP interface (NEW!)
├── simulink_converter.py  # Data format converters (NEW!)
├── simulink_config.m      # MATLAB/Simulink configuration (NEW!)
├── requirements.txt       # Python dependencies
├── setup.py              # Automated setup script
└── README.md             # This file
```

## 🔧 Configuration

Edit `config.py` to customize:
- CAN interface settings
- Attack parameters
- Dashboard refresh rates
- File paths
- ML model parameters
- Simulink integration settings

## 📊 Model Performance

The IDS uses Isolation Forest with:
- **Contamination Rate**: 10% (configurable)
- **Features**: CAN ID + 8-byte data payload
- **Evaluation**: Train/test split with classification reports
- **Metrics**: Precision, Recall, F1-score for attack detection

## 🛠️ Advanced Features

### Custom Attack Development
Extend `AttackEngine` class to add new attack types:
```python
def _custom_attack(self, duration):
    # Your custom attack logic here
    pass
```

### IDS Tuning
Modify detection signatures in `AdvancedIDS._init_attack_signatures()`:
```python
'CUSTOM_ATTACK': {
    'signature_name': lambda msgs: your_detection_logic(msgs)
}
```

### Simulink Model Integration
1. **Start Python Interface**: `python simulink_interface.py`
2. **Load Simulink Config**: Run `simulink_config.m`
3. **Use TCP/IP Blocks**: Connect to localhost:8888
4. **Stream CAN Data**: Send JSON-formatted messages
5. **Receive Results**: Get anomaly detection results

## 🔍 Troubleshooting

### Common Issues
1. **CAN Interface Error**: Ensure vcan0 is created and up
2. **Permission Denied**: Run with appropriate privileges
3. **Module Not Found**: Install requirements.txt
4. **No Traffic**: Start sender.py for test traffic
5. **Dashboard Not Loading**: Check if ids.py is running
6. **Simulink Connection**: Verify TCP port 8888 is available

### Debug Mode
Enable verbose logging by modifying print statements in respective modules.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📝 License

This project is for educational and research purposes. Use responsibly and in compliance with applicable laws and regulations.

## 🙏 Acknowledgments

- CAN Bus protocol specifications
- Scikit-learn machine learning library
- Streamlit dashboard framework
- Python-CAN library for CAN interface support
- MATLAB/Simulink for vehicle dynamics simulation
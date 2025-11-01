# 🚦 Smart Traffic Management & Emergency Response System

A real-time vehicle detection and traffic management system with emergency response capabilities using YOLO object detection and Streamlit.

## ✨ Features

- **Real-time Vehicle Detection**: Detects cars, trucks, buses, and motorcycles
- **Lane Priority Management**: Automatic priority for emergency vehicles (ambulance, fire truck, police)
- **Accident Detection**: AI-powered accident detection with automatic emergency alerts
- **Emergency Response**: Automatic Twilio-based emergency calls with location data
- **Traffic Counting**: Real-time vehicle counting with entry/exit tracking
- **Interactive Dashboard**: Web-based interface with live video feeds and statistics

## 🛠️ Technologies Used

- **Computer Vision**: OpenCV, YOLO (Ultralytics)
- **Object Tracking**: SORT algorithm
- **Web Framework**: Streamlit
- **Emergency Services**: Twilio API
- **Location Services**: IP-based geolocation

## 📋 Prerequisites

- Python 3.8+
- YOLO model weights (place in `../Yolo-Weights/`)
- Twilio account (for emergency alerts)
- Webcam or video files for testing

## 🚀 Quick Start

### Method 1: Automated Setup (Recommended)
```bash
git clone <repository-url>
cd pythonProject
python setup.py
```

### Method 2: Manual Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd pythonProject
   ```

2. **Create virtual environment (recommended)**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```

5. **Configure credentials** (Edit `.env` file)
   ```env
   TWILIO_ACCOUNT_SID=your_account_sid_here
   TWILIO_AUTH_TOKEN=your_auth_token_here
   TWILIO_FROM_NUMBER=+1234567890
   TWILIO_TO_NUMBER=+0987654321
   ```

6. **Download YOLO weights**
   - Create directory: `mkdir -p ../Yolo-Weights`
   - Download models:
     - Custom model: `best-2.pt` (for accident/emergency detection)
     - Standard model: `yolov8l.pt` (for vehicle detection)
   - Place in `../Yolo-Weights/` directory

## ⚙️ Configuration

Create a `.env` file with the following variables:

```env
# Twilio Configuration
TWILIO_ACCOUNT_SID=your_account_sid_here
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_FROM_NUMBER=your_twilio_phone_number
TWILIO_TO_NUMBER=emergency_contact_number

# Model Paths
YOLO_CUSTOM_MODEL_PATH=../Yolo-Weights/best-2.pt
YOLO_STANDARD_MODEL_PATH=../Yolo-Weights/yolov8l.pt
```

## 🎮 Running the Project

### 1. Main Application (Enhanced Version)
```bash
streamlit run main.py
```
**Features:**
- Real-time vehicle detection on 2 lanes
- Emergency vehicle priority detection
- Accident detection with automatic alerts
- Interactive dashboard with statistics
- Twilio emergency calling system

**Access:** Open browser to `http://localhost:8501`

### 2. Basic Vehicle Counter
```bash
python Car-Counter.py
```
**Features:**
- Simple vehicle counting
- OpenCV display window
- Entry/exit line detection
- Basic tracking with graphics overlay

## 🔧 Detailed Setup Instructions

### YOLO Model Setup
1. **Create weights directory:**
   ```bash
   mkdir -p ../Yolo-Weights
   ```

2. **Download required models:**
   - **YOLOv8 Large**: Download `yolov8l.pt` from [Ultralytics](https://github.com/ultralytics/ultralytics)
   - **Custom Model**: Place your trained `best-2.pt` model for accident detection

3. **Verify model paths in `.env`:**
   ```env
   YOLO_CUSTOM_MODEL_PATH=../Yolo-Weights/best-2.pt
   YOLO_STANDARD_MODEL_PATH=../Yolo-Weights/yolov8l.pt
   ```

### Twilio Setup (For Emergency Features)
1. **Create Twilio account:** [https://www.twilio.com/](https://www.twilio.com/)
2. **Get credentials from Console Dashboard:**
   - Account SID
   - Auth Token
   - Phone number (from Twilio)
3. **Verify destination number** (required for trial accounts)
4. **Update `.env` file:**
   ```env
   TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxx
   TWILIO_AUTH_TOKEN=your_auth_token_here
   TWILIO_FROM_NUMBER=+15551234567  # Your Twilio number
   TWILIO_TO_NUMBER=+15559876543    # Emergency contact
   ```

### Video Files Setup
Ensure these video files exist in `video/` directory:
- `Video.mp4` - Main traffic video for Lane 1
- `accident.mp4` - Video with accident scenarios for Lane 2
- Additional videos: `vehicles5.mp4`, `Video2.mp4`, `Video3.mp4`

### Mask Files Setup
Required mask files in `Masks/` directory:
- `mask.png` - Detection mask for Lane 1
- `mask2.png` - Alternative mask
- `mask3.png` - Detection mask for Lane 2

## 📁 Project Structure

```
pythonProject/
├── main.py                 # Main enhanced application
├── Car-Counter.py          # Basic vehicle counter
├── sort.py                 # SORT tracking algorithm
├── setup.py                # Automated setup script
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
├── .gitignore             # Git ignore rules
├── README.md              # This file
├── assets/                # Graphics and assets
│   └── graphics.png
├── Masks/                 # Detection masks
│   ├── mask.png
│   ├── mask2.png
│   └── mask3.png
├── templates/             # Web templates
├── video/                 # Sample videos
└── output/               # Output directory
```

## 🎯 Application Controls

### Web Interface (main.py)
- **▶️ Play Video**: Start/stop video processing
- **Detection Sensitivity**: Adjust detection threshold (0.1-0.9)
- **Show Debug Info**: Display tracking IDs and internal data
- **Emergency Alerts Enabled**: Toggle automatic emergency calling

### Keyboard Controls (Car-Counter.py)
- **Q**: Quit application
- **Space**: Pause/resume (if implemented)

## 🔧 Features Overview

### Vehicle Detection
- Multi-class vehicle detection (cars, trucks, buses, motorcycles)
- Real-time object tracking with unique IDs
- Configurable detection sensitivity

### Emergency Response
- Automatic accident detection
- Emergency vehicle priority (ambulance, fire truck, police)
- Twilio integration for emergency calls
- Location-based emergency alerts

### Traffic Management
- Lane-based vehicle counting
- Entry/exit tracking
- Priority lane management
- Real-time statistics dashboard

## 🛡️ Security

- Environment variables for sensitive credentials
- No hardcoded API keys or tokens
- Secure Twilio integration
- Git ignore for sensitive files

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🐛 Troubleshooting

### Common Issues

**1. "Failed to load models" error:**
```bash
# Check if YOLO weights exist
ls -la ../Yolo-Weights/
# Download missing models
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8l.pt -P ../Yolo-Weights/
```

**2. "Failed to load mask images" error:**
```bash
# Verify mask files
ls -la Masks/
# Ensure mask.png and mask3.png exist
```

**3. Twilio authentication error:**
```bash
# Check .env file exists and has correct format
cat .env
# Verify credentials in Twilio Console
```

**4. Video not playing:**
```bash
# Check video files exist
ls -la video/
# Ensure Video.mp4 and accident.mp4 are present
```

**5. Port already in use:**
```bash
# Run on different port
streamlit run main.py --server.port 8502
```

### System Requirements
- **Python**: 3.8 or higher
- **RAM**: Minimum 4GB (8GB recommended)
- **GPU**: Optional (CUDA-compatible for faster processing)
- **Storage**: 2GB free space for models and videos

## 🆘 Support

For support and questions:
- Create an issue in the GitHub repository
- Check the documentation in the code comments
- Verify all setup steps are completed
- Check troubleshooting section above

## 🔮 Future Enhancements

- [ ] Real-time camera integration
- [ ] Database logging for analytics
- [ ] Mobile app integration
- [ ] Advanced traffic flow optimization
- [ ] Integration with traffic light systems
- [ ] Multi-camera support

## 📋 Pre-run Checklist

- [ ] Python 3.8+ installed
- [ ] Virtual environment activated (recommended)
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] `.env` file created and configured
- [ ] YOLO model weights downloaded and placed correctly
- [ ] Video files present in `video/` directory
- [ ] Mask files present in `Masks/` directory
- [ ] Twilio account configured (for emergency features)

## 🚀 Quick Test

```bash
# Test basic functionality
python -c "import cv2, streamlit, ultralytics; print('✅ All imports successful')"

# Run main application
streamlit run main.py
```

---

**⚠️ Important**: Configure environment variables before running. Emergency features require valid Twilio credentials. The application will work without Twilio but emergency calling will be disabled.
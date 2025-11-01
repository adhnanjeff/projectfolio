import cv2
import numpy as np
import tensorflow as tf
from tensorflow import keras
import json
import time
from datetime import datetime
import logging

class EnhancedAccidentDetector:
    def __init__(self, model_path='accident_detection_model.h5', config_path='config.json'):
        """
        Enhanced accident detection with multiple detection methods
        """
        self.model = None
        self.yolo_net = None
        self.config = self.load_config(config_path)
        self.setup_logging()
        
        # Detection parameters
        self.confidence_threshold = 0.6
        self.nms_threshold = 0.4
        self.accident_classes = ['accident', 'collision', 'crash']
        
        # Load models
        self.load_models()
        
    def load_config(self, config_path):
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return self.get_default_config()
    
    def get_default_config(self):
        """Default configuration"""
        return {
            "input_size": [416, 416],
            "classes": ["car", "truck", "motorcycle", "accident"],
            "confidence_threshold": 0.6,
            "nms_threshold": 0.4,
            "alert_cooldown": 5
        }
    
    def setup_logging(self):
        """Setup logging for detection events"""
        logging.basicConfig(
            filename='accident_detection.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
    
    def load_models(self):
        """Load YOLO and TensorFlow models"""
        try:
            # Load YOLO model
            self.yolo_net = cv2.dnn.readNet(
                'yolov3_custom3_final.weights', 
                'yolov3_custom3.cfg'
            )
            
            # Load TensorFlow model if available
            try:
                self.model = keras.models.load_model('accident_detection_model.h5')
            except:
                print("TensorFlow model not found, using YOLO only")
                
        except Exception as e:
            print(f"Error loading models: {e}")
    
    def preprocess_frame(self, frame):
        """Preprocess frame for detection"""
        height, width = frame.shape[:2]
        
        # Create blob for YOLO
        blob = cv2.dnn.blobFromImage(
            frame, 1/255.0, (416, 416), 
            swapRB=True, crop=False
        )
        
        return blob, height, width
    
    def detect_with_yolo(self, frame):
        """Detect accidents using YOLO"""
        blob, height, width = self.preprocess_frame(frame)
        
        self.yolo_net.setInput(blob)
        outputs = self.yolo_net.forward(self.yolo_net.getUnconnectedOutLayersNames())
        
        boxes = []
        confidences = []
        class_ids = []
        
        for output in outputs:
            for detection in output:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                
                if confidence > self.confidence_threshold:
                    center_x = int(detection[0] * width)
                    center_y = int(detection[1] * height)
                    w = int(detection[2] * width)
                    h = int(detection[3] * height)
                    
                    x = int(center_x - w/2)
                    y = int(center_y - h/2)
                    
                    boxes.append([x, y, w, h])
                    confidences.append(float(confidence))
                    class_ids.append(class_id)
        
        # Apply NMS
        indices = cv2.dnn.NMSBoxes(boxes, confidences, 
                                   self.confidence_threshold, self.nms_threshold)
        
        detections = []
        if len(indices) > 0:
            for i in indices.flatten():
                detections.append({
                    'box': boxes[i],
                    'confidence': confidences[i],
                    'class_id': class_ids[i],
                    'class_name': self.config['classes'][class_ids[i]] if class_ids[i] < len(self.config['classes']) else 'unknown'
                })
        
        return detections
    
    def analyze_motion_patterns(self, frame, prev_frame):
        """Analyze motion patterns for accident detection"""
        if prev_frame is None:
            return False, 0
        
        # Convert to grayscale
        gray1 = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Calculate optical flow
        flow = cv2.calcOpticalFlowPyrLK(gray1, gray2, None, None)
        
        # Analyze sudden motion changes
        motion_magnitude = np.mean(np.abs(flow[0] - flow[1])) if flow[0] is not None else 0
        
        # Threshold for sudden motion (potential accident)
        accident_threshold = 50
        is_accident = motion_magnitude > accident_threshold
        
        return is_accident, motion_magnitude
    
    def detect_accidents(self, frame, prev_frame=None):
        """Main accident detection function"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'accident_detected': False,
            'confidence': 0,
            'detections': [],
            'motion_analysis': None
        }
        
        # YOLO detection
        detections = self.detect_with_yolo(frame)
        results['detections'] = detections
        
        # Check for accident classes
        accident_detected = any(
            det['class_name'] in self.accident_classes 
            for det in detections
        )
        
        if accident_detected:
            results['accident_detected'] = True
            results['confidence'] = max(det['confidence'] for det in detections 
                                      if det['class_name'] in self.accident_classes)
        
        # Motion analysis
        if prev_frame is not None:
            motion_accident, motion_magnitude = self.analyze_motion_patterns(frame, prev_frame)
            results['motion_analysis'] = {
                'accident_detected': motion_accident,
                'magnitude': motion_magnitude
            }
            
            if motion_accident:
                results['accident_detected'] = True
                results['confidence'] = max(results['confidence'], 0.7)
        
        # Log detection
        if results['accident_detected']:
            logging.info(f"Accident detected with confidence: {results['confidence']}")
        
        return results
    
    def draw_detections(self, frame, results):
        """Draw detection results on frame"""
        for detection in results['detections']:
            x, y, w, h = detection['box']
            confidence = detection['confidence']
            class_name = detection['class_name']
            
            # Color based on class
            if class_name in self.accident_classes:
                color = (0, 0, 255)  # Red for accidents
            else:
                color = (0, 255, 0)  # Green for vehicles
            
            # Draw bounding box
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            
            # Draw label
            label = f"{class_name}: {confidence:.2f}"
            cv2.putText(frame, label, (x, y - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        # Draw accident alert
        if results['accident_detected']:
            cv2.putText(frame, "ACCIDENT DETECTED!", (50, 50),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
            cv2.putText(frame, f"Confidence: {results['confidence']:.2f}", (50, 90),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        return frame

def main():
    """Main function for testing"""
    detector = EnhancedAccidentDetector()
    
    # Test with video file
    cap = cv2.VideoCapture('test_video.mp4')  # Replace with your video
    prev_frame = None
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Detect accidents
        results = detector.detect_accidents(frame, prev_frame)
        
        # Draw results
        frame_with_detections = detector.draw_detections(frame, results)
        
        # Display
        cv2.imshow('Accident Detection', frame_with_detections)
        
        # Update previous frame
        prev_frame = frame.copy()
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
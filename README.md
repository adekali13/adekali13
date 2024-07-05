Real-Time Vehicle License Plate Detection and SMS Notification System
This project implements a real-time vehicle license plate detection system using a combination of computer vision, machine learning, and text recognition technologies. The system detects license plates from a live video feed, extracts the text, and sends SMS notifications for traffic violations.
Key Features :
Real-Time License Plate Detection: Utilizes TensorFlow Lite for efficient object detection from video frames captured via webcam.
Text Recognition: Integrates Tesseract OCR to extract text from detected license plates.
Database Management: Uses SQLite to store and manage detected license plate numbers and associated email addresses.
SMS Notifications: Sends SMS alerts for traffic violations using the Infobip API.

import cv2
import face_recognition
import numpy as np

def capture_face():
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()
    if not ret:
        return None
    face_locations = face_recognition.face_locations(frame)
    if face_locations:
        return face_recognition.face_encodings(frame, face_locations)[0]
    return None

def recognize_face(known_faces):
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()
    if not ret:
        return None

    face_locations = face_recognition.face_locations(frame)
    encodings = face_recognition.face_encodings(frame, face_locations)

    for encoding in encodings:
        matches = face_recognition.compare_faces([f[2] for f in known_faces], encoding)
        if True in matches:
            idx = matches.index(True)
            return known_faces[idx][0], known_faces[idx][1]  # rollno, name
    return None

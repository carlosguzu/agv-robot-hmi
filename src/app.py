from flask import Flask, render_template, Response
from flask_socketio import SocketIO
import cv2
import time

app = Flask(__name__)
socketio = SocketIO(app)

# Iniciar la cámara web
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
time.sleep(3)  # Permitir que la cámara se caliente

# Función para capturar el video de la cámara
def gen_frames():
    while True:
        start_time = time.time()  # Comienza a medir el tiempo
        frame = picam2.capture_array()
        
        ret, frame = cap.read()
        if not ret:
            continue
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
               
        # Controlar la tasa de cuadros
        elapsed_time = time.time() - start_time
        if elapsed_time < 0.04:  # Si ha pasado menos de 40ms, espera el resto del tiempo, 25fps
            time.sleep(0.04 - elapsed_time)

@app.route('/')
def index():
    return render_template('index_joystick.html')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@socketio.on('control')
def handle_control(data):
    steer = data.get('steer', 0)
    speed = data.get('speed', 0)
    sliderx = data.get('SliderX', 0)
    slidery = data.get('SliderY', 0)
    
    # Asegúrate de que los valores estén dentro del rango de -1000 a 1000
    steer = max(-1000, min(1000, steer))
    speed = max(-1000, min(1000, speed))
    
    print(f"Steer: {steer}, Speed: {speed}, SliderX: {sliderx}, SliderY: {slidery}")
    # Aquí puedes añadir la lógica para controlar tu robot

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
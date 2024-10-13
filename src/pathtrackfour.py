# from picamera2 import Picamera2
import cv2
import numpy as np
from time import sleep, time

# Configuración de la cámara
# def setup_camera(resolution=(640, 480)):   # 640, 480     1280, 720     1920, 1080
#     picam2 = Picamera2()
#     config = picam2.create_preview_configuration(main={"size": resolution})
#     picam2.configure(config)
#     picam2.start()
#     sleep(2)  # Esperar a que la cámara se estabilice
#     return picam2


def setup_camera(resolution=(640, 480)):
    cap = cv2.VideoCapture(0)  # 0 es el índice de la cámara predeterminada
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])
    sleep(2)  # Esperar a que la cámara se estabilice
    return cap


# Procesamiento de imagen
def preprocess_image(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, binary = cv2.threshold(blurred, 60, 255, cv2.THRESH_BINARY_INV)
    
    # Crear un kernel para operaciones morfológicas
    kernel = np.ones((5, 5), np.uint8)
    
    # Aplicar erosión para hacer más burda la línea
    eroded = cv2.erode(binary, kernel, iterations=1)
    
    # Aplicar dilatación para adelgazar los elementos estructurales
    dilated = cv2.dilate(eroded, kernel, iterations=1)
    
    return dilated

def detect_line(binary_frame):
    frame_height, frame_width = binary_frame.shape
    roi = binary_frame[int(frame_height / 2):, :]
    contours, _ = cv2.findContours(roi, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return contours, roi, frame_width, frame_height

def compute_steer(cx, frame_center):
    return ((cx - frame_center) / frame_center) * 1000

# Variables globales para PID
steerPID = 0.0
prev_steer = 0.0  # Variable para almacenar el valor anterior de 'steer'

# Función para implementar el control PID
def pid_control(steer, kp=0.8, kd=0.3, dt=0.1):
    global steerPID, prev_steer
    
    # Componente proporcional
    steerP = steer

    # Componente derivativa (derivada aproximada)
    steerD = (steer - prev_steer) / dt

    # PID final
    steerPID = (steerP * kp) + (steerD * kd)
     
    # Limitar Steer y Speed entre 0 y 1000
    steerPID = max(-1000, min(1000, steerPID))
 
    # Actualizar el valor previo de 'steer'
    prev_steer = steer

    return steerPID

def main():
    picam2 = setup_camera()
    prev_time = time()
    frame_count = 0
    speed_output = 0
    running = True
    
    # Inicializar la última posición del centroide como el centro del frame
    last_cx = None

    try:
        while running:
            ret, frame = picam2.read()
            if not ret:
                print("Failed to capture image")
                continue

            # Convertir de RGB a BGR para corregir los tonos azulados
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

            binary_frame = preprocess_image(frame)
            contours, roi, frame_width, frame_height = detect_line(binary_frame)
            roi_offset = int(frame_height / 2)
            frame_center = frame_width // 2

            if contours:
                largest_contour = max(contours, key=cv2.contourArea)
                M = cv2.moments(largest_contour)
                if M['m00'] != 0:
                    cx = int(M['m10'] / M['m00'])
                    cy = int(M['m01'] / M['m00']) + roi_offset
                    steer = compute_steer(cx, frame_center)

                    # Dibuja la línea y el círculo en el centroide detectado
                    cv2.line(frame, (cx, cy), (frame_center, cy), (0, 255, 0), 7)
                    cv2.circle(frame, (cx, cy), 14, (0, 0, 255), -1)
                    
                    # Guardar la última posición del centroide
                    last_cx = cx

                    steer_output = pid_control(steer)
                    speed_output += 10.0

                else:
                    steer_output = 0.0
                    speed_output -= 20.0
                    print("Línea no detectada")
                    # Evaluar si la línea se perdió hacia la izquierda o derecha
                    if last_cx is not None:
                        if last_cx < frame_center:
                            print("Línea perdida a la izquierda")
                        else:
                            print("Línea perdida a la derecha")
            else:
                steer_output = 0.0
                speed_output -= 20.0
                print("Línea no detectada")
                # Evaluar si la línea se perdió hacia la izquierda o derecha
                if last_cx is not None:
                    if last_cx < frame_center:
                        print("Línea perdida a la izquierda")
                    else:
                        print("Línea perdida a la derecha")
            
            
            speed_output = max(0, min(400, speed_output))

            #print(f"Steer: {steer_output:.2f}" + f"      Speed: {speed_output:.2f}")

            # Calcular FPS
            frame_count += 1.0
            current_time = time()
            elapsed_time = current_time - prev_time

            if elapsed_time >= 0.01:
                fps = frame_count / elapsed_time
                prev_time = current_time
                frame_count = 0.0
                
                print(f"Steer: {steer_output:.2f}" + f"      Speed: {speed_output:.2f}"f"      FPS: {fps:.2f}")

            cv2.drawContours(frame[roi_offset:, :], contours, -1, (255, 0, 0), 2)
            cv2.imshow('Frame', frame)

            key = cv2.waitKey(10) & 0xFF
            if key == ord('q'):
                running = False

    finally:
        picam2.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()

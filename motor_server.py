# motor_server.py
import network
import socket
import json
import time
from machine import Pin
from motor_control import MotorController

linearMotorPin = 25
linearMotorPwmFrequency = 100
linearMotorDutyMin = 200
linearMotorDutyMax = 800
vibrationMotorPin = 26
vibrationMotorPwmFrequency = 2500
vibrationMotorDutyMin = 250
vibrationMotorDutyMax = 445

# Get WiFi credentials from config file
def get_wifi_config():
    try:
        with open('wifi_config.txt', 'r') as f:
            config = {}
            for line in f.readlines():
                line = line.strip()
                if '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
            
            if 'ssid' in config and 'password' in config:
                return config['ssid'], config['password']
            else:
                print("Error: wifi_config.txt missing ssid or password")
                return None, None
    except OSError:
        print("Error: Could not open wifi_config.txt")
        return None, None

# Load WiFi credentials from file
WIFI_SSID, WIFI_PASSWORD = get_wifi_config()

# API server settings
HOST = '0.0.0.0'
PORT = 80

# Status LED - Use built-in LED on ESP32 DEVKITV1
status_led = Pin(2, Pin.OUT)  # Pin 2 is often connected to the onboard LED

# Initialize the motor controller
controller = MotorController()
controller.add_motor("linearMotor", linearMotorPin, linearMotorPwmFrequency, duty_min=linearMotorDutyMin, duty_max=linearMotorDutyMax)  # Pin 25, 100Hz
controller.add_motor("vibeMotor", vibrationMotorPin, vibrationMotorPwmFrequency, duty_min=vibrationMotorDutyMin, duty_max=vibrationMotorDutyMax)     # Pin 26, 5000Hz
# Ensure all motors are stopped at initialization
controller.stop_all()

def connect_wifi():
    """Connect to WiFi network"""
    # Check if credentials were loaded successfully
    if not WIFI_SSID or not WIFI_PASSWORD:
        print("No valid WiFi credentials found in wifi_config.txt")
        return False
        
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    print(f"Connecting to {WIFI_SSID}...")
    
    if not wlan.isconnected():
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        
        # Wait for connection with timeout
        max_wait = 10
        while max_wait > 0:
            if wlan.isconnected():
                break
            max_wait -= 1
            print("Waiting for connection...")
            time.sleep(1)
            
    if wlan.isconnected():
        status = wlan.ifconfig()
        print(f"Connected to WiFi")
        print(f"IP address: {status[0]}")
        return True
    else:
        print("Failed to connect to WiFi")
        return False

def parse_request(request):
    """Parse HTTP request to extract method, path and body"""
    request_lines = request.split(b'\r\n')
    request_line = request_lines[0].decode()
    
    method, path, _ = request_line.split(' ', 2)
    
    # Extract body for POST/PUT requests
    body = None
    if method in ['POST', 'PUT']:
        # Find the empty line that separates headers from body
        for i, line in enumerate(request_lines):
            if line == b'':
                body_lines = request_lines[i+1:]
                body = b'\r\n'.join(body_lines)
                try:
                    body = json.loads(body)
                except:
                    body = {}
                break
    
    return method, path, body

def handle_request(method, path, body):
    """Handle API requests and return response"""
    
    # Motor status endpoint
    if path == '/api/motors' and method == 'GET':
        response = {
            'motors': {
                'linearMotor': controller.get_motor('linearMotor').speed,
                'vibeMotor': controller.get_motor('vibeMotor').speed
            },
            'status': 'running'
        }
        return json.dumps(response), 200
    
    # Stop all motors
    elif path == '/api/motors/stop' and method == 'POST':
        controller.stop_all()
        return json.dumps({'status': 'All motors stopped'}), 200
    
    # Single motor control
    elif path.startswith('/api/motors/') and (method == 'POST' or method == 'PUT'):
        motor_name = path.split('/')[-1]
        
        if motor_name not in ['linearMotor', 'vibeMotor']:
            return json.dumps({'error': 'Motor not found'}), 404
            
        if body and 'speed' in body:
            try:
                speed = float(body['speed'])
                controller.set_speed(motor_name, speed)
                return json.dumps({'status': 'success', 'motor': motor_name, 'speed': speed}), 200
            except ValueError:
                return json.dumps({'error': 'Invalid speed value'}), 400
        else:
            return json.dumps({'error': 'Missing speed parameter'}), 400
    
    # Not found
    else:
        return json.dumps({'error': 'Not found'}), 404

def start_server():
    """Start the HTTP server with non-blocking sockets"""
    addr = socket.getaddrinfo(HOST, PORT)[0][-1]
    
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(5)
    
    # Set socket to non-blocking mode
    s.setblocking(False)
    
    print(f"Listening on {addr}")
    
    while True:
        try:
            # Blink LED to show server is running
            status_led.value(1)
            
            # Try to accept connection (non-blocking)
            try:
                client, addr = s.accept()
                print(f"Client connected from {addr}")
                
                # Set client socket to blocking for proper handling
                client.setblocking(True)
                
                # Indicate activity
                status_led.value(0)
                
                # Receive request
                request = client.recv(1024)
                
                # Parse and handle request
                method, path, body = parse_request(request)
                print(f"{method} {path}")
                
                response_body, status_code = handle_request(method, path, body)
                
                # Send response
                status_message = {200: 'OK', 400: 'Bad Request', 404: 'Not Found'}
                status = status_message.get(status_code, 'Unknown')
                
                response = f"HTTP/1.0 {status_code} {status}\r\n"
                response += "Content-Type: application/json\r\n"
                response += "Access-Control-Allow-Origin: *\r\n"
                response += f"Content-Length: {len(response_body)}\r\n"
                response += "\r\n"
                response += response_body
                
                client.send(response.encode())
                client.close()
            
            except OSError as e:
                # No connection available, yield to other tasks
                pass
                
            # Short delay to allow WebREPL and other tasks to run
            time.sleep(0.01)
            
        except Exception as e:
            print(f"Error: {e}")
            try:
                client.close()
            except:
                pass

def main():
    """Main function"""
    # First connect to WiFi
    if connect_wifi():
        # Get network status
        wlan = network.WLAN(network.STA_IF)
        ip = wlan.ifconfig()[0]
        
        # Print connection info
        print("\n==========================")
        print(f"Connected to WiFi: {WIFI_SSID}")
        print(f"IP address: {ip}")
        print(f"REST API available at http://{ip}/api/motors")
        print("==========================\n")
        
        # Start the web server
        start_server()
    else:
        # Indicate error with rapid flashing
        print("WiFi connection failed. Please check wifi_config.txt")
        # Flash LED pattern: 3 quick flashes, pause, repeat
        while True:
            for _ in range(3):
                status_led.value(1)
                time.sleep(0.1)
                status_led.value(0)
                time.sleep(0.1)
            time.sleep(1)

if __name__ == "__main__":
    main()
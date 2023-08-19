import config
import traceback
import signal
import subprocess
import time
import asyncio
import os
import board
import RPi.GPIO as GPIO
from datetime import datetime
from datetime import datetime
from azure.iot.device import IoTHubSession, DirectMethodResponse
from adafruit_seesaw.seesaw import Seesaw

async def main():
    async_state = {}
    sensor_and_pumps_initialized = False
    while not sensor_and_pumps_initialized:
        try:
            sensor = init_sensor()
            init_pumps()
            sensor_and_pumps_initialized = True
            log("Pumps and sensor successfully initialized.")
        except Exception:
            log(traceback.format_exc())
            await asyncio.sleep(config.error_retry_seconds)
    
    while True:
        try:
            log("Connecting to IoT Hub...")
            async with IoTHubSession.from_connection_string(config.iot_hub_connection_string) as session:
                log("Connected to IoT Hub.")
                await asyncio.gather(
                    recurring_telemetry(session, sensor),
                    receive_direct_method_requests(session, async_state, sensor)
                )
        except KeyboardInterrupt:
            log("Keyboard exit.")
            raise
        except Exception:
            log(traceback.format_exc())
            await asyncio.sleep(config.error_retry_seconds)

def init_pumps():
    for pump_name, pin_number in config.pin_mapper.items():
        log(f'Initializing "{pump_name}" at GPIO{pin_number}.')
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin_number, GPIO.OUT)
        GPIO.cleanup()

def init_sensor():
    i2c_bus = board.I2C()
    sensor = Seesaw(i2c_bus, addr = config.sensor_address)
    return sensor

async def recurring_telemetry(session, sensor):
    while True:
        measurments = read_measurments(sensor)
        log(f'Sending message: "{measurments}"')
        await session.send_message(measurments)
        await asyncio.sleep(config.telemetry_frequency_seconds)

async def receive_direct_method_requests(session, async_state, sensor):
    async with session.direct_method_requests() as method_requests:
        async for method_request in method_requests:
            try:
                if method_request.name == "runPump":
                    log(f'Received run pump signal with payload: "{method_request.payload}"')
                    run_pump(method_request.payload["pumpName"], method_request.payload["duration"])
                    log('Finished running pump.')
                    payload = {"result": "OK"}
                    status = 200
                elif method_request.name == "startStreaming":
                    log('Received start streaming signal.')
                    start_streaming(async_state)
                    log('Streaming started.')
                    payload = {"result": "OK"}
                    status = 200
                elif method_request.name == "stopStreaming":
                    log('Received stop streaming signal.')
                    stop_streaming(async_state)
                    log('Streaming stopped.')
                    payload = {"result": "OK"}
                    status = 200
                elif method_request.name == "read":
                    log('Received read signal.')
                    measurments = read_measurments(sensor)
                    log(f'Finished reading. Measurements: "{measurments}".')
                    payload = { "result": "OK", "data": measurments }
                    status = 200
                elif method_request.name == "ping":
                    log('Received ping signal.')
                    payload = {"result": "OK"}
                    status = 200
                else:
                    payload = {"result": "Unknown direct method request."}
                    status = 400
                    log("Receivied unknown direct method request.")
            except Exception:
                status = 500
                payload = {"result": traceback.format_exc()}
                log(traceback.format_exc())
            method_response = DirectMethodResponse.create_from_method_request(
                method_request, status, payload)
            await session.send_direct_method_response(method_response)

def start_streaming(async_state):
    async_state['streaming_process'] = subprocess.Popen(
        config.start_streaming_script_path, preexec_fn = os.setsid)
    log(f'Streaming started with PID: {async_state["streaming_process"].pid}.')

def stop_streaming(async_state):
    log(f'Killing streaming with PID: {async_state["streaming_process"].pid}.')
    async_state['streaming_process'].kill()
    os.killpg(os.getpgid(async_state['streaming_process'].pid), signal.SIGTERM)

def run_pump(pump_name, duration):
    pin_number = config.pin_mapper[pump_name]
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin_number, GPIO.OUT)

        log(f'Setting GPIO{pin_number} to LOW for {duration}s.')
        GPIO.output(pin_number, GPIO.LOW)
        time.sleep(duration)
        log(f'Setting GPIO{pin_number} to HIGH.')
        GPIO.output(pin_number, GPIO.HIGH)
    finally:
        GPIO.cleanup()

def read_measurments(sensor):
    humidity = sensor.moisture_read()
    temp = sensor.get_temp()
    now = datetime.now().isoformat()
    measurments = dict(sensorId = 1, humidity = humidity, temperature = temp, timestamp = now)
    return measurments

def log(message):
    now = datetime.now()
    log_prefix = now.strftime("%d.%m.%Y %H:%M:%S")
    log_line = f'{log_prefix} {message}\n'
    logs_directory_path = config.logs_directory_path.rstrip('/')
    log_file_name = f'{now.strftime("%Y%m%d")}.log'
    log_file_path = f'{logs_directory_path}/{log_file_name}'

    with open(log_file_path, "a") as log_file:
        log_file.write(log_line)

if __name__ == "__main__":
    asyncio.run(main())
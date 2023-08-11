import requests
import config
from datetime import datetime
from picamera import PiCamera
from time import sleep

now = datetime.now()
capture_file_name = f'{now.strftime("%Y%m%d_%H%M%S")}.jpg'

camera = PiCamera()
camera.resolution = (3280, 2464)
camera.start_preview()
# Camera warm-up time
sleep(2)

captures_directory_path = config.captures_directory_path.rstrip('/')

camera.capture(f'{captures_directory_path}/{capture_file_name}')

with open(f'{captures_directory_path}/{capture_file_name}', "rb") as data:
    url = f'{config.captures_sa_url}/{config.captures_container}/{capture_file_name}{config.captures_sas_token}'
    response = requests.put(url, data = data, headers = {'x-ms-blob-type': 'BlockBlob'})
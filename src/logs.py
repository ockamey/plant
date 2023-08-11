import config
import requests
from datetime import datetime, timedelta

six_minutes_ago = datetime.now() - timedelta(minutes = 6)
log_file_name = f'{six_minutes_ago.strftime("%Y%m%d")}.log'
logs_directory_path = config.logs_directory_path.rstrip('/')

with open(f'{logs_directory_path}/{log_file_name}', "rb") as data:
    url = f'{config.logs_sa_url}/{config.logs_container}/{log_file_name}{config.logs_sas_token}'
    response = requests.put(url, data = data, headers = {'x-ms-blob-type': 'BlockBlob'})
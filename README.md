# Azure Integrated Plant Watering System

This project allows to control watering of plants by using phisical components like relay or pumps, as well as Azure services to send requests or analyze data.

## Demo of running Pumps with Video Streaming
### Video of Pump 1

[![IMAGE ALT TEXT HERE](https://img.youtube.com/vi/wpda6YF3fcg/0.jpg)](https://www.youtube.com/watch?v=wpda6YF3fcg)

### Video of Pump 2

[![IMAGE ALT TEXT HERE](https://img.youtube.com/vi/forhIUt8PwY/0.jpg)](https://www.youtube.com/watch?v=forhIUt8PwY)

## Images

<img src="https://github.com/ockamey/plant/assets/140854403/7d7267da-d88d-456f-9ad1-fc00e4aa4bf5" alt="pic1" width="400"/>

<img src="https://github.com/ockamey/plant/assets/140854403/2cf1ea30-3f3d-4fff-851e-799858f0daa9" alt="pic2" width="400"/>

<img src="https://github.com/ockamey/plant/assets/140854403/d4560829-f345-4ed9-b0c2-b0985572461e" alt="pic3" width="800"/>

<img src="https://github.com/ockamey/plant/assets/140854403/4f20f1b1-3d03-4676-9792-fef4154e8d7f" alt="pic3" width="400"/>

<img src="https://github.com/ockamey/plant/assets/140854403/1ffe9820-cf1e-49c0-a1bd-ae5866ddbc22" alt="pic3" width="400"/>

## Architecture of the project

<img width="1156" alt="Screenshot 2023-08-10 at 16 10 58" src="https://github.com/ockamey/plant/assets/140854403/9ccffdf6-b5de-46b1-8a0a-ebad6855cdb3">

## Phisical components used in the project

* Raspberry Pi Zero WH - to send signals to/from Azure and to/from phisical devices
* 4-channel 5V relay - to control pumps
* 5V water pumps - to add water to plants
* Adafruit STEMMA Soil Sensor - to receive humidity of soil
* Raspberry Pi Camera Module 2 - to see what's happening with plants

## Cloud components used in the project

* Azure IoT Hub - to send requests to Raspberry Pi and to receive humidity and temperature data from the sensor
* Azure Data Explorer - to present received data
* Azure Media Services - to stream video from the Camera to see live what's happening with plants
* Azure Storage Account - to save pictures taken by the Camera, save logs from Raspberry Pi and save recordings of video streams

## Software components used in the project
### `plant.py`
The main module connects to the IoT Hub, and every n minutes, sends information about humidity and temperature there. The module also listens to direct method requests coming from IoT Hub. The execution of this program is specified in `rc.local` to start it in the startup of the Raspberry Pi. The modules supports following requests:

* **Ping** - it's used to check the connection between IoT Hub and Raspberry Pi.
  * Method name: `ping`
  * Example request body:
      ```
      {}
      ``` 
  * Example response body: 
    ```
    {
        "status": 200,
        "payload": {
            "result": "OK"
        }
    }
    ```

https://github.com/ockamey/plant/assets/140854403/354dd909-dc9b-4d1a-902f-62db2410225f


* **Read** - it's used to obtain readings from the sensor.
  * Method name: `read`
  * Example request body:
    ```
    {}
    ```
  * Example response body:
    ```
    {
    "status": 200,
        "payload": {
            "result": "OK",
            "data": {
                "sensorId": 1,
                "humidity": 616,
                "temperature": 23.5075238802,
                "timestamp": "2023-08-10T21:35:17.011484"
            }
        }
    }
    ```

https://github.com/ockamey/plant/assets/140854403/697935b3-1900-48fa-a8bd-590e5c3cc45c

    
* **Start Streaming** - it's used to start video streaming from Raspberry Pi to Azure Media Services. The Live Streaming Event in AMS has to be started before that.
  * Method name: `startStreaming`
  * Example request body:
    ```
    {}
    ``` 
  * Example response body: 
    ```
    {
        "status": 200,
        "payload": {
            "result": "OK"
        }
    }
    ```
* **Stop Streaming** - it's used to gracefully stop video streaming from Raspberry Pi to Azure Media Services. Then the Live Streaming Event in AMS can be stopped to save costs.
  * Method name: `stopStreaming`
  * Example request body:
    ```
    {}
    ``` 
  * Example response body: 
    ```
    {
        "status": 200,
        "payload": {
            "result": "OK"
        }
    }
    ```
* **Run pump** - it's used to enable a pump for particular duration of time. The `pumpName` has to match with one in `pin_mapper` in `config.py`. The `duration` parameter is scaled in seconds. So far the system is using only 2 pumps and one sensor, but it's easly possible to extend that.
  * Method name: `runPump`
  * Example request body:
    ```
    {
        "pumpName": "pump1",
        "duration": 10
    }
    ``` 
  * Example response body: 
    ```
    {
        "status": 200,
        "payload": {
            "result": "OK"
        }
    }
    ```
Screenshots from Azure Data Explorer:
<img src="https://github.com/ockamey/plant/assets/140854403/1d75fa96-c5ab-4056-864a-9326f4cff090" alt="pic3" width="800"/>

<img src="https://github.com/ockamey/plant/assets/140854403/40a14371-f8a7-4adf-9955-24c2101282d8" alt="pic3" width="800"/>

### `capture.py`
Tthe side module which takes a picture from Raspberry Pi Camera, and uploads it to the Storage Account. The program is triggered every 5 min by cron job (`crontab -e`). To save some space in Raspberry Pi and in Azure, the cleanup activities have been configured. In Raspberry Pi, there is another cron for that to remove all pictures older than 24h (`0 0 * * * find <path to captures tmp folder>/* -mmin +1440 -delete`). On Azure side, in the Storage Account, Lifecycle Mangement has been configured to remove all captures older than a month.

### `logs.py`
The side module which takes logs generated from Raspberry Pi, and uploads them to the Storage Account. The module is triggered by cron job every 5 min.

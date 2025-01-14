import os
import random

import paho.mqtt.client as mqtt
from paho.mqtt import client as mqtt_client
import dotenv

dotenv.load_dotenv()

broker = os.getenv("BROKER")
port = int(os.getenv("PORT"))
topic = os.getenv("TOPIC")
feedback_topic = os.getenv("FEEDBACK_TOPIC", topic)
mqtt_username = os.getenv("MQTT_USERNAME")
mqtt_password = os.getenv("MQTT_PASSWORD")

client_id = f"python-mqtt-{random.randint(0, 1000)}"

print("Host:", broker)

def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)
    print("Connecting to", broker, port, topic, feedback_topic, mqtt_username, mqtt_password)
    client = mqtt_client.Client(mqtt.CallbackAPIVersion.VERSION1)
    # set username and password
    client.username_pw_set(mqtt_username, mqtt_password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client

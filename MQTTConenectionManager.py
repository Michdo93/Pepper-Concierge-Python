# -*- coding: utf-8 -*-
import paho.mqtt.client as mqtt
import xml.etree.ElementTree as ET

class MQTTConnectionManager:
    def __init__(self, delegate):
        self.delegate = delegate
        self.qos = 0
        self.auth = None
        self.broker_tls = None

        config_file_path = "config/config.xml"
        root = ET.parse(config_file_path).getroot()

        self.topic_publish_base = root.find('MQTT_PUBLISH_TOPIC_BASE').text
        self.topic_subscribe_base = root.find('MQTT_SUBSCRIBE_TOPIC_BASE').text
        self.broker_ip = root.find('MQTT_BROKER_IP').text
        self.broker_port = int(root.find('MQTT_BROKER_PORT').text)  # Convert port to integer
        self.brokerTransport = "tcp"

        self.client_id = "Pepper"
        self.client = mqtt.Client(self.client_id, clean_session=True,userdata=None, protocol=mqtt.MQTTv311, transport=self.brokerTransport)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.username_pw_set(self.auth)
        
        # Jetzt können Sie die Verbindung zum Broker herstellen
        self.client.connect(self.broker_ip, self.broker_port)

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Verbunden mit dem MQTT-Broker. Verbindungsergebniscode:", rc)
            # Fügen Sie hier weitere Aktionen nach erfolgreicher Verbindung hinzu
            # Zum Beispiel können Sie sich zu bestimmten Topics subscriben
            self.client.subscribe(self.topic_subscribe_base + "#", self.qos)
        else:
            print("Verbindung zum MQTT-Broker fehlgeschlagen. Rückgabewert:", rc)

    def on_message(self, client, userdata, msg):
        print("Message Arrived: " + msg.topic + " payload: " + msg.payload.decode())
        self.delegate.on_subscription(msg.topic, msg.payload.decode())

    def publish_to_item(self, item, payload):
        topic = self.topic_publish_base + str(item)
        print("Publishing to topic:", topic)
        print("Payload:", payload)
        self.client.publish(topic, payload, self.qos)

    def subscribe_to_item(self, item):
        topic = self.topic_subscribe_base + str(item)
        self.client.subscribe(topic, self.qos)

    def subscribe_to_items(self, items):
        for item in items:
            self.subscribe_to_item(item)

    def unsubscribe_of_item(self, item):
        topic = self.topic_subscribe_base + str(item)
        self.client.unsubscribe(topic)

    def unsubscribe_of_items(self, items):
        for item in items:
            self.unsubscribe_of_item(item)

    def disconnect(self):
        self.client.disconnect()


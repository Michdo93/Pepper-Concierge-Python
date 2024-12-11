# -*- coding: utf-8 -*-
import paho.mqtt.client as mqtt
import xml.etree.ElementTree as ET
import ssl  # Sicherstellen, dass `ssl` importiert ist

class MQTTConnectionManager:
    def __init__(self, delegate):
        self.delegate = delegate

        config_file_path = "config/config.xml"
        root = ET.parse(config_file_path).getroot()

        self.broker_transport = root.find('MQTT_BROKER_TRANSPORT').text
        self.broker_ip = root.find('MQTT_BROKER_IP').text
        self.broker_port = int(root.find('MQTT_BROKER_PORT').text)
        self.client_id = root.find('MQTT_CLIENT_ID').text
        self.tls_path = root.find('MQTT_BROKER_IP').text
        # self.tls_version = int(root.find('MQTT_TLS_VERSION').text)

        tls_version_str = root.find('MQTT_TLS_VERSION').text
        if tls_version_str == "1.2":
            self.tls_version = ssl.PROTOCOL_TLSv1_2
        elif tls_version_str == "1.3":
            self.tls_version = ssl.PROTOCOL_TLSv1_3
        else:
            raise ValueError("Unsupported TLS version specified in config: " + tls_version_str)

        self.broker_user = root.find('MQTT_BROKER_USER').text
        self.broker_password = root.find('MQTT_BROKER_PASSWORD').text
        self.broker_qos = int(root.find('MQTT_BROKER_QOS').text)
        self.retain = self.__stringToBoolean(root.find('MQTT_RETAIN').text)
        self.broker_async = self.__stringToBoolean(root.find('MQTT_BROKER_ASYNC').text)

        self.auth = None

        self.topic_publish_base = root.find('MQTT_PUBLISH_TOPIC_BASE').text
        self.topic_subscribe_base = root.find('MQTT_SUBSCRIBE_TOPIC_BASE').text

        if self.broker_qos not in range(0, 3):
            self.broker_qos = 0

        if self.broker_user is not None:
            if self.broker_password is not None:
                self.auth = {'username': self.broker_user,
                             'password': self.broker_password}
            else:
                self.auth = {'username': self.broker_user,
                             'password': ""}
        else:
            self.auth = None

        if self.broker_user == "" or self.broker_user == None:
            self.auth = None

        if self.broker_port != 1883:
            if self.tls_path is not None or self.tls_path != "":
                if self.tls_version is not None or self.tls_version != "":
                    self.broker_tls = (self.tls_path, self.tls_version)
                else:
                    self.broker_tls = self.tls_path
            else:
                self.broker_tls = None

        self.client = mqtt.Client(self.client_id, clean_session=True, userdata=None, protocol=mqtt.MQTTv311, transport=self.broker_transport)

        if self.broker_tls is not None:
            self.client.tls_set(self.broker_tls)

        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.username_pw_set(self.auth)
        
        # Jetzt können Sie die Verbindung zum Broker herstellen
        if self.broker_async:
            self.client.connect_async(self.broker_ip, self.broker_port)
        else:
            self.client.connect(self.broker_ip, self.broker_port)

    def __stringToBoolean(self, string):
        if string.lower() == "true":
            return True
        else:
            return False

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
        self.client.publish(topic, payload, self.qos, retain=self.retain)

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


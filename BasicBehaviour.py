# -*- coding: utf-8 -*-
import logging
import inspect
import traceback
import time
import threading
import sys
import paramiko
from MQTTConenectionManager import MQTTConnectionManager
import xml.etree.ElementTree as ET

class BasicBehaviour:
    def __init__(self, application, session):
        self.application = application

        app_file_path = "config/app.xml"
        config_file_path = "config/config.xml"
        mqtt_topics_file_path = "config/mqtt_topics.xml"
        text_file_path = "config/text.xml"

        app_root = ET.parse(app_file_path).getroot()
        config_root = ET.parse(config_file_path).getroot()
        mqtt_topics_root = ET.parse(mqtt_topics_file_path).getroot()
        text_root = ET.parse(text_file_path).getroot()

        self.app_config_xml = app_root.find('config')
        self.app_functions_xml = app_root.find('functions')
        self.config_xml = config_root
        self.text_xml = text_root
        self.mqtt_topics_xml = mqtt_topics_root

        self.memory = session.service("ALMemory")
        self.motion = session.service("ALMotion")
        self.text_to_speech = session.service("ALTextToSpeech")
        self.animated_speech = session.service("ALAnimatedSpeech")
        self.animation_player = session.service("ALAnimationPlayer")
        self.behavior_manager = session.service("ALBehaviorManager")

        self.session = session

        self.mqtt_connection_manager = MQTTConnectionManager(self)
        self.logger = None

        if self.__stringToBoolean(self.config_xml.find("DEBUG").text):
            self.init_logger()

        self.config()

    def __stringToBoolean(self, string):
        if string.lower() == "true":
            return True
        else:
            return False

    def start(self):
        try:
            self.presentation()
        except Exception as ex:
            self.log(logging.ERROR, traceback.format_exc())

    def config(self):
        self.text_to_speech.setLanguage(self.app_config_xml.find("LANGUAGE").text)
        self.motion.setExternalCollisionProtectionEnabled("All", True)
        self.motion.setWalkArmsEnabled(True, True)
        self.motion.setOrthogonalSecurityDistance(0.15)
        self.motion.wakeUp()

    def presentation(self):
        print("Presentation")
        self.put_head_up()

        # Liste der Funktionen, wie sie in der XML-Datei stehen
        function_list = [
            ("WELCOME", self.welcome),
            ("MUSIC", self.music),
            ("ALEXA", self.alexa),
            ("ROLLER_SHUTTER", self.roller_shutter),
            ("CAR_DRIVING_TRAINING", self.car_driving_training),
            ("KITCHEN", self.kitchen),
            ("FAREWELL", self.farewell)
        ]

        for function_name, function_method in function_list:
            if self.__stringToBoolean(self.app_functions_xml.find(function_name).text):
                function_method()
                if self.is_last_function(function_list, function_name):
                    print(f"{function_name} is the last function which will be executed.")

                    farewell_status = self.__stringToBoolean(self.app_functions_xml.find("FAREWELL").text)
                    if not farewell_status:
                        self.finalize_presentation()

        self.disconnect_all()

    def is_last_function(self, function_list, current_function_name):
        """
        Prüft, ob die aktuelle Funktion die letzte True-Funktion ist.
        """
        for function_name, _ in function_list:
            if function_name == current_function_name:
                continue  # Überspringe die aktuelle Funktion
            if self.__stringToBoolean(self.app_functions_xml.find(function_name).text):
                return False  # Es gibt noch eine andere ausführbare Funktion
        return True

    def finalize_presentation(self):
        """
        Führt Aktionen aus, wenn die Präsentation abgeschlossen ist.
        """
        print("Alle Funktionen wurden ausgeführt. Abschluss der Präsentation.")
        self.say_lines(["Vielen Dank für eure Aufmerksamkeit!"])
        self.put_head_up()

    def welcome(self):
        print("Welcome")
        welcome_text = self.text_xml.find("welcome")

        try:
            self.say_lines([welcome_text.find("LINE_1").text, welcome_text.find("LINE_2").text, welcome_text.find("LINE_3").text, welcome_text.find("LINE_4").text, welcome_text.find("LINE_5").text])
            self.put_head_up()
        except Exception as ex:
            self.log(logging.ERROR, traceback.format_exc())

    def music(self):
        print("Music")
        music_text = self.text_xml.find("music")

        multimedia_elements = self.mqtt_topics_xml.find('Multimedia')
        if multimedia_elements is not None:
            speakers_elements = multimedia_elements.find("speakers")

        try:
            self.say_lines([music_text.find("LINE_1").text, music_text.find("LINE_2").text])
            # Play music
            self.mqtt_connection_manager.publish_to_item(speakers_elements.find("SONOS_SPEAKER_URI").text, self.config_xml.find("MUSIC_URL").text)
            self.mqtt_connection_manager.publish_to_item(speakers_elements.find("SONOS_SPEAKER_MUTE").text, "OFF")
            self.mqtt_connection_manager.publish_to_item(speakers_elements.find("SONOS_SPEAKER_VOLUME").text, "50")

            time.sleep(5)

            self.behavior_manager.runBehavior("Headbang")

            time.sleep(2)

            self.mqtt_connection_manager.publish_to_item(speakers_elements.find("SONOS_SPEAKER_MUTE").text, "ON")

            time.sleep(2)

            self.say_lines([music_text.find("LINE_3").text])
            self.put_head_up()
        except Exception as ex:
            self.log(logging.ERROR, traceback.format_exc())
            
    def alexa(self):
        print("Alexa")
        alexa_text = self.text_xml.find("alexa")

        try:
            self.say_lines([alexa_text.find("LINE_1").text])
            time.sleep(1)
            
            self.say_lines([alexa_text.find("LINE_2").text])
            time.sleep(2)
            
            self.say_lines([alexa_text.find("LINE_3").text])
            time.sleep(0.5)
            
            self.say_lines([alexa_text.find("LINE_4").text])
            self.animation_player.run("animations/Stand/BodyTalk/Listening/Listening_1")
            time.sleep(2)
            
            self.animation_player.run("animations/Stand/Gestures/Yes_1")
            time.sleep(2)
            
            self.animation_player.run("animations/Stand/BodyTalk/Listening/Listening_7")
            time.sleep(3)
            
            self.animation_player.run("animations/Stand/Gestures/Yes_2")
            time.sleep(2)
            
            self.animation_player.run("animations/Stand/BodyTalk/Listening/Listening_4")
            time.sleep(1)
            
            self.say_lines([alexa_text.find("LINE_5").text])
            self.put_head_up()
            
            self.say_lines([alexa_text.find("LINE_6").text, alexa_text.find("LINE_7").text])
            
            if self.__stringToBoolean(self.app_config_xml.find("PROJECTOR_AUTOMATICALLY").text):
                self.mqtt_connection_manager.publish_to_item(self.mqtt_topics_xml.find("Conference").find("projector").find("PROJECTOR").text, "ON")
            
            time.sleep(1)
            
            self.say_lines([alexa_text.find("LINE_8").text])
            self.put_head_up()
        
        except Exception as ex:
            self.log(logging.ERROR, traceback.format_exc())

    def roller_shutter(self):
        print("Roller shutter")
        roller_shutter_text = self.text_xml.find("roller_shutter")

        try:
            self.say_lines([roller_shutter_text.find("LINE_1").text])
            self.motion.moveTo(0.0, 0.0, -0.785)
            
            self.behavior_manager.runBehavior("WTF")
            self.say_lines([roller_shutter_text.find("LINE_2").text])
            
            self.mqtt_connection_manager.publish_to_item(self.mqtt_topics_xml.find("Conference").find("roller_shutters").find("ROLLER_SHUTTER_2").text, "DOWN")
            time.sleep(12)
            self.mqtt_connection_manager.publish_to_item(self.mqtt_topics_xml.find("Conference").find("roller_shutters").find("ROLLER_SHUTTER_2").text, "STOP")
            
            self.motion.moveTo(0.0, 0.0, 0.785)
            self.say_lines([roller_shutter_text.find("LINE_3").text, roller_shutter_text.find("LINE_4").text, roller_shutter_text.find("LINE_5").text])
        except Exception as ex:
            self.log(logging.ERROR, traceback.format_exc())

    def car_driving_training(self):
        print("Car driving training")
        car_driving_training_text = self.text_xml.find("car_driving_training")

        self.say_lines([car_driving_training_text.find("LINE_1").text])

        def ssh_exec():
            user = self.config_xml.find("SSH_USER").text
            password = self.config_xml.find("SSH_PASSWORD").text
            host = self.config_xml.find("SSH_HOST").text
            port = self.config_xml.find("SSH_PORT").text
            vlc_path = self.config_xml.find('VLC_PATH').text
            movie_path = self.config_xml.find('MOVIE_PATH').text
            output_buffer = ""
            try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                print("Establishing Connection...")
                ssh.connect(host, port, user, password)
                print("Connection established.")
                print("Creating EXEC Channel.")
                stdin, stdout, stderr = ssh.exec_command(vlc_path + " " + movie_path)
                output_buffer = stdout.read().decode()
                ssh.close()
            except (paramiko.SSHException, IOError) as e:
                print(e)

        thread = threading.Thread(target=ssh_exec)
        thread.start()

        time.sleep(1)

        self.animation_player.run("animations/Stand/Waiting/DriveCar_1")
        self.animation_player.run("animations/Stand/Waiting/DriveCar_1")

        # thread.stop()  # Avoid using thread.stop() as it's deprecated and unsafe

        self.say_lines([car_driving_training_text.find("LINE_2").text])

        self.mqtt_connection_manager.publish_to_item(self.mqtt_topics_xml.find("Conference").find("projector").find("PROJECTOR").text, "OFF")

        self.say_lines([car_driving_training_text.find("LINE_3").text])
    
    def kitchen(self):
        print("Kitchen")
        kitchen_text = self.text_xml.find("kitchen")

        kitchen_elements = self.mqtt_topics_xml.find('Kitchen')
        if kitchen_elements is not None:
            topics = kitchen_elements.find("lights")

        try:
            self.put_head_up()

            self.say_lines([kitchen_text.find("LINE_1").text, kitchen_text.find("LINE_2").text])

            self.mqtt_connection_manager.publish_to_item(self.mqtt_topics_xml.find("Conference").find("roller_shutters").find("ROLLER_SHUTTER_2").text, "UP")

            self.motion.moveTo(0.0, 0.0, 0.785)
            time.sleep(0.5)
            self.motion.moveTo(3.3, 0.0, 0.0)
            time.sleep(0.5)
            self.motion.moveTo(0.0, 0.0, -1.5709)
            time.sleep(0.5)
            self.motion.moveTo(0.5, 0.0, 0.0)
            time.sleep(0.5)
            self.put_head_up()

            self.say_lines([kitchen_text.find("LINE_3").text, kitchen_text.find("LINE_4").text])

            # Licht anschalten
            if self.__stringToBoolean(self.app_config_xml.find("LAMPS_INDIVIDUALLY").text):
                self.mqtt_connection_manager.publish_to_item(topics.find("HUE_1_Switch").text, "ON")
                self.mqtt_connection_manager.publish_to_item(topics.find("HUE_2_Switch").text, "ON")
                self.mqtt_connection_manager.publish_to_item(topics.find("HUE_3_Switch").text, "ON")
                self.mqtt_connection_manager.publish_to_item(topics.find("HUE_4_Switch").text, "ON")
            else:
                self.mqtt_connection_manager.publish_to_item(topics.find("HUE_Switch").text, "ON")
            
            time.sleep(2)

            self.say_lines([kitchen_text.find("LINE_5").text, kitchen_text.find("LINE_6").text, kitchen_text.find("LINE_7").text])
        except Exception as ex:
            self.log(logging.ERROR, traceback.format_exc())

    def farewell(self):
        print("Farewell")
        farewell_text = self.text_xml.find("farewell")

        kitchen_elements = self.mqtt_topics_xml.find('Kitchen')
        if kitchen_elements is not None:
            topics = kitchen_elements.find("lights")

        try:
            time.sleep(2)
            self.say_lines([farewell_text.find("LINE_1").text])
            self.motion.moveTo(-1.0, 0.0, 0.0)

            if self.__stringToBoolean(self.app_config_xml.find("LAMPS_INDIVIDUALLY").text):
                self.mqtt_connection_manager.publish_to_item(topics.find("HUE_1_Switch").text, "OFF")
                self.mqtt_connection_manager.publish_to_item(topics.find("HUE_2_Switch").text, "OFF")
                self.mqtt_connection_manager.publish_to_item(topics.find("HUE_3_Switch").text, "OFF")
                self.mqtt_connection_manager.publish_to_item(topics.find("HUE_4_Switch").text, "OFF")
            else:
                self.mqtt_connection_manager.publish_to_item(topics.find("HUE_Switch").text, "OFF")

            self.motion.rest()
        except Exception as ex:
                self.log(logging.ERROR, traceback.format_exc())

    def put_head_up(self):
        try:
            self.motion.angleInterpolationWithSpeed("Head", [0.0, -0.3], 0.3)
        except Exception as ex:
            self.log(logging.ERROR, traceback.format_exc())

    def log(self, severity, message):
        if self.__stringToBoolean(self.config_xml.find("DEBUG").text):
            if self.logger:  # Sicherstellen, dass der Logger initialisiert wurde
                caller_frame = inspect.stack()[1]
                caller_file = caller_frame[1]
                caller_line = caller_frame[2]
                self.logger.error("%s - File: %s, Line: %d - %s", str(severity), caller_file, caller_line, str(message))
            else:
                print("Logger wurde nicht initialisiert:", severity, message)  # Alternativ: Auf die Konsole ausgeben

    def init_logger(self):
        self.logger = logging.getLogger("BasicBehaviour")
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        file_handler = logging.FileHandler("pepper_" + time.strftime("%d_%m_%Y_%H_%M") + ".log")
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        self.logger.setLevel(logging.DEBUG)

    def say_lines(self, lines):
        for line in lines:
            self.animated_speech.say(line)

    def disconnect_all(self):
        self.mqtt_connection_manager.disconnect()
        self.application.stop()
        sys.exit()

    def on_subscription(self, item, value):
        item_description = item.split("/")[3]
        print("onSubscription:", item_description)

        if item_description in [self.mqtt_topics_xml.find("Conference").find("WINDOW1").text, self.mqtt_topics_xml.find("Conference").find("WINDOW2").text,
                                self.mqtt_topics_xml.find("Conference").find("WINDOW3").text, self.mqtt_topics_xml.find("Conference").find("WINDOW4").text,
                                self.mqtt_topics_xml.find("Conference").find("WINDOW5").text, self.mqtt_topics_xml.find("Conference").find("WINDOW6").text,
                                self.mqtt_topics_xml.find("Multimedia").find("WINDOW1").text, self.mqtt_topics_xml.find("Multimedia").find("WINDOW2").text,
                                self.mqtt_topics_xml.find("Multimedia").find("WINDOW3").text]:
            try:
                if value == "OPEN":
                    print("onSubscription:", item_description, value)
                    self.memory.raise_event("WindowOpend", item_description)
                elif value == "CLOSED":
                    print("onSubscription:", item_description, value)
                    self.memory.raise_event("WindowClosed", item_description)
            except Exception as ex:
                self.log(logging.ERROR, traceback.format_exc())
        else:
            try:
                self.memory.insert_data(item, value)
            except Exception as ex:
                self.log(logging.ERROR, traceback.format_exc())

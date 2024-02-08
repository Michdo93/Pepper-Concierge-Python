# -*- coding: utf-8 -*-
import xml.etree.ElementTree as ET
from BasicBehaviour import BasicBehaviour
import qi
import sys

class Pepper:
    def __init__(self, application, session):
        self.application = application
        self.session = session

    def start(self):
        # BasicBehaviour mit der qi.Session-Instanz initialisieren und starten
        basic_behaviour = BasicBehaviour(self.application, self.session)
        basic_behaviour.start()

# Hauptprogramm
if __name__ == "__main__":
    # Implementierung der Logik zum Laden der Konfigurationsdatei
    config_file_path = "config/config.xml"
    root = ET.parse(config_file_path).getroot()

    ROBOT_URL = root.find('ROBOT_URL').text
    ROBOT_PORT = root.find('ROBOT_PORT').text

    app = qi.Application(["--qi-url=" + "tcp://" + ROBOT_URL + ":" + str(ROBOT_PORT)])
    app.start()

    pepper = Pepper(app, app.session)
    pepper.start()

    app.run()

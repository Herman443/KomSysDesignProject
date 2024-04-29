import paho.mqtt.client as mqtt
import logging
from threading import Thread
import json
from appJar import gui

MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883

MQTT_TOPIC_INPUT = "ttm4115/team_15/project/appInput"
MQTT_TOPIC_OUTPUT = "ttm4115/team_15/project/serverInput"


class AppComponent:

    def on_connect(self, client, version, userdata, flags, rc):
        self._logger.debug("MQTT connected to {}".format(client))

    def on_message(self, client, userdata, msg):
        self._logger.debug("Incoming message to topic {}".format(msg.topic))
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
        except Exception as err:
            self._logger.error(
                "Message sent to topic {} had no valid JSON. Message ignored. {}".format(
                    msg.topic, err
                )
            )
            return
        topic = payload.get("topic")
        self._logger.debug("Topic of message is {}".format(topic))
        if topic == "price":
            try:
                price = payload.get("price")
                self.app.clearLabel("label")
                self.app.setLabel("label", f"Price: {price} kWh")
            except Exception as err:
                self._logger.error("Invalid arguments to topic. {}".format(err))
        elif topic == "unavailable":
            try:
                self.app.clearLabel("label")
                self.app.setLabel("label", f"Charger unavailable")
            except Exception as err:
                self._logger.error("Invalid arguments to topic. {}".format(err))
        elif topic == "reserved":
            try:
                self.app.clearLabel("label")
                self.app.setLabel("label", f"Charger successfully reserved")
            except Exception as err:
                self._logger.error("Invalid arguments to topic. {}".format(err))
        elif topic == "charging":
            try:
                self.app.clearLabel("label")
                self.app.setLabel("label", f"Car is charging")
            except Exception as err:
                self._logger.error("Invalid arguments to topic. {}".format(err))
        elif topic == "charging_stopped":
            try:
                self.app.clearLabel("label")
                self.app.setLabel("label", f"Charging has stopped")
            except Exception as err:
                self._logger.error("Invalid arguments to topic. {}".format(err))
        elif topic == "unreserved":
            try:
                self.app.clearLabel("label")
                self.app.setLabel("label", f"Reservation ran out")
            except Exception as err:
                self._logger.error("Invalid arguments to topic. {}".format(err))
        elif topic == "plug_in":
            try:
                self.app.clearLabel("label")
                self.app.setLabel("label", f"Plug in car")
            except Exception as err:
                self._logger.error("Invalid arguments to topic. {}".format(err))
        else:
            self._logger.error("Unknown topic {}. Message ignored.".format(topic))

    def __init__(self):
        self._logger = logging.getLogger(__name__)
        print("logging under name {}.".format(__name__))
        self._logger.info("Starting Component")

        self._logger.debug(
            "Connecting to MQTT broker {} at port {}".format(MQTT_BROKER, MQTT_PORT)
        )
        self.mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        self.mqtt_client.connect(MQTT_BROKER, MQTT_PORT)
        self.mqtt_client.subscribe(MQTT_TOPIC_INPUT)
        self.mqtt_client.loop_start()

        self.create_gui()

    def create_gui(self):
        self.app = gui()

        def publish_command(command):
            payload = json.dumps(command)
            self._logger.info(command)
            self.mqtt_client.publish(MQTT_TOPIC_OUTPUT, payload=payload, qos=2)

        self.app.startLabelFrame("Choose action:")

        def check_price():
            publish_command({"command": "check_price"})

        def start_charging():
            publish_command({"command": "start_charge"})

        def reserve15():
            publish_command({"command": "reserve_15"})

        def reserve30():
            publish_command({"command": "reserve_30"})

        def stop_charge():
            publish_command({"command": "stop_charge"})

        self.app.addButton("Check Price", check_price)
        self.app.addButton("Start charging", start_charging)
        self.app.addButton("Reserve in 15 minutes", reserve15)
        self.app.addButton("Reserve in 30 minutes", reserve30)
        self.app.addButton("Stop charging", stop_charge)
        self.app.stopLabelFrame()
        self.app.addLabel("label", "")

        self.app.go()

    def stop(self):
        """
        Stop the component.
        """
        self.mqtt_client.loop_stop()


debug_level = logging.DEBUG
logger = logging.getLogger(__name__)
logger.setLevel(debug_level)
ch = logging.StreamHandler()
ch.setLevel(debug_level)
formatter = logging.Formatter(
    "%(asctime)s - %(name)-12s - %(levelname)-8s - %(message)s"
)
ch.setFormatter(formatter)
logger.addHandler(ch)

t = AppComponent()

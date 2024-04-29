import paho.mqtt.client as mqtt
import logging
import stmpy
from threading import Thread
import json
import requests

MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883

MQTT_TOPIC_INPUT = "ttm4115/team_15/project/serverInput"
MQTT_TOPIC_APP = "ttm4115/team_15/project/appInput"
MQTT_TOPIC_CHARGER = "ttm4115/team_15/project/chargerInput"


class ServerLogic:

    def __init__(self, name, duration, component):
        self._logger = logging.getLogger(__name__)
        self.name = name
        self.duration = duration
        self.component = component

    def create_machine(timer_name, duration, component):
        """
        Create a complete state machine instance for the timer object.
        Note that this method is static (no self argument), since it is a helper
        method to create this object.
        """
        server_logic = ServerLogic(
            name=timer_name, duration=duration, component=component
        )
        t0 = {"source": "initial"}
        server_stm = stmpy.Machine(name=timer_name, transitions=[t0], obj=server_logic)
        server_logic.stm = server_stm
        return server_stm


class ServerComponent:

    def on_connect(self, client, version, userdata, flags, rc):
        self._logger.debug("MQTT connected to {}".format(client))

    def publish_command(self, command, channel):
        payload = json.dumps(command)
        self._logger.info(command)
        if channel == "app":
            self.mqtt_client.publish(MQTT_TOPIC_APP, payload=payload, qos=2)
        else:
            self.mqtt_client.publish(MQTT_TOPIC_CHARGER, payload=payload, qos=2)

    def get_price(self):
        response = requests.get(
            "https://www.hvakosterstrommen.no/api/v1/prices/2024/04-15_NO5.json"
        )
        if response.status_code != 404:
            return json.loads(json.dumps(response.json()[0]))["NOK_per_kWh"]

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
        command = payload.get("command")
        self._logger.debug("command of message is {}".format(command))
        if command == "check_price":
            try:
                pris = str(self.get_price())
                melding = '{"topic":"price", "price":"' + pris + '"}'
                self.publish_command(json.loads(melding), "app")
            except Exception as err:
                self._logger.error("Invalid arguments to command. {}".format(err))
        elif command == "reserve_15":
            try:
                melding = '{"command":"reserve15"}'
                self.publish_command(json.loads(melding), "charger")
            except Exception as err:
                self._logger.error("Invalid arguments to command. {}".format(err))
        elif command == "reserve_30":
            try:
                melding = '{"command":"reserve30"}'
                self.publish_command(json.loads(melding), "charger")
            except Exception as err:
                self._logger.error("Invalid arguments to command. {}".format(err))
        elif command == "start_charge":
            try:
                melding = '{"command":"start_charge"}'
                self.publish_command(json.loads(melding), "charger")
            except Exception as err:
                self._logger.error("Invalid arguments to command. {}".format(err))
        elif command == "stop_charge":
            try:
                melding = '{"command":"stop_charge"}'
                self.publish_command(json.loads(melding), "charger")
            except Exception as err:
                self._logger.error("Invalid arguments to command. {}".format(err))
        elif command == "unavailable":
            try:
                melding = '{"topic":"unavailable"}'
                self.publish_command(json.loads(melding), "app")
            except Exception as err:
                self._logger.error("Invalid arguments to command. {}".format(err))
        elif command == "reserved":
            try:
                melding = '{"topic":"reserved"}'
                self.publish_command(json.loads(melding), "app")
            except Exception as err:
                self._logger.error("Invalid arguments to command. {}".format(err))
        elif command == "charging":
            try:
                melding = '{"topic":"charging"}'
                self.publish_command(json.loads(melding), "app")
            except Exception as err:
                self._logger.error("Invalid arguments to command. {}".format(err))
        elif command == "charging_stopped":
            try:
                melding = '{"topic":"charging_stopped"}'
                self.publish_command(json.loads(melding), "app")
            except Exception as err:
                self._logger.error("Invalid arguments to command. {}".format(err))
        elif command == "unreserved":
            try:
                melding = '{"topic":"unreserved"}'
                self.publish_command(json.loads(melding), "app")
            except Exception as err:
                self._logger.error("Invalid arguments to command. {}".format(err))
        else:
            self._logger.error("Unknown command {}. Message ignored.".format(command))

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

        self.stm_driver = stmpy.Driver()
        self.stm_driver.start(keep_active=True)
        self._logger.debug("Component initialization finished")

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

t = ServerComponent()

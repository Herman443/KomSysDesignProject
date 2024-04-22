# SenseHat packets
from sense_hat import SenseHat
import time

# MQTT packets
import paho.mqtt.client as mqtt
import logging
import stmpy
from threading import Thread
import json

# Sense Hat parameters
sense = SenseHat()
red = (255, 0, 0)
green = (0, 255, 0)
blue = (0, 0, 255)
yellow = (255, 255, 0)

# Avaliability
available = 1

# MQTT parameters
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC_INPUT = "ttm4115/team_15/project/chargerInput"
MQTT_TOPIC_OUTPUT = "ttm4115/team_15/project/serverInput"


class ChargerStateMachine:
    def __init__(self, sense, component):
        self._logger = logging.getLogger(__name__)
        self.component = component
        self.name = "charger"
        self.sense = sense
        self.state = "unconnected"
        available = 1

    def start_1(self):
        self.stm.start_timer("t1", 60000)  # 1 min
        self.sense.clear(blue)
        available = 0

    def start_15(self):
        self.stm.start_timer("t15", 900000)  # 15 min
        self.sense.clear(yellow)
        available = 0

    def start_30(self):
        self.stm.start_timer("t30", 1800000)  # 30 min
        self.sense.clear(yellow)
        available = 0

    def available(self):
        ChargerComponent.publish_command({"command": "unreserved"})
        available = 1

    def start_charging(self):
        self.sense.clear(red)
        ChargerComponent.publish_command({"command": "charging"})
        available = 0

    def stop_charging(self):
        self.sense.clear(green)
        ChargerComponent.publish_command({"command": "charging_stopped"})
        available = 1

    def create_machine(component):
        charger_logic = ChargerStateMachine(component=component)
        t0 = {"source": "initial", "target": "idle"}
        t1 = {
            "source": "idle",
            "target": "reserved",
            "trigger": "reserve15",
            "effect": "start_15",
        }
        t2 = {
            "source": "idle",
            "target": "reserved",
            "trigger": "reserve30",
            "effect": "start_30",
        }
        t3 = {
            "source": "reserved",
            "target": "charging",
            "trigger": "button_press",
            "effect": "start_charging",
        }
        t4 = {
            "source": "idle",
            "target": "awaiting",
            "trigger": "start_charge",
            "effect": "start_1",
        }
        t5 = {
            "source": "awaiting",
            "target": "charging",
            "trigger": "button_press",
            "effect": "start_charging",
        }
        t6 = {
            "source": "reserved",
            "target": "idle",
            "trigger": "t15",
            "effect": "available",
        }
        t7 = {
            "source": "reserved",
            "target": "idle",
            "trigger": "t30",
            "effect": "available",
        }
        t8 = {
            "source": "awaiting",
            "target": "idle",
            "trigger": "t1",
            "effect": "available",
        }
        t9 = {
            "source": "charging",
            "target": "idle",
            "trigger": "button_press",
            "effect": "stop_charging",
        }

        charger_stm = stmpy.Machine(
            name="charger",
            transitions=[t0, t1, t2, t3, t4, t5, t6, t7, t8, t9],
            obj=charger_logic,
        )
        charger_logic.stm = charger_stm
        return charger_stm

    def toggle(self):
        if self.state == "unconnected":
            self.state = "connected"
            self.sense.clear(green)
            # send message of new state (on)
        else:
            self.state = "unconnected"
            self.sense.clear(red)
            # send message of new state (off)


class ChargerComponent:
    def on_connect(self, client, version, userdata, flags, rc):
        self._logger.debug("MQTT connected to {}".format(client))

    def publish_command(self, command):
        payload = json.dumps(command)
        self._logger.info(command)
        self.mqtt_client.publish(MQTT_TOPIC_OUTPUT, payload=payload, qos=2)

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
        if command == "reserve":
            try:
                if available == 0:
                    self.publish_command({"command": "unavailable"})
                else:
                    self.publish_command({"command": "reserved"})
                    time = json.dumps(payload["time"])
                    if time == "15":
                        self.stm_driver.send("reserve15", "charger", [], {})
                    elif time == "30":
                        self.stm_driver.send("reserve30", "charger", [], {})
            except Exception as err:
                self._logger.error("Invalid arguments to command. {}".format(err))
        elif command == "start_charge":
            try:
                self.stm_driver.send("start_charge", "charger", [], {})
            except Exception as err:
                self._logger.error("Invalid arguments to command. {}".format(err))
        elif command == "stop_charge":
            try:
                self.stm_driver.send("stop_charge", "charger", [], {})
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
        self.stm_driver.add_machine(ChargerStateMachine.create_machine(self))
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

t = ChargerComponent()


state_machine = ChargerStateMachine(sense)

try:
    while True:
        for event in sense.stick.get_events():
            if event.action == "pressed":
                # state_machine.toggle()
                state_machine.stm_driver.send("button_press", "charger", [], {})
        time.sleep(0.1)  # Sleep a little to prevent bouncing
except KeyboardInterrupt:
    sense.clear()  # Turn off all LEDs

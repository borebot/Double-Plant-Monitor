# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import time
import board
import displayio
import terminalio
import adafruit_tsl2591
from adafruit_display_text import label
import adafruit_displayio_ssd1306
from adafruit_seesaw.seesaw import Seesaw
import ssl
import socketpool
import wifi
import adafruit_minimqtt.adafruit_minimqtt as MQTT
import supervisor

from secrets import secrets

i2c_bus = board.STEMMA_I2C()

ss1 = Seesaw(i2c_bus, addr=0x36)

ss2 = Seesaw(i2c_bus, addr=0x37)

lightsensor = adafruit_tsl2591.TSL2591(i2c_bus)
lightsensor.gain = adafruit_tsl2591.GAIN_LOW

displayio.release_displays()

display_bus = displayio.I2CDisplay(i2c_bus, device_address=0x3c)
display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=128, height=32)

splash = displayio.Group()
font = terminalio.FONT
text_color = 0xFFFFFF

label_1 = label.Label(font, text = "test", color=text_color, scale=1)
label_1.x = 0
label_1.y = 4
label_1.line_spacing = 1

splash.append(label_1)
display.show(splash)

# wifi/IO setup
aio_username = secrets["aio_username"]
aio_key = secrets["aio_key"]

try:
    wifi.radio.connect(secrets["ssid"], secrets["password"])
    label_1.text = "Connected to Wifi!"
except:
    supervisor.reload()

time.sleep(1.0)

### Feeds ###

# Setup a feed named 'ss1_moist' for publishing to a feed
ss1_moist_feed = secrets["aio_username"] + "/feeds/ss1_moist"
ss1_temp_feed = secrets["aio_username"] + "/feeds/ss1_temp"

ss2_moist_feed = secrets["aio_username"] + "/feeds/ss2_moist"
ss2_temp_feed = secrets["aio_username"] + "/feeds/ss2_temp"

plant_light_sensor_feed = secrets["aio_username"] + "/feeds/plant_light_sensor"

# Define callback methods which are called when events occur
# pylint: disable=unused-argument, redefined-outer-name
def connected(client, userdata, flags, rc):
    # This function will be called when the client is connected
    # successfully to the broker.
    #print("Connected to Adafruit IO! Listening for topic changes on %s" % onoff_feed)
    # Subscribe to all changes on the onoff_feed.
    #client.subscribe(onoff_feed)
    print("placeholder1")


def disconnected(client, userdata, rc):
    # This method is called when the client is disconnected
    print("Disconnected from Adafruit IO!")


def message(client, topic, message):
    # This method is called when a topic the client is subscribed to
    # has a new message.
    #print("New message on topic {0}: {1}".format(topic, message))
    print("placeholder2")


# Create a socket pool
pool = socketpool.SocketPool(wifi.radio)

# Set up a MiniMQTT Client
mqtt_client = MQTT.MQTT(
    broker=secrets["broker"],
    port=secrets["port"],
    username=secrets["aio_username"],
    password=secrets["aio_key"],
    socket_pool=pool,
    ssl_context=ssl.create_default_context(),
)

# Setup the callback methods above
mqtt_client.on_connect = connected
mqtt_client.on_disconnect = disconnected
mqtt_client.on_message = message

# Connect the client to the MQTT broker.
print("Connecting to Adafruit IO...")
label_1.text = "Connecting to Adafruit.io..."
mqtt_client.connect()

while True:
    try:
        #poll message queue
        #mqtt_client.loop()

        # read moisture level through capacitive touch pad
        moist1 = ss1.moisture_read()
        moist2 = ss2.moisture_read()

        # read temperature from the temperature sensor
        temp1 = ss1.get_temp()
        temp2 = ss2.get_temp()

        #read light levels

        visible = lightsensor.visible

        mqtt_client.publish(ss1_moist_feed, moist1)
        mqtt_client.publish(ss1_temp_feed, temp1)

        mqtt_client.publish(ss2_moist_feed, moist2)
        mqtt_client.publish(ss2_temp_feed, temp2)

        mqtt_client.publish(plant_light_sensor_feed, visible)



        print("Soil Sensor 1 temp: " + str(temp1) + "  moisture: " + str(moist1))
        print("Soil Sensor 2 temp: " + str(temp2) + "  moisture: " + str(moist2))
        print("visible light: " + str(visible))
        print("")

        label_1.text = "S1: T=" + "{:.2f}".format(temp1) + " M=" + str(moist1)+ "\n" + "S2: T=" + "{:.2f}".format(temp2) + " M=" + str(moist2) + "\n" + "Light=" + str(visible)

        time.sleep(30)
    except:
        supervisor.reload()


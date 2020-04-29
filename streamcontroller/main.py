#!/usr/bin/env python3

#         Python Stream Deck Library
#      Released under the MIT license
#
#   dean [at] fourwalledcubicle [dot] com
#         www.fourwalledcubicle.com
#

# Example script showing basic library usage - updating key images with new
# tiles generated at runtime, and responding to button state change events.

import os
import sys
import threading
import json
from PIL import Image, ImageDraw, ImageFont
from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.ImageHelpers import PILHelper
from pynput.keyboard import Key, Controller
import operator
import functools

# Folder location of image assets used by this example.
ASSETS_PATH = os.path.join(os.path.dirname(__file__), "Assets")


def get_or_default(dict, key, default):
    if key in dict.keys():
        return dict[key]
    else:
        print("Could not find key '" + key + "' in json object. Returning default value '" + default + "'.")
        return default


def dict_contains_key(dict, key):
    if key in dict.keys():
        return True
    else:
        return False


def dict_contains_keys(dict, keys):
    exists = list(map(lambda k: dict_contains_key(dict, k), keys))
    return functools.reduce(operator.and_, exists, True)


class ConfigItem:
    def __init__(self, keyId, text, image, command):
        self.keyId = keyId
        self.text = text
        self.image = image
        self.command = command

    @staticmethod
    def from_dictionary(json):
        required_keys = ["keyId", "command"]
        if dict_contains_keys(json, required_keys):
            keyId = get_or_default(json, "keyId", -1)
            text = get_or_default(json, "text", "")
            image = get_or_default(json, "image", "")
            command = get_or_default(json, "command", "")
            item = ConfigItem(keyId, text, image, command)
            return item
        else:
            raise Exception("The configuration item '{}' is missing at least one of the following keys: {}.".format(json, ", ".join(required_keys)))

    @staticmethod
    def error_item():
        item = ConfigItem()
        item.keyId = -1
        item.text = "Error"
        item.image = ""
        item.command = ""
        return item

    def validate(self):
        if not os.path.exists(self.command) and self.command != "(exit)":
            print("Warning: The command '{}' does not point to a valid file (although this might be because of added arguments).".format(self.command))

        if self.image is not None and self.image is not "" and not os.path.exists(self.image):
            raise Exception("The image '{}' defined for keyId '{}' does not exist.".format(self.image, self.keyId))


class Configuration:
    def __init__(self, items, serialnumber, font, font_size):
        self.items = items
        self.serialnumber = serialnumber
        self.font = font
        self.font_size = font_size

    def get_by_key_id(self, index):
        matches = list(filter(lambda i: i.keyId == index, self.items))
        if len(matches) > 0:
            return matches[0]
        else:
            return None

    def label_for_key_id(self, index):
        item = self.get_by_key_id(index)
        if item is not None:
            return item.text
        else:
            return ""

    def image_for_key_id(self, index):
        item = self.get_by_key_id(index)
        if item is not None:
            return item.image
        else:
            return ""

    def command_for_key_id(self, index):
        item = self.get_by_key_id(index)
        if item is not None:
            return item.command
        else:
            return None

    def validate(self):
        for i in self.items:
            i.validate()

        if not os.path.exists(self.font):
            raise Exception("The font configuration points to a non-existing file: '{}'.".format(self.font))

        if self.font is None or self.font == "":
            raise Exception("You have not set a font in the configuration file. Please add \"font\": \"path to font\" to the root element of the configuration.")
        
    @staticmethod
    def from_dictionary(dict):
        required_keys = [ "keys", "font" ]
        if dict_contains_keys(dict, required_keys):
            items = []
            serialnumber = get_or_default(dict, "serialnumber", None)
            for o in dict["keys"]:
                items.append(ConfigItem.from_dictionary(o))
            font_size = 14 if not dict_contains_key(dict, "fontSize") else dict["fontSize"]
            return Configuration(items, serialnumber, dict["font"], font_size)
        else:
            raise Exception("The configuration contains at least one object in the root array that does not have a 'serialnumber' or 'keys' key.")


def load_config(filename):
    if os.path.exists(filename):
        file = open(filename, 'r')
        try:
            content = json.load(file)
            return Configuration.from_dictionary(content)
        except json.JSONDecodeError as e:
            print("There is a problem with the format of the configuration file.", e)
    else:
        raise Exception("Could not find configuration file '" + filename + "'.")


def key_change_callback(config, current_deck, deck, key, state):
    if deck.get_serial_number() != current_deck.get_serial_number():
        print("A key on a different device has been pressed.")
        return

    if state:
        print("Key '{}' on deck '{}' has state '{}'.".format(key, deck.get_serial_number(), state))
        command = config.command_for_key_id(key)
        if command is not None and command == "(exit)":
            deck.reset()
            deck.close()
        elif command is not None:
            run_command(command)
        else:
            print("No command is defined for key '{}'.".format(key))


def update_key_image(config, deck, key, state):
    label = config.label_for_key_id(key)
    icon = config.image_for_key_id(key)
    image = render_key(config, deck, icon, config.font, label)
    deck.set_key_image(key, image)


def render_key(config, deck, icon_filename, font_filename, label):
    image = PILHelper.create_image(deck)
    has_label = label is not None and label != ""

    # Render the image in case it exists.
    if os.path.exists(icon_filename):
        icon = Image.open(icon_filename).convert("RGBA")
        image_height = image.height - 20 if has_label else image.height - 5
        image_width = image.width if has_label else image.width - 2
        icon.thumbnail((image_width, image_height), Image.LANCZOS)
        icon_pos = ((image.width - icon.width) // 2, 0)
        image.paste(icon, icon_pos, icon)
    
    # Render the label.
    if has_label:
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype(font_filename, config.font_size)
        label_w, label_h = draw.textsize(label, font=font)
        label_pos = ((image.width - label_w) // 2, image.height - 20)
        draw.text(label_pos, text=label, font=font, fill="white")

    return PILHelper.to_native_format(deck, image)


def run_command(command):
    os.system(command)


def list_streamdeck_ids():
    streamdecks = DeviceManager().enumerate()
    for index, deck in enumerate(streamdecks):
        deck.open()
        deck.reset()
        print("#{}.: Device type: {}, device id: {}, serial number: {}".format(index, deck.deck_type(), deck.id().decode("utf-8"), deck.get_serial_number()))
        deck.close()


def select_streamdeck(config, decks):
    if config.serialnumber is not None:
        for d in decks:
            d.open()
            stringId = d.get_serial_number()
            d.close()
            if stringId == config.serialnumber:
                return d
        ids = ", ".join(list(map(lambda x: x.get_serial_number(), decks)))
        raise Exception("The config files refers stream deck id '{}' but that device is not connected. The following devices are connected: '{}'. Please check the connected devices using the argument '--list'.".format(config.serialnumber, ids))
    elif len(decks) > 0:
        return decks[0]
    else:
        raise Exception("No stream deck device was detected.")


def run():
    config = load_config("config.json")
    config.validate()
    streamdecks = DeviceManager().enumerate()
    print("Found {} Stream Deck(s).\n".format(len(streamdecks)))
    deck = select_streamdeck(config, streamdecks)
    deck.open()
    deck.reset()
    _key_change_callback = functools.partial(key_change_callback, config, deck)
    print("Opened '{}' device (serial number: '{}')".format(deck.deck_type(), deck.get_serial_number()))
    deck.set_brightness(30)
    deck.set_key_callback(_key_change_callback)

    for key in range(deck.key_count()):
        update_key_image(config, deck, key, False)

    for t in threading.enumerate():
        if t is threading.currentThread():
            continue

        if t.is_alive():
            t.join()


try:
    if __name__ == "__main__":
        if len(sys.argv) == 2 and sys.argv[1] == "--list":
            list_streamdeck_ids()
        elif(len(sys.argv) >= 2):
            print("This programm can be run with a single argument '--list' to enumerate all stream decks or without any parameter for normal operation.")
        else:
            run()

except Exception as e:
    print("The program encountered an error: ", e)

# Overview

This small Python 3.7 app allows you to use your Elgato Stream Deck from Linux. 
It builds upon [abcminiuser's stream deck library](https://github.com/abcminiuser/python-elgato-streamdeck).
The project uses [poetry](https://python-poetry.org/) to manage its dependencies.

# Installation

The app relies on the following libraries:

* streamdeck
* wheel
* pillow
* pynput
* xlib
* argparse

In case you want to run this on Windows or OSX you will need to replace `xlib` according to this [documentatoin](https://python-elgato-streamdeck.readthedocs.io/en/stable/pages/backend_libusb.html).
You can download a release of this software from the [releases](https://github.com/b0wter/streamdeck/releases) page.

# Configuration

This is a sample configuration file:

```
{
    "serialnumber": "AL44G1A02732",
    "font": "/usr/share/fonts/truetype/ubuntu/UbuntuMono-R.ttf",
    "keys": [
        {
            "keyId": 0,
            "image": "brighter.png",
            "command": "/home/b0wter/bin/lights/brighter"
        },
        {
            "keyId": 1,
            "image": "dimmer.png",
            "text": "dim",
            "command": "/home/b0wter/bin/lights/dimmer"
        },
        {
            "keyId": 2,
            "text": "Text button!",
            "command": "/home/b0wter/bin/lights/off"
        },
        {
            "keyId": 14,
            "image": "exit.png",
            "command": "(exit)"
        }
    ]
}
```

The root object may have these keys:

| key          | description                         | optional |
|--------------|-------------------------------------|----------|
| serialnumber | Serial number of the device to use. | yes      |
| font         | Path to a TTF file.                 | no       |
| fontSize     | Font size, defaults to 14           | yes      |
| keys         | Definition of what the buttons do.  | no       |

The `serialnumber` is only required if you have connected more than one Stream Deck.
In case this field is empty the app will connect to the first device it finds.
To list the serial numbers of all connected devices you may run this app with the optional parameter `--list`.

The configuration items may have these keys:

| key     | description                                         | optional |
|---------|-----------------------------------------------------|----------|
| keyId   | Id of the key, ranges from 0 to number of keys - 1. | no       |
| image   | Path to an image file.                              | yes      |
| text    | Label for the button. Displayed under the image.    | yes      |
| command | Command to run.                                     | no       |

`command` has one special value. If you set it to "(exit)" a button press will exit the application.

The app will perform various checks when parsing the configuration file and exit immediately on any error.

## Multiple devices

In case you have multiple devices you need to define a configuration file for each device and add the `serialnumber` key.

# Running the app

The app knows two command line arguments. You need to supply exactly one of them:
```
./streamdeck.py --list                  # lists all connected devices and exits
./streamdeck.py --config config.json    # uses `config.json` to run the app
```

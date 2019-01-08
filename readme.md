# WOLBOT

Simple Wake-on-Lan Telegram bot

![chat example](images/chat.jpg)

## Commands

> See `/help` for a list of available commands

## Requirements
- python 3
- python-telegram-bot
- Virtualenv (recommended)

## Installation

Clone the repository
```
# mkdir -p /opt/wolbot
# chown -R user:group /opt/wolbot
$ git clone url /opt/wolbot
$ cd /opt/wolbot
```

Edit the config with your favorite editor (aka `vim`)
```
$ cp config.example.py config.py
$ vim config.py
```

Set up the Python environment
```
$ virtualenv wolbot_venv
$ source wolbot_venv/bin/activate
(venv)$ pip install -r requirements.txt
```

Start the application
```
(venv)$ python3 wolbot.py
```

### Autostart on Raspberry Pi

The easiest way is to add the launcher script to `/etc/rc.local`.
```
/opt/wolbot/wolbot-launcher.sh
```


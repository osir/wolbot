#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os.path
import logging
import re

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import config
import wol

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO)
logger = logging.getLogger(__name__)
machines = {}

##
# Command Handlers
##

def cmd_help(bot, update):
    help_message = """
    (*≧▽≦) WOLBOT (≧▽≦*)

    /help
        Display this help

    /wake <name>
        Wake saved machine with name

    /wakemac <mac>
        Wake machine with mac address

    /list
        List all saved machines

    /add <name> <mac>
        Add a machine

    /remove <name>
        Remove a machine

    Names may only contain a-z, 0-9 and _
    Mac addresses can use any or no separator
    """
    update.message.reply_text(help_message)


def cmd_wake(bot, update, **kwargs):
    if not authorize(bot, update):
        return
    if 'args' not in kwargs or len(kwargs['args']) < 1:
        update.message.reply_text('Please supply a name')
        return

    machine_name = kwargs['args'][0]
    if not machine_name in machines:
        update.message.reply_text('Could not find ' + machine_name)
    else:
        addr = machines[machine_name]
        send_magic_packet(bot, update, addr, machine_name)


def cmd_wake_mac(bot, update, **kwargs):
    if not authorize(bot, update):
        return
    if 'args' not in kwargs or len(kwargs['args']) < 1:
        update.message.reply_text('Please supply a mac address')
        return

    mac_address = kwargs['args'][0]
    send_magic_packet(bot, update, mac_address, mac_address)


def cmd_list(bot, update):
    if not authorize(bot, update):
        return
    msg = '{num} Stored Machines:\n'.format(num=len(machines))
    for name, addr in machines.items():
        msg += '{n}: {a}\n'.format(n=name, a=addr)
    update.message.reply_text(msg)


def cmd_add(bot, update, **kwargs):
    if not authorize(bot, update):
        return
    if 'args' not in kwargs or len(kwargs['args']) < 2:
        update.message.reply_text('Please supply a name and mac address')
        return

    machine_name = kwargs['args'][0]
    addr = kwargs['args'][1]
    if machine_name in machines:
        update.message.reply_text('Name already added')
        return

    if not is_valid_name(machine_name):
        update.message.reply_text('Name is invalid')
        return

    try:
        addr = normalize_mac_address(addr)
    except ValueError as e:
        update.message.reply_text(str(e))
        return

    machines[machine_name] = addr
    update.message.reply_text('Added new machine')

    try:
        write_to_disk()
    except:
        update.message.reply_text('Could not write changes to disk')


def cmd_remove(bot, update, **kwargs):
    if not authorize(bot, update):
        return
    if 'args' not in kwargs or len(kwargs['args']) < 1:
        update.message.reply_text('Please supply a name')
        return

    machine_name = kwargs['args'][0]
    if not machine_name in machines:
        update.message.reply_text('Could not find ' + machine_name)
        return

    del machines[machine_name]
    update.message.reply_text('Removed machine')

    try:
        write_to_disk()
    except:
        update.message.reply_text('Could not write changes to disk')

##
# Other Functions
##

def error(bot, update, error):
    logger.warning('Update "{u}" caused error "{e}"'.format(u=update, e=error))


def send_magic_packet(bot, update, mac_address, display_name):
    try:
        wol.wake(mac_address)
    except ValueError as e:
        update.message.reply_text(str(e))
        return
    poke = 'Sending magic packets...\n 彡ﾟ◉ω◉ )つー☆ﾟ.*･{name}｡ﾟ'
    update.message.reply_text(poke.format(name=display_name))


def user_is_allowed(uid):
    return str(uid) in config.ALLOWED_USERS


def authorize(bot, update):
    if not user_is_allowed(update.message.from_user.id):
        update.message.reply_text('You are not authorized to use this bot.\n' +
                'To set up your own visit https://github.com/os-sc/wolbot')
        return False
    return True


def is_valid_name(name):
    pattern = '[^_a-z0-9]'
    return not re.search(pattern, name)


def normalize_mac_address(addr):
    if len(addr) == 12:
        pass
        return config.MAC_ADDR_SEPARATOR.join(addr[i:i+2] for i in range(0,12,2))
    elif len(addr) == 12 + 5:
        sep = addr[2]
        return addr.replace(sep, config.MAC_ADDR_SEPARATOR)
    else:
        raise ValueError('Incorrect MAC address format')


def write_to_disk():
    csv=''
    for name, addr in machines.items():
        csv += '{n};{a}\n'.format(n=name, a=addr)

    with open(config.STORAGE_PATH, 'w') as f:
        f.write(csv)


def read_from_disk():
    # Warning: file contents will not be validated
    if not os.path.isfile(config.STORAGE_PATH):
        return
    with open(config.STORAGE_PATH, 'r') as f:
        for i, line in enumerate(f):
            name, addr = line.split(';', 1)
            machines[name] = addr.strip()


def main():
    read_from_disk()

    # Set up updater
    updater = Updater(config.TOKEN)
    disp = updater.dispatcher

    # Add handlers
    disp.add_handler(CommandHandler('help',    cmd_help))
    disp.add_handler(CommandHandler('list',    cmd_list))
    disp.add_handler(CommandHandler('wake',    cmd_wake,     pass_args=True))
    disp.add_handler(CommandHandler('wakemac', cmd_wake_mac, pass_args=True))
    disp.add_handler(CommandHandler('add',     cmd_add,      pass_args=True))
    disp.add_handler(CommandHandler('remove',  cmd_remove,   pass_args=True))

    disp.add_error_handler(error)

    # Start bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()


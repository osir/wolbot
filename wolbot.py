#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os.path
import logging
import re

from telegram import (InlineKeyboardButton,
        InlineKeyboardMarkup)
from telegram.ext import (Updater,
        CommandHandler,
        MessageHandler,
        Filters,
        CallbackQueryHandler)
import version
import config
import wol

# Compatible storage file version with this code
STORAGE_FILE_VERSION = '2.0'

logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO)
logger = logging.getLogger(__name__)
machines = []


class Machine:
    def __init__(self, mid, name, addr):
        self.id = mid
        self.name = name
        self.addr = addr


##
# Command Handlers
##

def cmd_help(bot, update):
    log_call(update)
    help_message = """
    (*≧▽≦) WOLBOT v{v} (≧▽≦*)

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
    """.format(v=version.V)
    update.message.reply_text(help_message)


def cmd_wake(bot, update, **kwargs):
    log_call(update)
    # Check correctness of call
    if not authorize(bot, update):
        return
    if 'args' not in kwargs or len(kwargs['args']) < 1:
        if not len(machines):
            update.message.reply_text('Please add a machine with the /add command first!')
        markup = InlineKeyboardMarkup(generate_machine_keyboard(machines))
        update.message.reply_text('Please select a machine to wake:', reply_markup=markup)
        return

    # Parse arguments and send WoL packets
    machine_name = kwargs['args'][0]
    for m in machines:
        if m.name == machine_name:
            send_magic_packet(bot, update, m.addr, m.name)
            return
    update.message.reply_text('Could not find ' + machine_name)


def cmd_wake_keyboard_handler(bot, update):
    try:
        n = int(update.callback_query.data)
    except ValueError:
        pass
    matches = [m for m in machines if m.id == n]
    if len(matches) < 1:
        return
    send_magic_packet(bot, update, matches[0].addr, matches[0].name)


def cmd_wake_mac(bot, update, **kwargs):
    log_call(update)
    # Check correctness of call
    if not authorize(bot, update):
        return
    if 'args' not in kwargs or len(kwargs['args']) < 1:
        update.message.reply_text('Please supply a mac address')
        return

    # Parse arguments and send WoL packets
    mac_address = kwargs['args'][0]
    send_magic_packet(bot, update, mac_address, mac_address)


def cmd_list(bot, update):
    log_call(update)
    # Check correctness of call
    if not authorize(bot, update):
        return

    # Print all stored machines
    msg = '{num} Stored Machines:\n'.format(num=len(machines))
    for m in machines:
        msg += '#{i}: "{n}" → {a}\n'.format(i=m.id, n=m.name, a=m.addr)
    update.message.reply_text(msg)


def cmd_add(bot, update, **kwargs):
    log_call(update)
    # Check correctness of call
    if not authorize(bot, update):
        return
    if 'args' not in kwargs or len(kwargs['args']) < 2:
        update.message.reply_text('Please supply a name and mac address')
        return

    # Parse arguments
    machine_name = kwargs['args'][0]
    addr = kwargs['args'][1]

    # Validate and normalize arguments
    if any(m.name == machine_name for m in machines):
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

    # Add machine to list
    machines.append(Machine(get_highest_id()+1, machine_name, addr))
    update.message.reply_text('Added new machine')

    # Save list
    try:
        write_savefile(config.STORAGE_PATH)
    except:
        update.message.reply_text('Could not write changes to disk')


def cmd_remove(bot, update, **kwargs):
    log_call(update)
    # Check correctness of call
    if not authorize(bot, update):
        return
    if 'args' not in kwargs or len(kwargs['args']) < 1:
        update.message.reply_text('Please supply a name')
        return

    # Parse arguments and look for machine to be deleted
    machine_name = kwargs['args'][0]
    if not any(m.name == machine_name for m in machines):
        update.message.reply_text('Could not find ' + machine_name)
        return

    # Delete machine
    for i, m in enumerate(machines):
        if m.name == machine_name:
            del machines[i]
            update.message.reply_text('Removed machine ' + machine_name)

    # Save list
    try:
        write_savefile(config.STORAGE_PATH)
    except:
        update.message.reply_text('Could not write changes to disk')

##
# Other Functions
##

def error(bot, update, error):
    logger.warning('Update "{u}" caused error "{e}"'.format(u=update, e=error))


def log_call(update):
    uid = update.message.from_user.id
    cmd = update.message.text.split(' ', 1)
    if len(cmd) > 1:
        logger.info('User [{u}] invoked command {c} with arguments [{a}]'
                .format(c=cmd[0], a=cmd[1], u=uid))
    else:
        logger.info('User [{u}] invoked command {c}'
                .format(c=cmd[0], u=uid))


def send_magic_packet(bot, update, mac_address, display_name):
    try:
        wol.wake(mac_address)
    except ValueError as e:
        update.message.reply_text(str(e))
        return
    poke = 'Sending magic packets...\n 彡ﾟ◉ω◉ )つー☆ﾟ. {name}'.format(
            name=display_name)

    if update.callback_query:
        update.callback_query.edit_message_text(poke)
    else:
        update.message.reply_text(poke)


def generate_machine_keyboard(machines):
    kbd = []
    for m in machines:
        btn = InlineKeyboardButton(m.name, callback_data=m.id)
        kbd.append([btn])
    return kbd


def user_is_allowed(uid):
    return str(uid) in config.ALLOWED_USERS


def authorize(bot, update):
    if not user_is_allowed(update.message.from_user.id):
        logger.warning('Unknown User {fn} {ln} [{i}] tried to call bot'.format(
                fn=update.message.from_user.first_name,
                ln=update.message.from_user.last_name,
                i=update.message.from_user.id))
        update.message.reply_text('You are not authorized to use this bot.\n'
                + 'To set up your own visit https://github.com/os-sc/wolbot')
        return False
    return True


def is_valid_name(name):
    pattern = '[^_a-z0-9]'
    return not re.search(pattern, name)


def normalize_mac_address(addr):
    if len(addr) == 12:
        pass
        return config.MAC_ADDR_SEPARATOR.join(
                addr[i:i+2] for i in range(0,12,2))
    elif len(addr) == 12 + 5:
        sep = addr[2]
        return addr.replace(sep, config.MAC_ADDR_SEPARATOR)
    else:
        raise ValueError('Incorrect MAC address format')


def get_highest_id():
    highest = -1
    for m in machines:
        if m.id > highest:
            highest = m.id
    return highest


def write_savefile(path):
    logger.info('Writing stored machines to "{p}"'.format(p=path))
    csv=''
    # Add meta settings
    csv += '$VERSION={v}\n'.format(v=STORAGE_FILE_VERSION)

    # Add data
    for m in machines:
        csv += '{i};{n};{a}\n'.format(i=m.id, n=m.name, a=m.addr)

    with open(path, 'w') as f:
        f.write(csv)


def read_savefile(path):
    logger.info('Reading stored machines from "{p}"'.format(p=path))
    # Warning: file contents will not be validated
    if not os.path.isfile(path):
        return
    with open(path, 'r') as f:
        for i, line in enumerate(f):
            # Handle Settings
            if line.startswith('$VERSION'):
                _, value = line.split('=', 1)
                if not value.strip() == STORAGE_FILE_VERSION:
                    raise ValueError('Incompatible storage file version')
            else:
                mid, name, addr = line.split(';', 2)
                machines.append(Machine(int(mid), name, addr.strip()))


def main():
    logger.info('Starting bot version {v}'.format(v=version.V))
    read_savefile(config.STORAGE_PATH)

    # Set up updater
    updater = Updater(config.TOKEN)
    disp = updater.dispatcher

    # Add handlers
    disp.add_handler(CommandHandler('help',    cmd_help))
    disp.add_handler(CommandHandler('list',    cmd_list))
    disp.add_handler(CommandHandler('wake',    cmd_wake,     pass_args=True))
    disp.add_handler(CallbackQueryHandler(cmd_wake_keyboard_handler))
    disp.add_handler(CommandHandler('wakemac', cmd_wake_mac, pass_args=True))
    disp.add_handler(CommandHandler('add',     cmd_add,      pass_args=True))
    disp.add_handler(CommandHandler('remove',  cmd_remove,   pass_args=True))

    disp.add_error_handler(error)

    # Start bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()


# Changelog

## 2.2

- Added the `/ip` command
- Added config entries for `/ip` command: `IP_WEBSERVICE`, `IP_REGEX`

## 2.1

- If `/wake` is called and there is only one machine stored in the machine list
    that one will automatically be selected

## 2.0

- The bot now displays a selection menu when no argument to `/wake` is provided
- A lot of new logging has been added
- Each machine now gets a persistent numerical ID
    which is also stored in the savefile
- The savefile format has been updated to include the ID
- The savefile now supports a savefile version to prevent errors
    when reading an outdated savefile version


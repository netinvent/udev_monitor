# udev_monitor
# Monitor linux udev events and execute actions on detection
# Designed to execute actions when USB devices are plugged-in / removed


[![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)
[![Percentage of issues still open](http://isitmaintained.com/badge/open/netinvent/udev_monitor.svg)](http://isitmaintained.com/project/netinvent/udev_monitor "Percentage of issues still open")
[![linux-tests](https://github.com/netinvent/udev_monitor/actions/workflows/linux.yaml/badge.svg)](https://github.com/netinvent/udev_monitor/actions/workflows/linux.yaml)
[![GitHub Release](https://img.shields.io/github/release/netinvent/udev_monitor.svg?label=Latest)](https://github.com/netinvent/udev_monitor/releases/latest)


udev_monitor works with Linux udev and monitors it's events.
Upon a specific event for a given device, it will execute an action.

Setup:
```
pip install udev_monitor
```

Example:
Run script `/usr/local/bin/myscript.sh` everytime USB device 0665:5161 is added or removed
```
udev_monitor.py --devices 0665:5161 --udev-actions add,remove --filters=usb --action /usr/local/bin/restart_nut_driver.sh
```

Full usage:
```
--devices           List of comma separated devices to monitor. Example:
                    '0665:5161, 8086:1234'
--udev-actions      List of udev events which should trigger and action
                    Valid actions are: 'add', 'remove', 'change', 'online', 'offline'. Defaults to 'add, change, online'
--filters           List of comma separated udev monitor filters. Filters are applied with OR logic. Example:
                    'usb,tty'
--action            Path to script. Script will get detected device as only argument.
--timeout           Maximum execution time for script
--config            Optional path to config file
```

Configuration file layout:
```
[UDEV_MONITOR]
devices = '0665:5161'
filters = 'usb'
action = '/path/to/script.sh'
udev_events = 'add'
timeout = 3600
```
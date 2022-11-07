#! /usr/bin/env python
#  -*- coding: utf-8 -*-
#
# This file is part of udev_monitor

"""
udev_monitor looks for given devices and executes an action when detected.
Of course, using udev, it only works for Linux

Versioning semantics:
    Major version: backward compatibility breaking changes
    Minor version: New functionality
    Patch version: Backwards compatible bug fixes

"""

__intname__ = "udev_monitor"
__author__ = "Orsiris de Jong"
__copyright__ = "Copyright (C) 2022 Orsiris de Jong"
__description__ = "udev_monitor triggers action on plugged in devices"
__licence__ = "BSD 3 Clause"
__version__ = "1.1.0"
__build__ = "2022110602"
__compat__ = "python3.6+"


import sys
import os
from typing import Callable, List
from argparse import ArgumentParser

try:
    from pyudev import Context, Monitor
except ModuleNotFoundError:
    print("Cannot load pyudev module")
import logging
from command_runner import command_runner
from ofunctions.threading import threaded, no_flood
from time import sleep
from datetime import datetime
import threading
from configparser import ConfigParser

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

TIMEOUT = 3600  # Default command timeout
WAIT_BEFORE_CALLBACK = 2  # How many seconds before we launch our callback, so the device driver for plugged in device is properly loaded


def load_config(config_file: str):
    conf = ConfigParser()
    conf.read(config_file)
    return conf


def monitor_udev(
    devices_to_monitor: List[str],
    udev_events: List,
    callback: Callable,
    action: str,
    filters: List[str],
):

    logger.info(
        "Setting up udev monitor for devices: {} with filters: {}".format(
            devices_to_monitor, filters
        )
    )

    ctx = Context()
    monitor = Monitor.from_netlink(ctx)
    if filters:
        for filter in filters:
            monitor.filter_by(subsystem=filter)

    for device in iter(monitor.poll, None):
        if device.action in udev_events:
            """
            Plugging a USB device may trigger multiple add actions here, eg a 4G modem would add multiple ttyUSB ports and a cdc-wdm port
            We'll launch callback_no_flood that will only execute callback once per CALLBACK_FLOOD_TIMEOUT
            """

            vendor_id = device.get("ID_VENDOR_ID")
            model_id = device.get("ID_MODEL_ID")
            if vendor_id and model_id:
                found_device = "{}:{}".format(vendor_id, model_id)
                device_node = device.device_node
                if device_node:
                    logger.info(
                        "Device {} added as {}".format(found_device, device.device_node)
                    )
                if found_device in devices_to_monitor:
                    logger.info(
                        "Executing callback function with device id {} as argument.".format(
                            found_device
                        )
                    )
                    callback(found_device, action)
            else:
                logger.debug("Added device: {}".format(device.device_node))


@threaded
@no_flood(WAIT_BEFORE_CALLBACK)
def callback(device, action):
    """
    Callback function is threaded so we don't wait for it to complete before getting next device add actions
    Callback funtcion has a no_flood decorator so it won't execute multiple times for the same device in a 3 second timespan
    """

    # Arbitrary second delay so most device add actions for the same device are executed
    sleep(WAIT_BEFORE_CALLBACK)

    if action:
        """
        You could write any alternative python action here instead of executing a command
        """

        cmd = "{} {}".format(action, device)
        logger.info("Executing comamnd {}".format(cmd))
        exit_code, output = command_runner(cmd, timeout=TIMEOUT, method="poller")
        if exit_code != 0:
            logger.error(
                "Erorr while executing action for device {}. Exit code: {}, output was:".format(
                    device, exit_code
                )
            )
            logger.error(output)
        else:
            logger.info("Command executed succesfully. Output was:")
            logger.info(output)
    else:
        logger.info("No action configured.")


if __name__ == "__main__":
    if os.name == "nt":
        print("This program is designed to run on Linux with udev only.")
        sys.exit(4)
    parser = ArgumentParser(prog="udev_monitor.py", description="Udev hook")

    parser.add_argument(
        "-c",
        "--config",
        type=str,
        dest="config_file",
        default=None,
        help="Optional config file",
    )

    parser.add_argument(
        "-u",
        "--udev-actions",
        type=str,
        default="add, change, online",
        help="udev action to monitor. Usual actions are 'add', 'remove', 'change', 'online', 'offline'. Defaults to 'add, change, online'",
    )

    parser.add_argument(
        "-f",
        "--filters",
        type=str,
        required=False,
        dest="filters",
        default=None,
        help="comma separated list of udev device type filters, eg: 'usb,tty'",
    )

    parser.add_argument(
        "-d",
        "--devices",
        type=str,
        required=False,
        dest="devices",
        default=None,
        help="comma separated list of devices to monitor, eg: '0123:2345,9876:ABCD'",
    )

    parser.add_argument(
        "-a",
        "--action",
        required=False,
        type=str,
        dest="action",
        default=None,
        help="action to execute on device detection. Action will get device VENDOR:MODEL as argument",
    )

    parser.add_argument(
        "-t",
        "--timeout",
        required=False,
        type=int,
        dest="timeout",
        default=None,
        help="Maximum execution time in seconds for the action. Defaults to 3600",
    )

    args = parser.parse_args()

    devices = None
    filters = None
    action = None

    if args.config_file:
        conf = load_config(args.config_file)
        try:
            devices = conf["UDEV_MONITOR"]["devices"]
        except KeyError:
            devices = None
        try:
            filters = conf["UDEV_MONITOR"]["filters"]
        except KeyError:
            devices = None
        try:
            TIMEOUT = conf["UDEV_MONITOR"]["timeout"]
        except KeyError:
            pass
        try:
            action = conf["UDEV_MONITOR"]["action"]
        except KeyError:
            pass
        try:
            udev_events = conf["UDEV_MONITOR"]["udev_events"]
        except KeyError:
            pass
    else:
        if args.devices:
            devices = args.devices
        if args.filters:
            filters = args.filters
        if args.action:
            action = args.action
        if args.timeout:
            TIMEOUT = args.timeout
        if args.udev_events:
            udev_events = args.udev_events

        if devices:
            devices = [device.strip() for device in devices.split(",")]
        if filters:
            filters = [filter.strip() for filter in filters.split(",")]
        if udev_events:
            udev_events = [
                udev_event.strip() for udev_event in udev_events.split(",")
            ]

    try:
        monitor_udev(devices, udev_events, callback, action, filters)
    except KeyboardInterrupt:
        logger.info("Program interrupted by CTRL+C")
        sys.exit(3)
    except Exception as exc:
        logger.error("Program failed with error %s" % exc)
        logger.error("Trace:", exc_info=True)

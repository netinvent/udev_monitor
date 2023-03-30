# udev_monitor
# Monitor linux udev events and execute actions on detection
## Designed to execute actions when USB devices are plugged-in / removed


[![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)
[![Percentage of issues still open](http://isitmaintained.com/badge/open/netinvent/udev_monitor.svg)](http://isitmaintained.com/project/netinvent/udev_monitor "Percentage of issues still open")
[![linux-tests](https://github.com/netinvent/udev_monitor/actions/workflows/pylint-linux.yaml/badge.svg)](https://github.com/netinvent/udev_monitor/actions/workflows/pylint-linux.yaml)
[![GitHub Release](https://img.shields.io/github/release/netinvent/udev_monitor.svg?label=Latest)](https://github.com/netinvent/udev_monitor/releases/latest)


udev_monitor works with Linux udev and monitors it's events.
Upon a specific event for a given device (in VENDOR_ID:PRODUCT_ID format), it will execute an action.

udev_monitor has been used to:
 - Re-attach USB devices to virtual machines after they're unplugged - plugged in again
 - Run a full USB reset when device is plugged in (fixes some of the USB UPS that identify as Cypress Semiconductor USB to Serial)

# Setup
```
pip install udev_monitor
```

# Quickstart example
This is a realworld example to detect most USB UPS and execute a script upon plug-in.

Run script `/usr/local/bin/restart_nut_driver.sh` with argument `0665:5161` everytime USB device with vendor id 0665 and product id 5161 is added or removed
```
udev_monitor --devices 0665:5161 --udev-actions add,remove --filters=usb --action /usr/local/bin/restart_nut_driver.sh
```

# Full usage
```
--devices           List of comma separated devices to monitor. Example:
                    '0665:5161, 8086:1234'
                    If no devices are given, all devices are monitored.
--udev-actions      List of udev events which should trigger and action
                    Valid actions are: 'add', 'remove', 'change', 'online', 'offline'. Defaults to 'add, change, online'
--filters           List of comma separated udev monitor filters. Filters are applied with OR logic. Example:
                    'usb,tty'
--action            Path to script. Script will get detected device as only argument.
--timeout           Maximum execution time for script
--config            Optional path to config file
```

# Optional configuration file layout
```
[UDEV_MONITOR]
devices = '0665:5161'
filters = 'usb'
action = '/path/to/script.sh'
udev_events = 'add'
timeout = 3600
```

# Setting monitor up as a service

- copy file `scripts/udev_monitor@.service` to `/etc/systemd/system`
- Reload daemons
- Create configuration file in `/etc/udev_monitor` from example config in `scripts/udev_monitor.conf.example`
- Launch service

Example:
```
cp scripts/udev_monitor\@.service to /etc/systemd/system
systemctl daemon-reload

mkdir /etc/udev_monitor
cat << EOF > /etc/udev_monitor/udev_monitor1.conf
devices = '0665:5161'
filters = 'usb'
action = '/path/to/script.sh'
udev_events = 'add'
timeout = 3600
EOF

systemctl enable --now udev_monitor@udev_monitor1.conf
```

You can launch multiple udev_monitor instances by creating multiple conf files and loading them with:
```
systemctl enable --now udev_monitor@umy_ups.conf
systemctl enable --now udev_monitor@my_modem.conf
systemctl enable --now udev_monitor@my_harddrive.conf
```

## Further examples

### Automatically attach an USB device (4G modem) to a KVM virtual machine with libvirt and udev_monitor

Let's imagine we have a Sierra 4G model that identifies as 1199:9097, and we would like to attach it to VM modem.vm.local

Grab yourself a copy of usb_reset via `pip install usb_reset`

Create the following script as `/usr/local/bin/attach_modem.sh` and make it executable with `chmod +x /usr/local/bin/attach_modem.sh`

```
#!/usr/bin/env bash

# /usr/local/bin/usb_reset.py --reset-device --device 1199:9071

virsh detach-device sms.badmin.local /root/4G_modem.xml
virsh attach-device sms.badmin.local /root/4G_modem.xml
```

Create the file `/root/4G_modem.xml` containing:
```
    <hostdev mode='subsystem' type='usb' managed='yes'>
      <source>
        <vendor id='0x1199'/>
        <product id='0x9071'/>
      </source>
    </hostdev>
```

Now we must execute that script everytime the USB 4G modem is plugged-in, so we get to re-attach it to the VM.

In order to do so, let's create the following conf file in `/etc/udev_monitor/modem.conf`
```
[UDEV_MONITOR]
devices = 1199:9071
filters = usb
action = /usr/local/bin/attach_modem.sh
udev_events = add
timeout = 300
```

Now let's create a systemd service by copying `udev_monitor@.service` from this git repo to `/etc/systemd/system`

Once this is done, we just can activate the service with `systemctl enable --now udev_monitor@modem.conf`

### Reset a lawless UPS USB

Some of the USB uninterrupted power supplies (smaller devices) have a quite unreliable USB/Serial interface.
Sometimes it's needed to restart the usb port for the device to work properly.

In that case, we can use udev_monitor to trigger a usb reset on device plug-in.

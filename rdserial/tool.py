# rdserialtool
# Copyright (C) 2019 Ryan Finnie
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.

import argparse
import sys
import os
import logging
import time

from rdserial import __version__
import rdserial.device
import rdserial.um.tool
import rdserial.dps.tool

def parse_args(argv=None, address_required=True, command_required=True):
    """Parse user arguments."""
    if argv is None:
        argv = sys.argv

    parser = argparse.ArgumentParser(
        description='rdserialtool ({})'.format(__version__),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        prog=os.path.basename(argv[0]),
        epilog=((
            'Additional options are available for each command; see `{} {{command}} --help`' +
            'for more details.'
        ).format(os.path.basename(argv[0]))),
    )

    parser.add_argument(
        '--version', '-V', action='version',
        version=__version__,
        help='Report the program version',
    )

    parser.add_argument(
        '--quiet', '-q', action='store_true',
        help='Suppress human-readable stderr information',
    )
    parser.add_argument(
        '--debug', action='store_true',
        help='Print extra debugging information.',
    )

    if address_required:
        device_group = parser.add_mutually_exclusive_group(required=True)
        device_group.add_argument(
            '--bluetooth-address', '-b',
            help='Bluetooth EUI-48 address of the device',
        )
        device_group.add_argument(
            '--serial-device', '-s',
            help='Serial filename (e.g. /dev/rfcomm0) of the device',
        )

    parser.add_argument(
        '--bluetooth-port', type=int, default=1,
        help='Bluetooth RFCOMM port number',
    )
    parser.add_argument(
        '--baud', type=int, default=9600,
        help='Serial port baud rate',
    )
    parser.add_argument(
        '--connect-delay', type=float, default=0.3,
        help='Seconds to wait after connecting to the serial port',
    )
    parser.add_argument(
        '--json', action='store_true',
        help='Output JSON data',
    )
    parser.add_argument(
        '--watch', action='store_true',
        help='Repeat data collection until cancelled',
    )
    parser.add_argument(
        '--watch-seconds', type=float, default=2.0,
        help='Number of seconds between collections in watch mode',
    )
    parser.add_argument(
        '--trend-points', type=int, default=5,
        help='Number of points to remember for determining a trend in watch mode',
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')
    rdserial.um.tool.add_subparsers(subparsers)
    rdserial.dps.tool.add_subparsers(subparsers)

    args = parser.parse_args(args=argv[1:])

    if command_required and args.command is None:
        parser.error('Command required')

    return args

class RDSerialTool:
    """Main class to interface with the device"""
    def _setup_logging(self):
        logging_format = '%(message)s'
        if self.args.debug:
            logging_level = logging.DEBUG
            logging_format = '%(asctime)s %(levelname)s: %(message)s'
        elif self.args.quiet:
            logging_level = logging.ERROR
        else:
            logging_level = logging.INFO
        logging.basicConfig(
            format=logging_format,
            level=logging_level,
        )

    def _setup_args(self,
                    bluetooth_address,
                    device,
                    connect_delay,
                    bluetooth_port,
                    quiet,
                    debug,
                    baud,
                    write_json,
                    watch,
                    watch_seconds,
                    trend_points):
        address_required = bluetooth_address is None
        device_required = device is None
        self.args = parse_args(address_required=address_required, command_required=device_required)
        if not address_required:
            self.args.bluetooth_address = bluetooth_address
            self.args.serial_device = None
        if not device_required:
            self.args.command = device
        if connect_delay is not None:
            self.args.connect_delay = connect_delay
        if quiet is not None:
            self.args.quiet = quiet
        if debug is not None:
            self.args.debug = debug
        if baud is not None:
            self.args.baud = baud
        if write_json is not None:
            self.args.json = write_json
        if watch is not None:
            self.args.watch = watch
        if watch_seconds is not None:
            self.args.watch_seconds = watch_seconds
        if trend_points is not None:
            self.args.trend_points = trend_points
        if bluetooth_port is not None:
            self.args.bluetooth_port = bluetooth_port

    def main(self,
             bluetooth_address=None,
             device=None,
             connect_delay=None,
             bluetooth_port=None,
             callback=None,
             quiet=None,
             debug=None,
             baud=None,
             write_json=None,
             watch=None,
             watch_seconds=None,
             trend_points=None):
        """Connects to the specified device"""

        self._setup_args(bluetooth_address,
                         device,
                         connect_delay,
                         bluetooth_port,
                         quiet,
                         debug,
                         baud,
                         write_json,
                         watch,
                         watch_seconds,
                         trend_points)
        self._setup_logging()

        logging.info('rdserialtool %s', __version__)
        logging.info('Copyright (C) 2019 Ryan Finnie')
        logging.info('')

        if self.args.serial_device:
            logging.info('Connecting to %s %s', self.args.command.upper(), self.args.serial_device)
            self.socket = rdserial.device.Serial(
                self.args.serial_device,
                baudrate=self.args.baud,
            )
        else:
            logging.info('Connecting to %s %s',
                         self.args.command.upper(),
                         self.args.bluetooth_address)
            self.socket = rdserial.device.Bluetooth(
                self.args.bluetooth_address,
                port=self.args.bluetooth_port,
            )
        self.socket.connect()
        logging.info('Connection established')
        logging.info('')
        time.sleep(self.args.connect_delay)

        if self.args.command in ('um24c', 'um25c', 'um34c'):
            tool = rdserial.um.tool.Tool(self, callback)
        elif self.args.command == 'dps':
            tool = rdserial.dps.tool.Tool(self, callback)
        ret = tool.main()

        self.socket.close()
        return ret

def main(**kwargs):
    """Runs the tool"""
    return RDSerialTool().main(**kwargs)


if __name__ == '__main__':
    sys.exit(main())

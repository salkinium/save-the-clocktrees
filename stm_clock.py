#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, sys, math, glob, re
sys.path.append(os.path.join(os.path.dirname(__file__), 'xpcc',  'tools', 'device_file_generator'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'xpcc',  'tools', 'logger'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'xpcc',  'tools', 'device_files'))

from reader import XMLDeviceReader
from peripheral import Peripheral
from register import Register
from lxml import etree

from logger import Logger
from device_identifier import DeviceIdentifier

from stm import stm32_defines
from stm import stm32f1_remaps
from stm import stm32_memory

class STMClockReader(XMLDeviceReader):
	""" STMClockReader
	This STM specific clock tree reader knows the structure and
	translates the data into a platform independent format.
	"""

	def __init__(self, deviceName, logger=None):

		XMLDeviceReader.__init__(self, os.path.join(os.path.dirname(__file__), 'data', deviceName + '.xml'), logger)
		self.name = deviceName
		self.id = DeviceIdentifier(self.name.lower())

		if logger:
			logger.info("STMClockReader: Parsing '{}'".format(self.id.string))

	def __repr__(self):
		return self.__str__()

	def __str__(self):
		return "STMClockReader({}, [\n{}])".format(os.path.basename(self.name), ",\n".join(map(str, self.properties)))


if __name__ == "__main__":
	level = 'debug'
	logger = Logger(level)
	device = STMClockReader('STM32F100', logger)

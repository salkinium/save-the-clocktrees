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

		rccName = "RCC-STM32F100_rcc_v1_0_Modes"
		self.rcc = XMLDeviceReader(os.path.join(os.path.dirname(__file__), 'data', rccName + '.xml'), logger)

		# clock sources
		self.sources = []

		sources = self.query("//Clock/Tree/Element[contains(@type,'Source')]")

		for source in sources:
			clks = []
			for p in self._getParameter(source.get('refParameter')):
				c = {'speed': 'high' if 'HS' in p.get('Name') else 'low',
					 'type': 'unknown',
					 'location': ('ex' if 'E_' in p.get('Name') else 'in') + 'ternal'}
				if p.get('Min') == p.get('Max'):
					c.update({'fixed': p.get('DefaultValue')})
				else:
					c.update({'min': p.get('Min'), 'max': p.get('Max')})

				if len(p.getchildren()) > 0:
					t = p.getchildren()[0].get('Expression')
					if 'Oscillator' in t:
						c['type'] = 'crystal'
					elif 'ByPass' in t:
						c['type'] = 'clock'
				clks.append(c)

			specified = 'crystal'
			for c in [c for c in clks if c['type'] is not 'unknown']:
				specified = c['type']

			for c in [c for c in clks if c['type'] is 'unknown']:
				c['type'] = 'clock' if specified is 'crystal' else 'crystal'

			self.sources.extend(clks)

		for s in self.sources:
			print s



	def __repr__(self):
		return self.__str__()

	def __str__(self):
		return "STMClockReader({}, [\n{}])".format(os.path.basename(self.name), ",\n".join(map(str, self.properties)))

	def _getParameter(self, parameter):
		return self.rcc.query("//IP/RefParameter[@Name='{}']".format(parameter))


if __name__ == "__main__":
	level = 'info'
	logger = Logger(level)
	device = STMClockReader('STM32F100', logger)

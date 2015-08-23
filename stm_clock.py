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

from clock_element import STMClockElement
from clock_element import STMClockConnection
from clock_element import STMXMLParameter


class STMClockReader(XMLDeviceReader):
	""" STMClockReader
	This STM specific clock tree reader knows the structure and
	translates the data into a platform independent format.
	"""

	def __init__(self, deviceName, logger=None):

		XMLDeviceReader.__init__(self, os.path.join(os.path.dirname(__file__), 'data', deviceName + '.xml'), logger)
		self.name = deviceName
		self.id = DeviceIdentifier(self.name.lower())

		self.log.info("STMClockReader: Parsing '{}'".format(self.id.string))

		rccName = "RCC-STM32F100_rcc_v1_0_Modes"
		self.rcc = XMLDeviceReader(os.path.join(os.path.dirname(__file__), 'data', rccName + '.xml'), logger)

		self.parameters = []
		for parameter in self.rcc.query("//RefParameter"):
			p = STMXMLParameter(parameter.attrib)

			p.values = [c.attrib for c in parameter.getchildren() if c.tag == 'PossibleValue']
			p.conditions = [c.attrib for c in parameter.getchildren() if c.tag == 'Condition']

			self.parameters.append(p)
			# self.log.debug("STMClockReader: {}".format(p))

		self.elements = []
		self.connections = []

		# read all elements and connections
		for element in self.query("//Element"):
			e = STMClockElement(element.attrib)
			# only store the ids of the in and outputs for now
			e.outputs = [c.get('to') for c in element.getchildren() if c.tag == 'Output']
			e.inputs = [c.get('from') for c in element.getchildren() if c.tag == 'Input']
			e.conditions = [c.attrib for c in element.getchildren() if c.tag == 'Condition']
			if 'refParameter' in e.attributes:
				e.parameters = [p for p in self.parameters if p.name == e.attributes['refParameter']]

			# create the connections
			for c in [c.attrib for c in element.getchildren() if c.tag in ['Input', 'Output']]:
				conn = STMClockConnection(e, c)
				if conn not in self.connections:
					self.connections.append(conn)

			self.elements.append(e)

		for signal in self.query("//Signals/Signal"):
			param = signal.get('refParameter')
			if param is not None and param != "":
				conn = [c for c in self.connections if c.id == signal.get('id')][0]
				conn.attributes['refParameter'] = param

		# connect the element input and outputs with the actual object, not just the id string
		for element in self.elements:
			inputs = []
			outputs = []
			for i in element.inputs:
				inputs.extend([e for e in self.elements if e.id == i])
			for o in element.outputs:
				outputs.extend([e for e in self.elements if e.id == o])
			element.inputs = inputs
			element.outputs = outputs
			self.log.debug("STMClockReader: {}".format(element))

		for conn in self.connections:
			if 'refParameter' in conn.attributes:
				conn.parameters = [p for p in self.parameters if p.name == conn.attributes['refParameter']]

			conn.begin = filter(lambda e: e.id == conn.begin, self.elements)[0]
			conn.end = filter(lambda e: e.id == conn.end, self.elements)[0]
			self.log.debug("STMClockReader: {}".format(conn))

		# find the SYSCLK connection
		sysClk = filter(lambda c: c.id == 'SYSCLK', self.connections)[0]

		# find the clock tree elements
		clockTree = sysClk.begin.getChildren()
		# and the system clock elements
		systemClock = sysClk.end.getParents()

		print '### ClockTree ###'
		for e in clockTree:
			print e

		print '\n### SytemClock ###'
		for e in systemClock:
			print e

		"""
		# simple filtering now possible
		self.sources = filter(lambda e: len(e.inputs) == 0, self.elements)
		self.sinks = filter(lambda e: len(e.outputs) == 0, self.elements)
		self.divisors = filter(lambda e: e.type == 'devisor', self.elements) # yes, ST misspelled divisor
		self.multiplexors = filter(lambda e: e.type == 'multiplexor', self.elements)
		self.multiplicator = filter(lambda e: e.type == 'multiplicator', self.elements)
		"""

		""" # don't read the stuff manually
		# clock sources
		self.sources = []
		for source in self.query("//Clock/Tree/Element[contains(@type,'Source')]"):
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
		"""




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

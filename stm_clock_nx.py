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
from clock_element import STMXMLValue
from clock_element import STMXMLCondition

import networkx as nx
# import matplotlib.pyplot as plt


class STMClockReader(XMLDeviceReader):
	""" STMClockReader
	This STM specific clock tree reader knows the structure and
	translates the data into a platform independent format.
	"""

	def __init__(self, deviceName, logger=None):

		XMLDeviceReader.__init__(self, os.path.join(os.path.dirname(__file__), 'data', deviceName + '.xml'), logger)
		self.name = deviceName
		self.id = DeviceIdentifier(self.name.lower())
		self.graph = nx.DiGraph()

		self.log.info("STMClockReader: Parsing '{}'".format(self.id.string))

		rccName = "RCC-STM32F100_rcc_v1_0_Modes"
		self.rcc = XMLDeviceReader(os.path.join(os.path.dirname(__file__), 'data', rccName + '.xml'), logger)

		self.parameters = []
		for parameter in self.rcc.query("//RefParameter"):
			p = STMXMLParameter(parameter.attrib)

			p.values = [STMXMLValue(c.attrib) for c in parameter.getchildren() if c.tag == 'PossibleValue']
			p.conditions = [STMXMLCondition(c.attrib) for c in parameter.getchildren() if c.tag == 'Condition']

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



			for p in element.parameters:
				# self.graph.add_edge(element, p)
				# for v in p.values:
				# 	self.graph.add_edge(p, v)
				# for c in p.conditions:
				# 	self.graph.add_edge(p, c)

				if 'IP' in p.attributes:
					for ip in p.attributes['IP'].split(','):
						e = STMClockElement({'id': ip, 'type': "ip"})
						# self.graph.add_edge(e, element)

			for i in element.inputs:
				self.graph.add_edge(i, element)
			for o in element.outputs:
				self.graph.add_edge(element, o)

		for conn in self.connections:
			if 'refParameter' in conn.attributes:
				conn.parameters = [p for p in self.parameters if p.name == conn.attributes['refParameter']]

			conn.begin = filter(lambda e: e.id == conn.begin, self.elements)[0]
			conn.end = filter(lambda e: e.id == conn.end, self.elements)[0]
			self.log.debug("STMClockReader: {}".format(conn))

		"""
		# find the SYSCLK connection
		sysClk = filter(lambda c: c.id == 'SYSCLK', self.connections)[0]

		# find the clock tree elements
		systemClockSink = sysClk.begin.getChildren()
		# and the system clock elements
		systemClockSource = sysClk.end.getParents()

		print '\n### SytemClock ###'
		for e in clockTree:
			print e

		print '\n### Sources ###'

		for e in systemClock:
			print e

		# simple filtering now possible

		self.sinks = filter(lambda e: len(e.outputs) == 0, self.elements)

		for e in self.elements:
			print e

		self.sources = []
		for s in filter(lambda e: len(e.inputs) == 0, self.elements):
			self.sources.extend(self._parseSource(s))

		print '\n### Sources ###'
		for s in self.sources:
			print s



		self.pll = {'name': 'Pll', 'inputs': [], 'multiplier':'2:16'}
		# find the PLL Multiplier connection
		pllMul = filter(lambda c: c.id == 'PLLMUL', self.elements)[0]


		print '\n### Pll ###'
		pllMulPaths = pllMul.getParentPaths()
		pllInputs = []
		for path in pllMulPaths:
			print [p.id for p in path]
			sources = self._parseSource(path[-1])
			for source in sources:
				input = {'name': source['name']}
				divisor = filter(lambda c: c.type == 'devisor', path)[0]
				print divisor.parameters
		"""

		# nx.draw_graphviz(self.graph)
		# plt.savefig("path.png")
		nx.write_dot(self.graph,'file.dot')



	def _parseNumberRange(self, parameters):
		print parameters


	def _parseSource(self, source):
		sources = []
		for p in source.parameters:
			c = {'speed': 'high' if 'HS' in source.id else 'low',
			     'type': 'unknown',
			     'location': ('ex' if 'E_' in source.id else 'in') + 'ternal'}
			if 'Min' not in p.attributes or (p.attributes['Min'] == p.attributes['Max']):
				c.update({'fixed': p.attributes['DefaultValue']})
			else:
				c.update({'min': p.attributes['Min'], 'max': p.attributes['Max']})

			if len(p.conditions) > 0:
				t = p.conditions[0]['Expression']
				if 'Oscillator' in t:
					c['type'] = 'crystal'
				elif 'ByPass' in t:
					c['type'] = 'clock'

			sources.append(c)

		specified = 'crystal'
		for c in [c for c in sources if c['type'] is not 'unknown']:
			specified = c['type']

		for c in [c for c in sources if c['type'] is 'unknown']:
			c['type'] = 'clock' if specified is 'crystal' else 'crystal'

		for s in sources:
			s['name'] = "{}{}{}".format(
					"LowSpeed" if s['speed'] == 'low' else "",
					s['location'].capitalize(),
					s['type'].capitalize())

		return sources

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

# -*- coding: utf-8 -*-
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'xpcc',  'tools', 'logger'))

from lxml import etree
from logger import Logger

class STMClockConnection:
	""" STMClockConnection
	Base class for all inputs of a clock element.
	"""

	def __init__(self, element, attributes):
		self.attributes = attributes

		self.id = attributes['signalId']

		self.begin = element.id
		self.end = element.id

		if 'to' in attributes:
			self.end = attributes['to']
		if 'from' in attributes:
			self.begin = attributes['from']

		# remove unnecessary keys from attributes
		keys = ('signalId', 'to', 'from')
		map(self.attributes.__delitem__, filter(self.attributes.__contains__, keys))


	def __repr__(self):
		return self.__str__()

	def __str__(self):
		s = "Connection( {} ---{}--> {}".format(self.begin, self.id, self.end)
		if len(self.attributes) > 0:
			s += ', '
			s += ', '.join(["{}='{}'".format(key, value) for (key, value) in self.attributes.items()])
		return s + ' )'

	def __eq__(self, other):
		if not isinstance(other, STMClockConnection):
			return False

		return (self.begin == other.begin and
				self.id == other.id and
				self.end == other.end)

	def __hash__(self):
		return hash(self.begin, self.id, self.end)


class STMClockElement:
	""" STMClockElement
	Base class for all elements of a clock tree.
	"""

	def __init__(self, attributes):
		self.attributes = attributes
		self.id = attributes['id']
		self.type = attributes['type']

		self.inputs = []
		self.outputs = []

		# remove unnecessary keys from attributes
		keys = ('id', 'x', 'y', 'type')
		map(self.attributes.__delitem__, filter(self.attributes.__contains__, keys))

	def __repr__(self):
		return self.__str__()

	def __str__(self):
		inputs = self.inputs
		outputs = self.outputs
		# rather complicated, but necessary to avoid recursions!
		if len(self.inputs) > 0 and isinstance(self.inputs[0], STMClockElement):
			inputs = [i.id for i in self.inputs]
		if len(self.outputs) > 0 and isinstance(self.outputs[0], STMClockElement):
			outputs = [o.id for o in self.outputs]

		inputs = '' if len(inputs) == 0 else "{} => ".format(inputs)
		outputs = '' if len(outputs) == 0 else " => {}".format(outputs)

		s = "Element( {}{}{}".format(inputs, self.id, outputs)
		if len(self.attributes) > 0:
			s += ', '
			s += ', '.join(["{}='{}'".format(key, value) for (key, value) in self.attributes.items()])
		return s + ' )'


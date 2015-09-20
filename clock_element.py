# -*- coding: utf-8 -*-
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'xpcc',  'tools', 'logger'))

from lxml import etree
from logger import Logger

class STMXMLParameter:
	""" STMXMLParameter
	Class for describing the reference parameters IPs.
	"""

	def __init__(self, attributes):
		self.attributes = attributes
		self.name = attributes['Name']
		self.type = attributes['Type']
		self.values = []
		self.conditions = []

		# remove unnecessary keys from attributes
		keys = ('Name', 'Type', 'Visible', 'Comment')
		map(self.attributes.__delitem__, filter(self.attributes.__contains__, keys))

	def __repr__(self):
		return self.__str__()

	def __str__(self):
		s = "XmlParameter( {}{}{}".format(self.name,
			'' if len(self.values) == 0 else ':{}'.format(len(self.values)),
			'' if len(self.conditions) == 0 else '?{}({})'.format(len(self.conditions), ",".join([c['Expression'] for c in self.conditions])))
		if len(self.attributes) > 0:
			s += ', ' + ', '.join(["{}='{}'".format(key, value) for (key, value) in self.attributes.items()])
		return s + ' )'

class STMClockConnection:
	""" STMClockConnection
	Class for describing the graph edges (=connections) of the clock tree.
	"""

	def __init__(self, element, attributes):
		self.attributes = attributes
		self.id = attributes['signalId']

		self.begin = element.id
		self.end = element.id
		self.parameters = []

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
		s = "Connection( {} ---{}--> {}".format(self.begin.id, self.id, self.end.id)
		if len(self.parameters) > 0:
			s += ',\n\t' + ',\n\t'.join(map(str, self.parameters))
		return s + ' )'

	def __eq__(self, other):
		if not isinstance(other, STMClockConnection):
			return False
		return (self.id == other.id)

	def __hash__(self):
		return hash(self.id)


class STMClockElement:
	""" STMClockElement
	Class for describing the graph vertexes (=elements) of the clock tree.
	"""

	def __init__(self, attributes):
		self.attributes = attributes
		self.id = attributes['id']
		self.type = attributes['type']

		self.inputs = []
		self.outputs = []
		self.conditions = []
		self.parameters = []

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
		name = self.id
		if len(self.conditions) > 0:
			name += '?{}'.format(len(self.conditions))

		s = "Element( {}{}{}".format(inputs, name, outputs)
		if len(self.parameters) > 0:
			s += ',\n\t' + ',\n\t'.join(map(str, self.parameters))
		if len([a for a in self.attributes.keys() if a != 'refParameter']) > 0:
			s += ',\n\t' + ',\n\t'.join(["{}='{}'".format(key, value) for (key, value) in self.attributes.items() if key != 'refParameter'])
		return s + ' )'

	def getParents(self):
		parents = list(self.inputs)
		for parent in parents:
			parents.extend(parent.getParents())
		parents = list(set(parents))
		return parents

	def getChildren(self):
		children = list(self.outputs)
		for child in children:
			children.extend(child.getChildren())
		children = list(set(children))
		return children

	def __eq__(self, other):
		if not isinstance(other, STMClockElement):
			return False
		return (self.id == other.id)

	def __hash__(self):
		return hash(self.id)


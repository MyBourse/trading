import yf
from util import *
import logging
import time
from datetime import datetime
import itertools as it
import pprint

class Quote(object):
	def __init__(self, d, o, h, l, c, v):
		self.d = datetime(*(time.strptime(d, '%Y-%m-%d')[0:6]))
		self.o = float(o)
		self.h = float(h)
		self.l = float(l)
		self.c = float(c)
		self.v = float(v)
 
	def __str__(self):
		return '[' + datetime.strftime(self.d, '%Y-%m-%d') + '] ' + str(self.a)
 
	def __repr__(self):
		return self.__str__()

class Cube(object):
	'''symbol -> key -> date -> value'''
	def __init__(self):
		self.dates = []
		self.symbols = []
		self.keys = []
		self.data = {}
	
	def add_quote(self, symbol, quote):
		self.add(quote.d, symbol, 'open', quote.o)
		self.add(quote.d, symbol, 'high', quote.h)
		self.add(quote.d, symbol, 'low', quote.l)
		self.add(quote.d, symbol, 'close', quote.c)
		self.add(quote.d, symbol, 'volume', quote.v)
	
	def add(self, date, symbol, key, value):
		if date not in self.dates:
			self.dates.append(date)
		if symbol not in self.symbols:
			self.symbols.append(symbol)
		if key not in self.keys:
			self.keys.append(key)
			
		data_key = (symbol, key)
		if data_key not in self.data:
			self.data[data_key] = {}		
		if date not in self.data[data_key]:
			self.data[data_key][date] = value
			
	def write_to_csv(self, location, extra_series = None):
		headings = list(it.product(self.symbols, self.keys))
				
		out = 'date,' + ','.join(['_'.join(heading) for heading in headings])
		if extra_series is not None:
			for series in extra_series:
				out += ',' + series['name']
				
		for dt in sorted(self.dates):
			out += '\n' + datetime.strftime(dt, '%Y-%m-%d') + ',' + \
				','.join([str(self.data[(symbol, key)][dt]) for symbol, key in headings])
			if extra_series is not None:
				for series in extra_series:
					out += ',' + str(series['data'][dt])
		write_to_file(location, out)
		
	def get_dates(self):
		return sorted(self.dates)
		
	def go_back(self, dt, num_days):
		dates = self.get_dates()
		index_of = dates.index(dt)
		return dates[max(0, index_of - num_days)]
		
	def get_values(self, symbol, key):
		values = []
		for dt in self.get_dates():
			values.append(self.data[(symbol, key)][dt])
		return values
		
	def pretty_print(self):
		pp = pprint.PrettyPrinter(indent=4)
		pp.pprint(self.data)

def load(symbols, start, end):		
	if type(symbols) is str:
		symbols = [symbols]
	
	cube = Cube()
	for symbol in symbols:
		logging.debug('Loading data for {}, {} - {}.'.format(symbol, start, end))
		filename = '{}_{}_{}.pkl'.format(symbol, start, end)
		if file_exists(filename):
			data = pickle_load(filename)
		else:
			data = yf.get_historical_prices(symbol, start[:4]+'-'+start[4:6]+'-'+start[6:], end[:4]+'-'+end[4:6]+'-'+end[6:])
			pickle_it(filename, data)
		try:
			for i in range(0, len(data)):
				d = str(data.index[i].date())
				o = data.iloc[i].Open
				h = data.iloc[i].High
				l = data.iloc[i].Low
				c = data.iloc[i].Close
				v = data.iloc[i].Volume
				quote = Quote(d, o, h, l, c, v)
				cube.add_quote(symbol, quote)
		except Exception as e:
			print('Trouble getting data for {}'.format(symbol))
			print('{}'.format(e))
	return cube
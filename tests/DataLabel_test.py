import pandas as pd
import remi.gui as gui
from remi import start, App

from common_addons import *

testdata = [('ID', 'Enabled', 'First Name', 'Last Name'),
			(101, True, 'Danny zag lange loesje lopen langs de lange lindelaan', 'Young'),
			(102, False, 'Christine', 'Holland'),
			(103, True, 'Lars', 'Gordon'),
			(104, False, 'Roberto', 'Robitaille'),
			(105, True, 'Maria', 'Papadopoulos')]

test_df = pd.DataFrame({'ID': [101, 102, 103, 104, 105], 'Enabled': [True, False, True, False, True],
						'First Name': ['Danny zag lange loesje lopen langs de lange lindelaan', 'Christine',
									   'Lars', 'Roberto', 'Maria'],
						'Last Name': ['Young', 'Holland', 'Gordon', 'Robitaille', 'Papadopoulos']})

tooltips = [[None, 'Dit is de enabled kolom', None, 'Achternaam'],
			['Rare achternaam<br/>Tweede regel<br/>Derde regel', '101 tweede col', '101 derde col'],
			['Dit is dus 102'],
			['Dit is dus 103 <br/>Tweede regel', None, '103 derde col'],
			['en dit 104 <br/>Extra regel <br/>En nog een..'],
			['en dit 105 <br/>En nog een..'],
			]
tt_df = pd.DataFrame(tooltips)

class Test_Dp(object):
	def __init__(self, **kwargs):
		for k,v in kwargs.items():
			setattr(self, k, v)
			
test_dp = Test_Dp(name='test', group='group1', value=20.0, unit='kWh', read_write='RW', text='dit is een test')



test_df = pd.DataFrame(testdata[1:], columns=testdata[0])


def jsem_decorator(cls):
	print(type(cls))
	orig__init__ = cls.__init__
	def new__init__(self, *args, **kwargs):
		dp = kwargs.pop('datapoint', None)
		cond_format = kwargs.pop('cond_format', None)
		parent = kwargs.pop('parent', None)

		rw_fields = {
			'name': {'value': dp.name, 'style': 'position:absolute;left:5%'},
			'subcat': {'value': dp.sub_cat, 'style': 'position:absolute;left:25%'},
			'value': {'value': dp.value, 'style': 'position:absolute;left:50%'},
			'unit': {'value': dp.unit, 'style': 'position:absolute;left:70%'},
			'input': {'value': '', 'style': 'position:absolute;left:80%;background:white', 'is_input': True}
				}
		
		ro_fields = {
			'name': {'value': dp.name, 'style': 'position:absolute;left:2%'},
			'subcat': {'value': dp.sub_cat, 'style': 'position:absolute;left:35%;font-size:0.8em'},
			'value': {'value': dp.value, 'style': 'position:absolute;left:60%'},
			'unit': {'value': dp.unit, 'style': 'position:absolute;left:70%;font-size:0.8em'},
				}

		if dp.read_write.upper() == "RW":
			kwargs['fields'] = rw_fields
		else:
			kwargs['fields'] = ro_fields

		orig__init__(self, *args, **kwargs)

		if cond_format:
			if type(cond_format) is not list:    self.cond_format = [cond_format]
		self.cond_format = cond_format
		self.datapoint = dp
		self.parent = parent
		if self.parent: self.parent.append(self)
		if self.datapoint: self.datapoint.subscribed_widgets.append(self)
	
	cls.__init__ = new__init__
	
	return cls


class DataPoint:
	def __init__(self, name='', value=2.4):
		self.name = name
		self.value = value
		self.unit = 'kWh'
		self.sig_rule ='warning=>2.0&alarm=>2.5'
		self.subscribed_widgets = []
		self.read_write = 'R'
		self.sub_cat = 'test categorie'

@jsem_decorator
class JsemDataLabel(DataLabel):
	def __init__(self, **kwargs):
		super(JsemDataLabel, self).__init__(**kwargs)
		
		

class MyApp(App):
	def __init__(self, *args):
		super(MyApp, self).__init__(*args)
	
	def main(self):
		# Add my own stylesheet
		style_str = get_extra_css('css')
		head = self.page.get_child('head')
		head.add_child(str(id(style_str)), style_str)
		
		self.top_cont = gui.Container(style='position:absolute;height:90%;width:90%;top:5%;left:5%')
		
		self.lbl0 = DataLabel(fields={
			'name': {'value':'test', 'style':'position:absolute;left:5%'},
			'groep': {'value':'meetwaardes', 'style':'position:absolute;left:25%'},
			'waarde': {'value': 2.4, 'style': 'position:absolute;left:60%'},
			'input': {'value': 2.4, 'style': 'position:absolute;left:80%;background:white', 'is_input':True}
			},
			style='position:absolute;top:30%;left:40%;width:300px;height:20px;background:yellow')

		self.lbl1 = DataLabel(naam='test', groep='meetwaardes', waarde=2.4,
							 style='position:absolute;top:50%;left:40%;width:300px;height:20px;justify-content:space-between;background:yellow')
		self.top_cont.append([self.lbl0, self.lbl1])

		dp = DataPoint('testDataPoint', 3.0)
		self.lbl2 = JsemDataLabel(parent=self.top_cont, datapoint=dp,
								  # cond_format = [
									# 		dict(cond="gte", check_value=0.95, true="red", false="green", qit=True),
									# 		dict(cond="gte", check_value=0.9, true="orange", false="green", qit=True),
									# 		dict(cond="ste", check_value=5.0, true="red", false="green", qit=True),
									# 		dict(cond="ste", check_value=10.0, true="orange", false="green", qit=True)
									# 			],
								  style='position:absolute;top:10%;left:40%;width:300px;height:20px;justify-content:space-between;background:orange')

		
		return self.top_cont
	


# starts the web server
start(MyApp, port=8082)
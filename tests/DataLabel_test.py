import pandas as pd
import remi.gui as gui
from remi import start, App

from common_addons.common_utils import get_extra_css
from common_addons.remi_addons import DataLabel, EditableTable

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


class MyApp(App):
	def __init__(self, *args):
		super(MyApp, self).__init__(*args)
	
	def main(self):
		# Add my own stylesheet
		style_str = get_extra_css('css')
		head = self.page.get_child('head')
		head.add_child(str(id(style_str)), style_str)
		
		self.top_cont = gui.Container(style='position:absolute;height:90%;width:90%;top:5%;left:5%')
		
		# self.lbl = DataLabel(text='test_text',
		# 					 name='test datapoint', value=20.0, group='testgroep', unit='kW',
		# 					 style='position:absolute;top:40%;left:40%;background:yellow',
		# 					 config={'show_text':True},
		# 					 value_style='background:green',
		# 					 name_style='font-size:1.5em;font-weight:bold',
		# 					 unit_style='font-size:0.7em;color:red')

		self.lbl = DataLabel(test_dp,
							 style='position:absolute;top:40%;left:40%;background:yellow',
							 config={'show_text':True},
							 value_style='background:green',
							 name_style='font-size:1.5em;font-weight:bold',
							 unit_style='font-size:0.7em;color:red')

		self.top_cont.append(self.lbl)
		
		return self.top_cont
	


# starts the web server
start(MyApp, port=8082)
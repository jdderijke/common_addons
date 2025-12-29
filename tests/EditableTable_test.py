import pandas as pd
import remi.gui as gui
from remi import start, App

from common_addons.common_utils import get_extra_css
from common_addons.remi_addons import EditableTable

testdata = [('ID', 'Enabled', 'First Name', 'Last Name'),
			(101, True, 'Danny zag lange loesje lopen langs de lange lindelaan', 'Young'),
			(102, False, 'Christine', 'Holland'),
			(103, True, 'Lars', 'Gordon'),
			(104, False, 'Roberto', 'Robitaille'),
			(105, True, 'Maria', 'Papadopoulos')]

test_df = pd.DataFrame({'ID':[101,102,103,104,105], 'Enabled':[True,False,True,False,True],
						'First Name':['Danny zag lange loesje lopen langs de lange lindelaan', 'Christine',
									  'Lars', 'Roberto', 'Maria'],
						'Last Name':['Young','Holland','Gordon','Robitaille','Papadopoulos']})

tooltips = [[None, 'Dit is de enabled kolom', None, 'Achternaam'],
			['Rare achternaam<br/>Tweede regel<br/>Derde regel', '101 tweede col', '101 derde col'],
			['Dit is dus 102'],
			['Dit is dus 103 <br/>Tweede regel',None,'103 derde col'],
			['en dit 104 <br/>Extra regel <br/>En nog een..'],
			['en dit 105 <br/>En nog een..'],
			]
tt_df = pd.DataFrame(tooltips)

# test_df = pd.DataFrame(testdata[1:], columns=testdata[0])


class MyApp(App):
	def __init__(self, *args):
		super(MyApp, self).__init__(*args)
	
	def main(self):
		# Add my own stylesheet
		style_str = get_extra_css('css')
		head = self.page.get_child('head')
		head.add_child(str(id(style_str)), style_str)
		
		self.top_cont = gui.Container(style='position:absolute;height:90%;width:90%;top:5%;left:5%')
		self.lbl = gui.Label(text='This is a LABEL!', style='position:relative;margin:20px')
		
		# self.table_cont = gui.Container(style='height:auto; width:50%; overflow-y:scroll; background-color:silver')
		self.table_cont = gui.Container(style='width:auto; margin:20px; background-color:silver')

		self.table = EditableTable(theme='theme0', sort_on_title_click=False, style='table-layout:auto; white-space:nowrap; font-size:1.0em')
		# self.table.set_data(test_df, tt_df, editable=['ID','Last Name'], tip_type='item',
		# 							tt_style='color:black;height:auto;left:50%;top:50%;width:auto;min-width:150px')
		self.table.set_data(test_df, editable=['ID','Last Name'])

		self.table.on_item_changed.connect(self.on_item_changed_hndlr)
		# self.table.onclick.connect(self.table_click)
		
		self.table_cont.append(self.table)
		
		self.top_cont.append([self.lbl, self.table_cont])
		
		self.hbox = gui.HBox(style='width:50%;justify-content:space-around')
		self.btn1 = gui.Button('Click to reset')
		self.btn1.onclick.connect(self.button1_onclick)
		self.hbox.append(self.btn1)
		
		self.btn2 = gui.Button('Click to get data')
		self.btn2.onclick.connect(self.button2_onclick)
		self.hbox.append(self.btn2)
		self.top_cont.append(self.hbox)

		
		return self.top_cont
	
	def table_click(self, *args, **kwargs):
		print(args)
		print(kwargs)
	
	def on_table_row_click(self, table, row, item):
		self.lbl.set_text('Table Item clicked: ' + item.get_text())
		# get the rownumber by finding the key (string representing rownumber) of the tablerow widget in de children dict of the table
		rownumber = int(list(table.children.keys())[list(table.children.values()).index(row)])
		if rownumber == 0:
			# the header
			return
		for row_widget in table.children.values():
			if row_widget is row:
				row_widget.style['background-color'] = 'red'
			else:
				row_widget.style.pop('background-color', None)
	
	def on_item_changed_hndlr(self, table, item, new_value, row, column):
		print(f'cel in row {row}, col {column}, changed to: {new_value}')
		print(self.table.table_data)
		# print(test_df)

	def button1_onclick(self, btn, **kwargs):
		print('Reset Button clicked')
		self.table.reset()

	def button2_onclick(self, btn, **kwargs):
		print('Get Data Button clicked')
		print('List')
		data = self.table.get_data()
		for row in data:
			print(row)
		print()
		print('DataFrame')
		print (self.table.get_data(as_dataframe=True))

# starts the web server
start(MyApp, port=8082)
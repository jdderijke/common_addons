import copy
from argparse import ArgumentError
from collections import ChainMap
from typing import Union

import remi.gui as gui
import remi
from common_utils import update_css_stylestr, AttrDict, Waitkey, dump
from remi import TableTitle
from remi.gui import decorate_event, decorate_set_on_listener

from pygal import Config, DateTimeLine, Line
from pygal.style import Style

import markdown
from textwrap import dedent
import pandas as pd


class EditableTable(gui.Table):
	"""
	Simplified version of the Remi table widget.
	"""
	
	def __init__(self, theme='theme1', sort_on_title_click=True, **kwargs):
		"""
		:param args: See gui.Container.__init__()

		:param theme:					Specify a specific CSS theme, default empty string (equals theme1)
		:param sort_on_title_click: 	Sort the table when the title row is clicked
		:keyword style:					Sets the style of the table parent object
		"""
		self.__column_count = 0
		super(EditableTable, self).__init__(**kwargs)
		self.css_display = 'table'
		self.add_class(theme)
		self.sort_on_title_click = sort_on_title_click
		# if self.sort_on_title_click:
		# self.on_table_row_click.connect(self.on_table_row_click)
		
		self.row_count = 0
		self.column_count = 0
		self.sort_item = None
		
		self.table_data = []
		""" The internally used table_data list including tooltips and index"""
		
		self.initial_list = []
		""" initially loaded list, used for reset/cancel purpose"""
		
		self.editable = []
		self._editable_check = []
		self.toggle = []
		self._toggle_check = []
		self.toggle_in_progress = False
		
		self.tooltips = []
		self.tip_type = 'item'
		self.tt_style = ''
		self.rowdata_links = []
		
		self.btn_columns = {}
	
	def set_data(self, table_data: Union[list[list], pd.DataFrame],
				 tooltips: Union[list[list[str]], pd.DataFrame] = None, editable: list[str] = None,
				 toggle: list[str] = None, buttons: dict = None,
				 tip_type: str = 'item', tt_style: str = '', update_only=False, rowdata_links: list = None, **kwargs):
		"""
			Normal way to fill the table after the constructor.
			The table is build from a List of Lists (All rows MUST have equal length and first row is header/title row),
			or from a DataFrama (column names are header/title row). Optionally tooltips can be specified which will show
			on mouseover on item or row level (tip_type).

			:param table_list:		Can be a list[list] or a DataFrame. In case of list[list] first row is header/title row,
									all rows must have equal lengths.
			:param tooltips: 		Can be a list[list] or a DataFrame. In both cases first row is title tooltips. The list[list]
									or DataFrame will be automatically redimensioned to fit the table_data
			:param editable: 		list with column names for editable columns
			:param toggle:			(only works on editable columns with boolean values)
									list with column names with a toggle functionality, a small 'T' button will be shown in de column title
									when clicked all True values in that column will be flipped to False and vice versa
			:param buttons:			(only works on non_editable columns)
									Creates a button in every cell of the specified column. When
									clicked the hndlr routine will be called with the arguments: btn, row_nr, col_nr, table_item). The table_item
									has an attribute data_link (populated from the rowdata_links list) that can be used to pass meaningful
									information to the handler routine.
									format: buttons={'col_name':{'hndlr':handler_routine, 'symbol':'symbol_to_show_on_button', 'style':'button specific style'}}
			:param tip_type: 		tooltip behaviour, item or row
			:param tt_style:		Style string for the tooltip
			:param update_only:		Update or refresh the table maintaining any active sort
			:param rowdata_links:	Key or link to datastructures represented in the table title and datarows.
									accessible through Tablerow data_link attribute. and Tableitem data_link attribute.
									When providing this list make sure there is also a rowdata_link for the title row provided...
									if nothing is provided None will be used

			:return:

			Examples:
				| test = EditableTable()
				|
				| test.set_data([['column1','column2','column3'],[True,'John','Doe'],[False,'Remi','GUI']],
				|						editable=['column1', 'column3'], toggle=['column1'],
				|						buttons={'column2':{'hndlr':lambda *args:print('clicked'), 'symbol':'>'}})

			:raises TypeError:	When the table_data is ot of type list[list] or pd.DataFrame
			:raises ValueError:	When the table_data list of lists contains rows of un-equal length


		"""
		
		if type(table_data) is list:
			data = copy.deepcopy(table_data)
		elif type(table_data) is pd.DataFrame:
			header = table_data.columns.tolist()
			data = [header] + table_data.values.tolist()
		else:
			raise TypeError(f'Table list should be of type list or DataFrame.. not {type(table_data)}')
		
		if not update_only:
			# store the initial_list for reset/cancel purposes
			self.initial_list = data
			
			# determine the table dimensions and check table validity
			max_columns = max(map(len, data))
			min_columns = min(map(len, data))
			if max_columns != min_columns: raise ValueError('Passed table rows must have identical column count...')
			self.column_count = max_columns
			self.row_count = len(data)
			# if len(data) > 1:
			# 	self.column_types = [type(x) for x in data[1][:self.column_count]]
			# else:
			# 	self.column_types = [None for x in range(self.column_count)]
			#
			# for row in data[1:]:
			# 	for teller, col in enumerate(row):
			# 		if type(col) is not self.column_types[teller]:
			# 			raise TypeError(f'{data[0][teller]}--All values in 1 column should be of the same type...')
			
			# pre-checks and conversions
			if tooltips is None: tooltips = [[]]
			if type(tooltips) is pd.DataFrame and tooltips.empty: tooltips = [[]]
			if type(tooltips) is pd.DataFrame: tooltips = tooltips.values.tolist()
			tooltips = self._re_dim(tooltips, self.row_count, self.column_count)
			
			# store arguments like editable, the tooltips, type and style for reset/cancel purposes
			self.editable = editable if editable is not None else []
			self._editable_check = [data[0][x] in self.editable for x in range(self.column_count)]
			self.toggle = toggle if toggle is not None else []
			self._toggle_check = [data[0][x] in self.toggle for x in range(self.column_count)]
			
			self.buttons = buttons if buttons is not None else {}
			self._button_check = [data[0][x] in self.buttons for x in range(self.column_count)]
			self._button_hndlr = [self.buttons.get(data[0][x], {}).get('hndlr', None) for x in range(self.column_count)]
			self._button_symb = [self.buttons.get(data[0][x], {}).get('symbol', '') for x in range(self.column_count)]
			self._button_style = [self.buttons.get(data[0][x], {}).get('style', '') for x in range(self.column_count)]

			self.rowdata_links = [None for x in range(len(self.initial_list))]
			if rowdata_links is not None: self.rowdata_links = self.rowdata_links[:-len(rowdata_links)] + rowdata_links

			self.tooltips = tooltips
			self.tip_type = tip_type
			self.tt_style = tt_style
			# start with a clean empty table, reset the sort
			self.sort_item = None
			self._reverse_sort = [True for x in range(self.column_count)]
			self.empty()
		
		# construct a data structure with the table_data, the tooltips and an index (to store the original sort sequence)
		self.table_data = [data[x] + self.tooltips[x] + [self.rowdata_links[x]] + [x] for x in range(len(data))]
		
		
		if update_only and self.sort_item:
			# re-create the pre-existing sort in the table
			sorted_data = sorted(self.table_data[1:], key=lambda x: x[self.sort_item.column_number],
								 reverse=self._reverse_sort[self.sort_item.column_number])
			sorted_data = [self.table_data[0]] + sorted_data
			self.table_data = sorted_data
		
		self._build_table()
	
	def get_data(self, as_dataframe: bool = False) -> Union[list[list], pd.DataFrame]:
		"""
		Returns a list[list] with the current data of the table. First row is title row

		:param as_dataframe: Return result as a dataframe, column names from title row
		:return: list[list] or pd.DataFrame
		"""
		result = []
		# build a list with rows that only contain the columns of the original list and the index
		result = [row[:self.column_count] + [row[-1]] for row in self.table_data]
		# Now sort the rows as they show up in the index sequence
		result = sorted(result, key=lambda x: x[-1], reverse=False)
		# now remove the index column (last column)
		result = [row[:-1] for row in result]
		
		if as_dataframe:
			result = pd.DataFrame(data=result[1:], columns=result[0])
		
		return result
	
	def _build_table(self):
		
		for i in range(self.row_count):
			if str(i) in self.children:
				tr = self.get_child(str(i))
			else:
				tr = gui.TableRow()
				self.append(tr, str(i))
			tr.data_link = self.table_data[i][-2]
			
			# before we start with the columns in the table, check if there are btn columns defined
			
		
		
			for c in range(self.column_count):
				data = self.table_data[i][c]
				if str(c) in tr.children:
					ti = tr.get_child(str(c))
					ti.set_text(f'{data}')
					# mark the active sort column with a visible border
					if self.sort_item is ti: ti.style['border'] = 'solid 3px black'
				
				else:
					if i == 0:
						if self._toggle_check[c] and self._editable_check[c]:
							ti = gui.HBox(style='width:100%;height:100%;justify-content:space-between')
							ti.type = 'th'
							title = gui.Label(f'{data}', style='margin: 0px 5px 0px 0px')
							tgl_btn = gui.Button('T', style='height:100%;background:red;color:white;margin: 0px 0px 0px 5px')
							tgl_btn.onclick.connect(self.on_toggle, i, c, )
							ti.set_text = title.set_text
							ti.get_text = title.get_text
							ti.append([title, tgl_btn])
							
						else:
							ti = gui.TableTitle(f'{data}')
							
					else:
						# Not a title row
						if self._button_check[c] and not self._editable_check[c]:
							ti = gui.HBox(style='width:100%;height:100%;justify-content:space-between')
							ti.type = 'td'
							cell_txt = gui.Label(f'{data}', style='margin: 0px 5px 0px 0px')
							cell_btn = gui.Button(self._button_symb[c],
												  style='height:100%;background:grey;color:black;margin: 0px 0px 0px 5px')
							if self._button_style[c]: cell_btn.set_style(self._button_style[c])
							# cell_btn = gui.Button(u'\u8635', style='height:100%;background:grey;color:black')
							cell_btn.onclick.connect(self._button_hndlr[c], self, tr, ti, i, c,)
							ti.set_text = cell_txt.set_text
							ti.get_text = cell_txt.get_text
							
							# ti.set_text('pipo')
							
							ti.append([cell_txt, cell_btn])

						elif self._editable_check[c]:
							ti = TableCheckBox(data) if type(data) is bool else gui.TableEditableItem(f'{data}')
							ti.onchange.connect(self.on_item_changed, int(i), int(c))
						else:
							ti = gui.TableItem(f'{data}')
					
					tr.append(ti, str(c))
				
				# now deal with the data_link, they get sorted with the table_data and must be re-connected
				ti.data_link = self.table_data[i][-2]
				ti.column_name = self.initial_list[0][c]
				ti.column_number = c
				ti.row_number = i
				
				# The tooltips need to be connected, they may need to change because of a sort action
				tt_item_tip = self.table_data[i][self.column_count + c]
				if tt_item_tip:
					if '_tt' in ti.children: ti.remove_child(ti.get_child('_tt'))
					tt = gui.Widget(_type='div', _class='tiptext', style=self.tt_style)
					tt.add_child(str(id(tt_item_tip)), tt_item_tip)
					if self.tip_type.lower() == 'row' and c == 0:
						tr.add_class('hooverhere')
						ti.append(tt, key='_tt')
					elif self.tip_type.lower() == 'item':
						ti.add_class('hooverhere')
						ti.append(tt, key='_tt')
	
	def reset(self):
		"""
		Resets all values in the table to their initial values. Also resets sorting
		"""
		if self.initial_list:
			self.set_data(self.initial_list, self.tooltips, editable=self.editable,
						  tip_type=self.tip_type, tt_style=self.tt_style)
	
	def item_at(self, row, column):
		"""Returns the TableItem instance at row, column coordinates

		Args:
			row (int): zero based index
			column (int|str): zero based index or column title name
		"""
		if type(column) is str and not column.isnumeric():
			return self.children[str(row)].children[str(self.column_nr(column))]
		else:
			return self.children[str(row)].children[str(column)]
	
	def value_at(self, row, column):
		return self.item_at(row, column).get_text()
	
	def item_coords(self, table_item):
		"""Returns table_item's (row, column) cordinates.
		Returns None in case of item not found.

		Args:
			table_item (TableItem): an item instance
		"""
		for row_key in self.children.keys():
			for item_key in self.children[row_key].children.keys():
				if self.children[row_key].children[item_key] == table_item:
					return (int(row_key), int(item_key))
		return None
	
	def column_name(self, column_nr):
		return self.item_at(0, column_nr).get_text()
	
	def column_nr(self, column_name):
		for col_nr in range(self.column_count):
			if self.column_name(col_nr) == column_name:
				return col_nr
		return None
	
	def _re_dim(self, input_list, row_count, column_count):
		"""
		Forces a list[list] to expand or collaps to the specified row/column dimensions
		:param input_list: The llist of lists to be redimensioned
		:param row_count: The new row count
		:param column_count: The new column count
		:return: the redimensioned list
		"""
		# Force the list to be of the correct length, filled up by empty lists
		nw_list = input_list[:row_count] + [[None]] * (row_count - len(input_list))
		
		# Force the list entries to be of the correct length, filled up by None's
		for teller, _row in enumerate(nw_list):
			nw_list[teller] = nw_list[teller][:column_count] + [None] * (column_count - len(nw_list[teller]))
		return nw_list
	
	@decorate_event
	def on_item_changed(self, item, new_value, row, column):
		"""Event for the item change.

		Args:
			emitter (TableWidget): 	The emitter of the event.
			item (TableItem): 		The TableItem instance.
			new_value: 				New text content.
			row (int): 				row index.
			column (int): 			column index.
		"""
		casting_type = type(self.table_data[row][column])
		# if self.table_df is not None:
		# 	# casting_type = type(self.table_df.iat[row - 1, column])
		# 	self.table_df.iat[row - 1, column] = casting_type(new_value)
		self.table_data[row][column] = casting_type(new_value)
		
		return (item, new_value, row, column)
	
	@decorate_event
	def on_table_row_click(self, table_row, table_item):
		""" Event for the table row clicked
		:param table_row: 	Tablerow instance
		:param table_item: 	Tableitem instance, is TableTitle instance for a title row click..
		:return:
		"""
		# always reset the toggle, even if no sorting is enabled!
		if self.toggle_in_progress:
			self.toggle_in_progress = False
			return
		
		if not self.sort_on_title_click: return
		
		row, col = table_item.row_number, table_item.column_number
		if row == 0:
			# sort the content, keep the header
			# Give the active sort item a clearly visible border
			if self.sort_item: self.sort_item.style['border'] = ''
			self._reverse_sort[col] = not self._reverse_sort[col]
			sorted_data = sorted(self.table_data[1:], key=lambda x: x[col], reverse=self._reverse_sort[col])
			sorted_data = [self.table_data[0]] + sorted_data
			self.table_data = sorted_data
			self.sort_item = table_item
			self.sort_item.style['border'] = 'solid 3px black'
			# self.empty()
			self._build_table()
		return (table_row, table_item)
	
	@decorate_event
	def on_toggle(self, tgl_btn, row, column):
		"""
		Toggles the boolean value of the entries in the column
		 * Does NOT call the on_item_changed event...
		 * connect to the on_toggle event to do any actions needed beyond just toggling the values
		"""
		if not row == 0: return
		self.toggle_in_progress = True
		
		tmp_df = self.get_data(as_dataframe=True)
		tmp_df.iloc[:, column] = ~ tmp_df.iloc[:, column]
		self.set_data(tmp_df, update_only=True)
		return (row, column)


class TableCheckBox(gui.Container):
	"""item widget for the TableRow."""
	
	def __init__(self, checked: bool = False, *args, **kwargs):
		"""
		Args:
			checked (bool):
			kwargs: See Container.__init__()
		"""
		super(TableCheckBox, self).__init__(*args, **kwargs)
		self.type = 'td'
		self.checkbox = gui.CheckBox()
		self.append(self.checkbox)
		self.checkbox.set_value(checked)
		self.checkbox.onchange.connect(self.onchange)
	
	def get_text(self):
		return str(self.checkbox.get_value())
	
	def set_text(self, checked: str):
		self.checkbox.set_value(checked.lower() in ['true', 'waar', 'on', 'aan', 'yes'])
	
	def get_value(self):
		return self.checkbox.get_value()
	
	def set_value(self, checked: bool):
		self.checkbox.set_value(checked)
	
	# @decorate_set_on_listener("(self, emitter, new_value)")
	@decorate_event
	def onchange(self, emitter, new_value):
		return (new_value,)


class Conditional_Format_MixIn():
	def __init__(self, widget, property, cond_formats):
		self.widget = widget
		self.property = property
		self.cond_formats = cond_formats
		
	def do_cond_format(self, value):
		if self.value is None:
			check = False
		for cond_format in self.cond_formats:
			match cond_format['cond']:
				case "gt"|">":
					if self.value > cond_format["check_value"]: check=True
				case "gte"|">=":
					if self.value >= cond_format["check_value"]: check=True
				case "st"|"<":
					if self.value < cond_format["check_value"]: check=True
				case "ste"|"<=":
					if self.value <= cond_format["check_value"]: check=True
				case "eq"|"="|"==":
					if self.value == cond_format["check_value"]: check=True
				case "neq"|"!=":
					if self.value != cond_format["check_value"]: check=True
				case _:
					check = False
			if check:
				nw_style = cond_format.get('true', None)
				if nw_style: self.widget.set_style(f'{self.property}:{nw_style}')
				if cond_format.get('qit', False):
					return
			else:
				nw_style = cond_format.get('false', None)
				if nw_style: self.widget.set_style(f'{self.property}:{nw_style}')

		return


class DataLabel(gui.Container):
	"""
	Creates an enhanced label widget to be used for presenting a data element
	The label can contain the following elements:
	* name: The name of the data element, can be overruled by passing a text argument with an alternative name
	* group: The category of the data element
	* value: The value of the data element, with as sub element:
		* unit: The unit of the value
	* input: If the data element is RW, an input field element will be shown

	Styles for all elements normally inherit from the class style. To change the style for certain elements pass a stylestring
	for that element as argument
	"""
	cont_style = ('height:auto;width:auto;display:flex;justify-content:flex-start;align-items:center;'
				  'border-style:solid;border-width:2px;border-color:black;overflow:hidden;font-size:1.0em')
					
	default_field_style = 'width:auto;height:auto;font-size:1.0em'
	default_input_style = 'width:auto;height:auto;font-size:1.0em;border-style:solid;border-width:2px;border-color:black'
	
	config = {'fields':[{'name':'name', 'position':'left'},
						{'name':'value', 'position':'50%'},
						{'name':'input', 'position':'right', 'is_input':True}]}
	
	def __init__(self, fields=None, input_fields=None, field_pos=None, style='', **kwargs):
		"""
		:param fields:			A dictionary with the fieldnames (key) and per field a dictionary with the value, style and other field information
		:param input_fields:	A string or list[str], containing the names of the fields that must be ready to accept input (RW)
		:param field_pos:		An list[int] for the position of the different fields, in %.
								Omitting will result in auto positioning through the style settings
						
		lbl = DataLabel(naam='test', groep='measurements', waarde=2.15, input_fields='waarde', update_fields='waarde' ,
						field_pos=[0,20,40], style='position:absolute;left:5%;top:5%')
		lbl = DataLabel(fields={'naam':{'value':'test', 'position':'left'},
							   'groep':{'value':'measurements', 'style':'left:30%'},
							   'waarde':{'value':2.15, 'style':'left:60%', style='background:yellow', is_updated:True},
							   'input':{style:'background:orange', is_input:True}})
		:examples:
		lbl.waarde = 2.35
		lbl.update({'waarde':2.35})
		lbl.update(2.35)
		
		"""
		self.style = update_css_stylestr(self.cont_style, style)
		super().__init__(style=self.style, **kwargs)
		
		if fields is not None:
			self.fields = fields
		else:
			self.fields = {}
			
		for fieldname, fieldvalue in kwargs.items():
			self.fields[fieldname] = {'value':fieldvalue, 'is_input':False, 'is_updated':False, 'style':self.default_field_style}
		
		if input_fields:
			if type(input_fields) is not list: input_fields = [input_fields]
			for inp_field in input_fields:
				if inp_field in self.fields:
					self.fields[inp_field]['is_input'] = True
					
					
		for fieldname, field in self.fields.items():
			if not field.get('is_input', False):
				lbl = gui.Label(text=str(field.get('value','')), style=update_css_stylestr(self.default_field_style, field.get('style','')))
			else:
				lbl = gui.TextInput(style=update_css_stylestr(self.default_input_style, field.get('style','')))
				lbl.set_text(str(field.get('value','')))
				lbl.onchange.connect(self.onchange)
			self.append(lbl)
		
	@decorate_event
	def onchange(self, emitter, new_value:str):
		return (new_value,)


class MultilineLabel(gui.Widget):
	"""Multiple lines label with Markdown support

	"""
	
	def __init__(self, text: str = '', **kwargs):
		"""
		Multiple lines label with Markdown support

		Args:
			text (str): The Markdown text
		"""
		super().__init__(_type='div', **kwargs)
		self.text = text
		self.markdown_html = None
		if self.text: self.set_value(self.text, **kwargs)
	
	def set_value(self, text: str, **kwargs):
		self.empty()
		list_style = kwargs.pop('list_style', 'square')
		self.markdown_html = markdown.markdown(dedent(text), output_format='html')
		self.markdown_html = self.markdown_html.replace('<li>',
														f'<li style="display:list-item;list-style:{list_style};background-color:transparent">')
		self.add_child(str(id(self.markdown_html)), self.markdown_html)


class ALB_widget(gui.Container):
	@property
	def alb_value(self):
		return self._alb_value
	
	@alb_value.setter
	def alb_value(self, nw_value):
		self._alb_value = nw_value
	
	@property
	def min_value(self):
		return self._min_value
	
	@min_value.setter
	def min_value(self, nw_value):
		self._min_value = nw_value
	
	@property
	def max_value(self):
		return self._max_value
	
	@max_value.setter
	def max_value(self, nw_value):
		self._max_value = nw_value
	
	@property
	def value(self):
		return self._data_buffer[-1]
	
	@value.setter
	def value(self, nw_value):
		self._data_buffer = self._data_buffer[1:] + [nw_value]
		self.update_chart()
	
	def __init__(self, name: str, value: float = 11, min_value: int = 0, max_value: int = 25, alb_value: int = 20,
				 alb_state: bool = False, data_buffer_length: int = 100,
				 width: int = 300, height: int = 600, **kwargs):
		"""
		Displays a chart (typically for charting a current on L1, L2 or L3) with an ALB (active load balancing) pushbutton.
		Upon activation of the ALB button a slider will be displayed controlling the setting of a limit/threshold line (the ALB threshold)
		:param name: The name of the data displayed in the chart on which an active load balancing will be done
		:param value: Value of the data, can  be set/read using the value property of the widget
		:param min_value: Minimum displayed value (y-axis)
		:param max_value: Maximum displayed value (y-axis)
		:param alb_value: ALB threshold, can be set/read using the alb_value property of the widget
		:param alb_state: ALB state, subsequent can be set/read using the alb_state property
		:param data_buffer_length: Length of the data buffer displayed by the chart, the buffer acts as a FIFO (queue)
		:param width: Width of the widget in pixels (no percentages at this point)
		:param height: Height of the widget in pixels (no percentages at this point)
		:param kwargs: Style string passed to the container div tag

		:raises onALBstate_change: raised when the ALB pushbutton is pressed.
		To connect: onALBstate_change.connect(handling routine, *args, **kwargs), signature: (emitter:ALB_widget, nwstate:bool)
		:raises onALBvalue_change: raised when the ALB treshold is adjusted.
		To connect: onALBvalue_change.connect(handling routine, *args, **kwargs), signature: (emitter:ALB_widget, nwvalue:int)

		"""
		
		self.width = width
		self.height = height
		
		super(ALB_widget, self).__init__(**kwargs)
		kwargs.pop('style', None)  # the style kwarg is handled now... get rid of it
		self.style['width'] = f'{self.width}px'
		self.style['height'] = f'{self.height}px'
		
		self.name = name
		self.data_buffer_length = data_buffer_length
		self._data_buffer = [0] * self.data_buffer_length
		self._min_value = min_value
		self._max_value = max_value
		if min_value <= alb_value <= max_value:
			self._alb_value = alb_value
		else:
			raise ValueError
		self.alb_state = alb_state
		
		self.chart_config = Config(
			range=(self.min_value, self.max_value),
			show_y_guides=False,
			show_legend=False,
			show_x_labels=False,
			show_dots=False,
			margin_bottom=0,
			explicit_size=True,
			width=self.width,
			height=self.height
		)
		self.chart_style = Style(
			background="transparent",
			plot_background="transparent",
			# legend_font_size=20,
			# label_font_size=20,
			# major_label_font_size=20,
			# title_font_size=30,
			stroke_width=2,
			colors=["red", "blue", "green", "black", "yellow", "orange", "purple", "darkgrey"]
		)
		pygal_kwargs = []
		for arg in kwargs:
			if hasattr(self.chart_config, arg):
				pygal_kwargs.append(arg)
				setattr(self.chart_config, arg, kwargs.get(arg))
			elif hasattr(self.chart_style, arg):
				pygal_kwargs.append(arg)
				setattr(self.chart_style, arg, kwargs.get(arg))
		# remove the pygal kwargs from the dict, they have been handled
		for arg in pygal_kwargs: kwargs.pop(arg)
		
		self.main_cont = None
		self.chart_cont = None
		self.name_lbl = None
		self.slide_cont = None
		self.alb_slider = None
		# self.alb_switch = None
		self.slider_line_indicator = None
		self.alb_value_lbl = None
		self.chart = None
		
		self.build()
		# self.value = value
	
	def build(self):
		# print('pipo')
		# Because in Remi tis ALB widgets inherited container may get a position static when used in HBox or VBox.
		# We need to add a intermediate container ... the main_cont (div tag) with a relative position to provide an
		# anchor point for the absolute positioning of its inside components
		self.main_cont = gui.Container(style='position:relative; width:100%; height:100%; background-color:transparent')
		# The chart_cont holds the pygal chart and covers the whole widget
		self.chart_cont = gui.Widget(_type='div',
									 style='position:absolute;top:0%;left:0%;width:100%;height:100%;background-color:transparent')
		
		# The ALB on/off switch is positioned absolute annd should maintain its aspect ratio
		# self.alb_switch = gui.CheckBox(checked=self.alb_state,
		# 							   style='position:absolute;bottom:0%;right:0%;width:10px;height:10px')
		# self.alb_switch.onchange.connect(self.onALBstate_change)
		
		# self.alb_switch = PushBtn(text='ALB', style='position:absolute;bottom:0%;right:0%;width:50px')
		# self.alb_switch.set_value(self.alb_state)
		# self.alb_switch.onpushed.connect(self.onALBstate_change)
		
		self.name_lbl = gui.Label(text=self.name,
								  style='position:absolute;top:0%;left:0%;width:100%;height:10%;text-align:center;'
										'font-size:1.0em')
		# self.name_lbl.onclick.connect(self.onALBstate_change)
		
		# The slider to set the ALB treshold is contained within ist own container
		bottom_offset = int(17 - (self.height / 100))
		top_offset = int(17 - (self.height / 100))
		slider_width = self.height / 12
		
		self.slide_cont = gui.Container(style=f'position:absolute;top:{top_offset}px;left:0%;'
											  f'height:{self.height - bottom_offset - top_offset}px;width:{slider_width}px;'
											  'background-color:transparent')
		
		self.alb_slider = gui.Slider(default_value=str(self.alb_value), min=self.min_value, max=self.max_value, step=1,
									 style='position:relative;width:100%;height:100%')
		self.alb_slider.add_class('alb-slider')
		
		self.alb_slider.attributes['orient'] = 'vertical'
		self.slide_cont.append(self.alb_slider)
		self.alb_slider.onchange.connect(self.onALBvalue_change)
		
		# The line indicator for the ALB level
		self.slider_line_indicator = gui.Container(style=f'position:absolute;left:0%;width:100%;'
														 'background-color:transparent;border-style:dashed none none none;'
														 'border-color:black;border-width:2px')
		self.alb_value_lbl = gui.Label(text=f'{self.alb_value}',
									   style=f'position:absolute;top:0%;right:0%;font-size:1.0em')
		self.slider_line_indicator.append(self.alb_value_lbl)
		self.onALBvalue_change(self.alb_slider, str(self.alb_value))
		
		self.main_cont.append(
			[self.chart_cont, self.slider_line_indicator, self.name_lbl, self.slide_cont])
		self.append(self.main_cont)
		
		self.onALBstate_change(self.name_lbl, self.alb_state)
		self.update_chart()
	
	def set_content(self, chart):
		'''
			This method renders a PyGal Chart object into an SVG object that can be handled by Remi
		'''
		# Bij het renderen moet is_unicode op True worden gezet, anders zien we geen special characters (zoals degree signs etc.)
		self.chart_data = chart.render(is_unicode=True)
		self.chart_cont.add_child("chart", self.chart_data)
	
	def refresh(self, dp=None, *args, **kwargs):
		"""
		For compatibility with older JSEM implementations where datapoint call on subscribed widgets refresh method
		with dp argument. This routine will set the value property of this widget thus triggering an update
		:param dp: The calling JSEM datapoint, use its value property or its last100_values buffer queue
		:param args:
		:param kwargs:
		:return:
		"""
		if dp: self.value = dp.value
	
	def update_chart(self):
		# Create a DateTimeLine chart
		
		self.chart = Line(config=self.chart_config, style=self.chart_style)
		self.chart.add(self.name, self._data_buffer)
		self.chart.value_formatter = lambda x: f'{x:.1f}'
		# self.chart.x_value_formatter = lambda dt: dt.strftime(Best_dtFormat.get(self.dataselection, "%d-%m %H:%M"))
		self.set_content(self.chart)
	
	# print('chart_children:', len(self.chart_cont.children))
	
	# @decorate_set_on_listener("(self, emitter, item, new_value, row, column)")
	@decorate_event
	def onALBvalue_change(self, emitter, nw_value: str):
		"""Event for ALB value change.

		Args:
			emitter (SliderWidget): The emitter of the event.
			nw_value (string): The new value of the slider.
		"""
		# print(nw_value)
		nw_value = int(float(nw_value))
		factor = (nw_value - self.min_value) / (self.max_value - self.min_value)
		
		# offset1 = self.height/15			# bottom offset
		# offset2 = self.height/15			# top offset
		offset1 = int(22 + (self.height / 100))  # bottom offset
		offset2 = int(22 + (self.height / 100))  # top offset
		height = factor * (self.height - offset1 - offset2) + offset1
		# height = int(int(nw_value)*(self.height-offset1-offset2)/self.max_value) + offset1
		top = self.height - height
		self.slider_line_indicator.css_height = f'{height}px'
		self.slider_line_indicator.css_top = f'{top}px'
		self.alb_value = int(nw_value)
		self.alb_value_lbl.set_text(f'{self.alb_value}')
		return (self.alb_value,)
	
	# @decorate_set_on_listener("(self, emitter, item, new_value, row, column)")
	@decorate_event
	def onALBstate_change(self, emitter, nw_state: bool=None):
		if nw_state is None:
			self.alb_state = not self.alb_state
			nw_state = self.alb_state
			
		if not nw_state:
			self.name_lbl.set_style('color:black')
			self.slider_line_indicator.style['visibility'] = 'hidden'
			self.slide_cont.style['visibility'] = 'hidden'
		else:
			self.name_lbl.set_style('color:red')
			self.slider_line_indicator.style['visibility'] = 'visible'
			self.slide_cont.style['visibility'] = 'visible'
		return (nw_state,)


class PushBtn(gui.Widget):
	
	@property
	def locked(self):
		return self._locked
	
	@locked.setter
	def locked(self, value):
		self._locked = value
		if self._locked:
			self.style['opacity'] = '0.5'
		else:
			self.style['opacity'] = '1.0'
	
	def __init__(self, text='', initial_state=False, initial_locked=False, *args, **kwargs):
		super().__init__(_type='div', _class='pushbtn', *args, **kwargs)
		self._locked = False
		self.attributes['pushbtn'] = 'off'
		
		self.press = gui.Widget(_class='press')
		self.light = gui.Widget(_class='light')
		self.press.add_child(str(id(self.light)), self.light)
		
		self.text = gui.Widget(_class='label')
		txt = f'<text>{text}</text>'
		self.text.add_child(str(id(txt)), txt)
		self.press.add_child(str(id(self.text)), self.text)
		
		self.lines = gui.Widget(_class='lines')
		no_of_lines = 2
		for x in range(no_of_lines):
			line = gui.Widget(_class='line')
			self.lines.add_child(str(id(line)), line)
		self.press.add_child(str(id(self.lines)), self.lines)
		
		self.add_child(str(id(self.press)), self.press)
		self.onclick.connect(self.onpushed)

		self.__set_switch(initial_state)
		self.set_lock(initial_locked)

	def get_value(self):
		return self.attributes['pushbtn'] == 'on'
	
	def set_value(self, nw_state: bool):
		if self.locked: return
		if nw_state:
			self.__set_switch(True)
		else:
			self.__set_switch(False)
	
	def set_lock(self, lock: bool = False):
		self.locked = lock
	
	@decorate_set_on_listener("(self, emitter)")
	@decorate_event
	def onpushed(self, emitter):
		if self._locked: return (self.get_value(),)
		if self.get_value():
			self.__set_switch(False)
			return (False,)
		else:
			self.__set_switch(True)
			return (True,)
	
	def __set_switch(self, state):
		if self.locked: return
		if state:
			self.attributes['pushbtn'] = 'on'
			self.press.style['border-style'] = 'solid solid double solid'
			self.light.style['background'] = 'red'
			self.style['border-style'] = 'solid'
		else:
			self.attributes['pushbtn'] = 'off'
			self.press.style['border-style'] = 'hidden'
			self.light.style['background'] = 'black'
			self.style['border-style'] = 'double'


class Switch(gui.Widget):
	@property
	def locked(self):
		return self._locked
	
	@locked.setter
	def locked(self, value):
		self._locked = value
		if self._locked:
			self.style['opacity'] = '0.5'
		else:
			self.style['opacity'] = '1.0'
	
	def __init__(self, on_text='', off_text='', initial_state=False, initial_locked=False, *args, **kwargs):
		super().__init__(_type='div', _class='switch', *args, **kwargs)
		self._locked = False
		self.slider = gui.Widget(_class='thumb')
		
		self.light = gui.Widget(_class='light')
		
		self.on_text = gui.Widget(_class='onlabel')
		on_txt = f'<text>{on_text}</text>'
		self.on_text.add_child(str(id(on_txt)), on_txt)
		
		self.off_text = gui.Widget(_class='offlabel')
		off_txt = f'<text>{off_text}</text>'
		self.off_text.add_child(str(id(off_txt)), off_txt)
		
		self.lines = gui.Widget(_class='lines')
		no_of_lines = 3
		for x in range(no_of_lines):
			line = gui.Widget(_class='line')
			self.lines.add_child(str(id(line)), line)
		
		self.slider.add_child(str(id(self.light)), self.light)
		self.slider.add_child(str(id(self.on_text)), self.on_text)
		self.slider.add_child(str(id(self.off_text)), self.off_text)
		self.slider.add_child(str(id(self.lines)), self.lines)
		
		self.add_child(str(id(self.slider)), self.slider)
		self.onclick.connect(self.onswitched)
		
		self.__set_switch(initial_state)
		self.set_lock(initial_locked)
	
	def get_value(self):
		return self.attributes['switch'] == 'on'
	
	def set_value(self, nw_state: bool):
		if self.locked: return
		if nw_state:
			self.__set_switch(True)
		else:
			self.__set_switch(False)
	
	def set_lock(self, lock: bool = False):
		self.locked = lock
	
	@decorate_set_on_listener("(self, emitter)")
	@decorate_event
	def onswitched(self, emitter):
		if self._locked: return (self.get_value(),)
		if self.get_value():
			self.__set_switch(False)
			return (False,)
		else:
			self.__set_switch(True)
			return (True,)
	
	def __set_switch(self, state):
		if self.locked: return
		if state:
			self.attributes['switch'] = 'on'
			self.style["align-items"] = "flex-start"
			# self.slider.style['transform'] = 'translateY(-99%)'
			self.light.style['background-color'] = 'red'
			self.on_text.style['visibility'] = 'visible'
			self.off_text.style['visibility'] = 'hidden'
		else:
			self.attributes['switch'] = 'off'
			self.style["align-items"] = "flex-end"
			# self.slider.style['transform'] = 'translateY(0%)'
			self.light.style['background-color'] = 'black'
			self.on_text.style['visibility'] = 'hidden'
			self.off_text.style['visibility'] = 'visible'



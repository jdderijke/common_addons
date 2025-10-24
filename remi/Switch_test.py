import pathlib

import remi.gui as gui
from pandas.core.indexes.base import str_t
from remi import start, App

from common.Common_Utils import get_extra_css
from remi_addons import Switch


class MyApp(App):
	def __init__(self, *args):
		super(MyApp, self).__init__(*args)
	
	def main(self):
		style_str = get_extra_css("css")
		head = self.page.get_child('head')
		head.add_child(str(id(style_str)), style_str)
		
		self.container = gui.HBox(style='width:800px;height:600px;align_items:center;justify-content:center;background-color:black')
		
		self.onoff = Switch('HP_ON', 'OFF', style='width:70px;height:150px;font-size:0.7em')
		self.onoff.onswitched.connect(switch_handler)
		
		# self.boost = PushBtn('BOOST_52', style='position:absolute;top:100px;left:510px;width:100px;height:50px')
		# self.boost.onpushed.connect(boost_hndlr)
		#
		# self.lock = PushBtn('LOCK', style='position:absolute;top:160px;left:510px;width:100px;height:50px')
		# self.lock.onpushed.connect(locked_hndlr, widget_to_lock=self.onoff)
		#
		# self.lock = PushBtn('LOCK', style='position:absolute;top:160px;left:510px;width:100px;height:50px')
		# self.lock.onpushed.connect(locked_hndlr, widget_to_lock=self.onoff)
		#
		# self.lock2 = PushBtn('LOCK', style='position:absolute;top:220px;left:510px;width:100px;height:50px')
		# self.lock2.onpushed.connect(locked_hndlr, widget_to_lock=self.onoff)
		#
		# self.lock3 = PushBtn('LOCK', style='position:absolute;top:280px;left:510px;width:100px;height:50px')
		# self.lock3.onpushed.connect(locked_hndlr, widget_to_lock=self.onoff)
		#
		# self.lock4 = PushBtn('LOCK', style='position:absolute;top:340px;left:510px;width:100px;height:50px')
		# self.lock4.onpushed.connect(locked_hndlr, widget_to_lock=self.onoff)
		#
		# self.lock5 = PushBtn('Lck', style='position:absolute; top:395px; left:400px; width:25px; height:12px')
		
		# self.test.append([self.onoff, self.boost, self.lock, self.lock2, self.lock3, self.lock4, self.lock5])
		self.container.append(self.onoff)
		# returning the root widget
		return self.container


# listener function
def switch_handler(switch, state, *kwargs):
	print(switch)
	print(state)


# def boost_hndlr(pushbtn, state, **kwargs):
# 	print(f'BOOST PushButton pushed, new state = {"ON" if state else "OFF"}')


# def locked_hndlr(btn: PushBtn, state, **kwargs):
# 	print(f'LOCK PushButton pushed, new state = {"ON" if state else "OFF"}')
# 	widget_to_lock: Switch = kwargs.get('widget_to_lock')
# 	widget_to_lock.set_lock(state)


import inspect


def waitkey(prompt='Press any key to continue: '):
	"""
	Prints a prompt and waits for a keypress
	:param prompt:
	"""
	wait = input(inspect.currentframe().f_back.f_code.co_name + '> ' + prompt)


def is_child_of(child, parent):
	""" Determines if child is in any way a descendant of parent """
	try:
		for key in parent.children:
			if key.isdecimal():
				offspring = parent.children[key]
				print(f'checking offspring: {offspring} vs {parent}')
				
				if offspring is child:
					return True
				elif is_child_of(child, offspring):
					return True
		return False
	except Exception as err:
		print(str(err))
		return False


# starts the web server
start(MyApp, port=8081)

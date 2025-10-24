import os
import sys
import pathlib


import logging
from logging import handlers

import socket
import time
from datetime import datetime
from pathlib import Path, PosixPath

import pandas as pd
from dateutil.relativedelta import relativedelta


def get_logger(name: str = __name__):
	if os.getenv("ENV") == "DEV":
		logging.basicConfig(
			level=logging.INFO,
			format="%(asctime)s - %(levelname)s - %(module)s:%(funcName)s - %(message)s",
			datefmt="%Y-%m-%d %H:%M:%S"
		)
		logger = logging.getLogger(name)
	else:
		filepath = Path('Logs', f'{name}.log')
		Path(filepath).parent.mkdir(parents=True, exist_ok=True)
		logfile_handler = logging.FileHandler(filepath, mode="w")
		# logfile_handler = handlers.RotatingFileHandler(filepath, mode="w", backupCount=5)
		std_handler = logging.StreamHandler(sys.stdout)
		logging.basicConfig(
			level=logging.INFO,
			format="%(asctime)s - %(levelname)s - %(module)s:%(funcName)s - %(message)s",
			datefmt="%Y-%m-%d %H:%M:%S",
			handlers=[logfile_handler, std_handler]
		)
		logger = logging.getLogger(name)
	return logger

def update_css_stylestr(orig_style:str, new_style:str)->str:
	"""
	Updates a CSS style-string with another CSS style string... returns the updated CSS style-string
	:param orig_style: 	The CSS style-string to be updated
	:param new_style: 	The CSS style-string that must be applies to the original
	:return: 			An updated orig_style string
	"""
	if not new_style: return orig_style
	if not orig_style: return new_style
	
	new_items = new_style.split(';')
	orig_items = orig_style.split(';')
	
	orig_dict = {x.split(':')[0]:x.split(':')[1] for x in orig_items}
	new_dict = {x.split(':')[0]:x.split(':')[1] for x in new_items}

	orig_dict.update(new_dict)
	
	return ';'.join([f'{k}:{v}' for k,v in orig_dict.items()])


def get_ip_address():
	'''
	Returns the current ip_address of the system
	'''
	ip_address = ''
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.connect(("8.8.8.8", 80))
	ip_address = s.getsockname()[0]
	s.close()
	return ip_address


def cpu_temp(value=None):
	"""
	cpu_temp returns the temperature in Celcius in thermal zone 0 aka the CPU
	the value argument is not used and only here for compatibility purposes
	"""
	f = open("/sys/class/thermal/thermal_zone0/temp", "r")
	t = f.readline()
	f.close()
	return (int(t) / 1000)


def free_diskspace_mb(value=None, path='/'):
	"""
	free_diskspace_mb returns de free diskspace in MB as seen from the path variable
	the value argument is not used and only here for compatibility purposes
	"""
	st = os.statvfs(path)
	
	# free blocks available * fragment size
	bytes_avail = (st.f_bavail * st.f_frsize)
	megabytes = float(bytes_avail / 1024 / 1024)
	gigabytes = float(bytes_avail / 1024 / 1024 / 1024)
	return megabytes


def string_builder(motherstring: str, index: int, insertstring: str) -> str:
	"""
	string_builder is a routine that adds an insertstring into a motherstring at the specified index location
	It automatically sizes the motherstring UP to fit the insertstring if necessary
	"""
	# make motherstring longer if needed
	motherstring = motherstring.ljust(max(len(motherstring), (index + len(insertstring))))
	# slice insertstring in motherstring en return result
	return motherstring[:index] + insertstring + motherstring[index + len(insertstring):]


def conv_from_string(data_string, data_type):
	"""
	conv_from_string returns an Boolean, Integer, Float or String derived from the data_string
	data_type determines the type of conversion that will happen
	Raises an exception when the conversion fails
	"""
	if data_type == bool and data_string.strip().upper() in ["ON", "AAN", "TRUE", "WAAR", "JA"]:
		return True
	elif data_type == bool and data_string.strip().upper() in ["OFF", "UIT", "FALSE", "ONWAAR", "NEE"]:
		return False
	elif data_type == int:
		try:
			result = int(data_string.strip())
			return result
		except:
			raise Exception("Not a valid integer")
	elif data_type == float:
		try:
			result = float(data_string.strip())
			return result
		except:
			raise Exception("Not a valid floating point number")
	elif data_type == str:
		result = data_string.strip()
		return result


def ddlist_from_value(value):
	"""
	ddlist_from_value returns a LIST with strings that can be used for a pulldown menu in a data entry field
	The list is populated based on the value argument:
	If the value argument is boolean type, then the list contains the normal boolean selections like AAN en UIT etc.
	If the value is INT or FLOAT a list is returned with several strings indicating values above and below the value argument.
	Also the current string representation of the value argument is returned as selected_item...
	"""
	ddlist = []
	selected_item = ""
	
	if type(value) == bool:
		ddlist.append("AAN")
		ddlist.append("UIT")
		if value:
			selected_item = "AAN"
		else:
			selected_item = "UIT"
	
	elif type(value) == int:
		for perc in [-100, -50, -20, -15, -10, -5, 0, 5, 10, 15, 20, 50, 100]:
			if perc == 0:
				if str(value - 3) not in ddlist: ddlist.append(str(value - 3))
				if str(value - 2) not in ddlist: ddlist.append(str(value - 2))
				if str(value - 1) not in ddlist: ddlist.append(str(value - 1))
				ddlist.append(str(value))
				if str(value + 1) not in ddlist: ddlist.append(str(value + 1))
				if str(value + 2) not in ddlist: ddlist.append(str(value + 2))
				if str(value + 3) not in ddlist: ddlist.append(str(value + 3))
			else:
				ddlist.append(str(value + int((perc / 100.0) * value)))
		selected_item = str(value)
	
	elif type(value) == float:
		for perc in [-100, -50, -20, -15, -10, -5, 0, 5, 10, 15, 20, 50, 100]:
			if perc == 0:
				ddlist.append(str(value))
			else:
				ddlist.append(str(value + (perc / 100.0) * value))
		selected_item = str(value)
	
	elif type(value) == str:
		if value.upper() in ["AAN", "UIT"]:
			ddlist.append("AAN")
			ddlist.append("UIT")
		elif value.upper() in ["TRUE", "FALSE"]:
			ddlist.append("TRUE")
			ddlist.append("FALSE")
		selected_item = value.upper()
	
	return ddlist, selected_item


import builtins


def get_type(type_name):
	try:
		return getattr(builtins, type_name)
	except AttributeError:
		return None


def dump(obj):
	for attr in dir(obj):
		print("obj.%s = %r" % (attr, getattr(obj, attr)))


def get_newest_file(path: str = "./", pattern: str = "*.*"):
	# print(f"path: {path}, pattern: {pattern}")
	files = Path(path).glob(pattern)
	files = [f for f in files]
	
	if not files:
		return None
	else:
		latest_file = max(files, key=lambda item: item.stat().st_ctime)
		return str(latest_file)


def get_files(path, option='all'):
	import glob
	# print("path plus pattern = %s" % path)
	files = glob.glob(path)
	
	if files == []:
		return []
	elif option.lower() == 'newest':
		return max(files, key=os.path.getctime)
	elif option.lower() == 'oldest':
		return min(files, key=os.path.getctime)
	elif option.lower() == 'all':
		files = sorted(files, key=os.path.getctime)
		return files


def normalize_data(df: pd.DataFrame, normalize: str = 'mean_std', settings: dict = {}):
	"""
	This routine normalizes the data in 1 of 2 possible ways:
	mean_std: substract the mean from the data and then divide by the std deviation
	min_max: Scale everything back to a range between 0.0 and 1.0
	
	:param df: The pandas dataframe to normalize
	:param normalize: 'mean_std' or 'min_max'
	:param settings: a dictionary with per column a dictionary with mean/std or min/max presets
	:return: the normalized data (in a dataframe) and a dataframe with the mean/std or min/max values per column
	"""
	result_settings = settings.copy()
	
	from pandas.api.types import is_numeric_dtype
	# Normalizes all numerical data in a dataframe, shifts each column by its mean and scales it by its stddev
	def shift_and_scale(col):
		if is_numeric_dtype(col):
			if settings:
				mean = settings[col.name]['mean']
				stddev = settings[col.name]['stddev']
			else:
				mean = col.mean()
				stddev = col.std()
				result_settings[col.name] = {}
				result_settings[col.name]['mean'] = mean
				result_settings[col.name]['stddev'] = stddev
			col = col - mean
			if stddev != 0.0:
				col = col / stddev
		return col
	
	def min_max_scale(col):
		if is_numeric_dtype(col):
			if settings:
				min_value = settings[col.name]['min']
				max_value = settings[col.name]['max']
			else:
				min_value = col.min()
				max_value = col.max()
				result_settings[col.name] = {}
				result_settings[col.name]['min'] = min_value
				result_settings[col.name]['max'] = max_value
			
			if min_value != max_value:
				col = (col - min_value) / (max_value - min_value)
			else:
				# all values are equal... so 0 for 0 and 1 for everything else
				col = pd.np.where(col != 0, 1.0, 0.0)
		return col
	
	if normalize == 'mean_std':
		# Shift the data by the mean per columns and scale by the stddev per columns
		return df.apply(lambda x: shift_and_scale(x), axis=0), result_settings
	elif normalize == 'min_max':
		# now scale everything in a range between 0 and 1
		return df.apply(lambda x: min_max_scale(x), axis=0), result_settings
	else:
		raise Exception(f'non existing normalization method..{normalize}')


def get_extra_css(directory=None):
	"""
	This routine returns a css HTML string (with HTML tags) with the contents of all
	css files in a specified directory
	:param directory: Relative to the current working directory (cwd) or a Posix path
						Defaults to css directory under the current working dir
	:return: HTML style string with style tags
	"""
	if not directory:
		directory = pathlib.Path(pathlib.Path.cwd(), "css")
	elif type(directory) is not PosixPath:
		directory = pathlib.Path(pathlib.Path.cwd(), directory)
	
	style_str = ""
	for path_to_css_file in directory.glob("*.css"):
		print(f'adding {path_to_css_file}.')
		style_str += f"\n/* ======BEGIN=== {path_to_css_file.name} =============== */\n"
		with open(path_to_css_file, 'r') as f:
			style_str += f.read()
		style_str += f"\n/* ========END=== {path_to_css_file.name} =============== */\n"
	
	style_str = f'<style type="text/css">{style_str}</style>'
	return style_str


import inspect


def Waitkey(prompt='Press any key to continue: '):
	"""
	Prints a prompt and waits for a keypress
	:param prompt:
	"""
	wait = input(inspect.currentframe().f_back.f_code.co_name + '> ' + prompt)


def dump(obj):
	"""

	:param obj:
	:return: Prints all attributes of the passed object
	"""
	for attr in dir(obj):
		print("obj.%s = %r" % (attr, getattr(obj, attr)))


def dump_dict(obj: dict):
	'''
	Dumps a dictionary in key:value pairs
	:param obj:
	:return:
	'''
	if not type(obj) is dict: raise TypeError
	for k, v in obj.items():
		print(f'key= {k} : value= {v}')


def Is_NOE(value):
	''' returns True if (NULL/None or Empty) '''
	if value is None: return True
	if type(value) in [str, list, dict, bytearray] and len(value) == 0: return True
	return False


def IsNot_NOE(value):
	''' returns True if NOT (NULL/None or Empty)'''
	return not Is_NOE(value)


def thisday_timestamp(now=datetime.now(), at_noon=False):
	'''
	Returns the timestamp of the start of this day.... or noon...
	'''
	if not at_noon:
		return int(datetime.timestamp(now.replace(hour=0, minute=0, second=0, microsecond=0)))
	else:
		return int(datetime.timestamp(now.replace(hour=12, minute=0, second=0, microsecond=0)))


def thishour_timestamp(now=datetime.now(), at_half=False):
	'''
	Returns the timestamp of the start of this hour.... or halfhour...
	'''
	if not at_half:
		return int(datetime.timestamp(now.replace(minute=0, second=0, microsecond=0)))
	else:
		return int(datetime.timestamp(now.replace(minute=30, second=0, microsecond=0)))


def this10min_timestamp(now=datetime.now()):
	'''
	Returns the timestamp of the previous 10 minute mark...
	'''
	mark_10min = datetime(now.year, now.month, now.day, now.hour, (now.minute // 10) * 10)
	return int(datetime.timestamp(mark_10min.replace(second=0, microsecond=0)))


def get_begin_of_week(check_day=datetime.now(), sunday_as_start=True):
	from datetime import timedelta
	'''
	Returns the start of the week for the given checkday
	'''
	week_day = check_day.weekday()
	if sunday_as_start:
		week_day += 1
		if week_day == 7: week_day = 0
	start = check_day - timedelta(days=week_day)
	return start.replace(hour=0, minute=0, second=0, microsecond=0)


def get_days_in_month(selecteddate=datetime.now()):
	'''
	Returns the number of days in the month of the selecteddate.
	'''
	first_day_this_month = selecteddate.replace(day=1, hour=0, minute=0, second=0)
	first_day_next_month = selecteddate.replace(day=1, hour=0, minute=0, second=0) + relativedelta(months=1)
	days_in_month = (first_day_next_month - first_day_this_month).days
	# print("Days in this month: %s" % days_in_month)
	return int(days_in_month)


def get_input(prompt="", default=None):
	'''
	prompts the user for input and returns the input in the type specified by the default argument
	'''
	if default is not None:
		default_str = str(default)
		try:
			inp = input(prompt + "(default: " + default_str + ") :")
			if inp == "":
				return default
			else:
				if type(default) in [int, float]:
					return type(default)(float(inp))
				elif type(default) in [bool]:
					if inp.upper() in ['ON', '1', 'TRUE', 'AAN', 'YES']:
						return True
					elif inp.upper() in ['OFF', '0', 'FALSE', 'UIT', 'NO']:
						return False
				else:
					return str(inp)
		except Exception as err:
			return default
	else:
		return input(prompt + ' :')


def update_progressbar(max_num=100, act_num=100, max_bars=100):
	'''
	Print and updates a progressbar in terminal mode
	'''
	print("\r", end="")
	print("{:.1%} ".format(act_num / max_num), "-" * int(act_num / max_num) * max_bars, end="")


def spinning_cursor():
	while True:
		for cursor in '|/-\\':
			yield cursor


def spincursor(duration=1.0):
	'''
	Spins the cursor for duration seconds
	'''
	spinner = spinning_cursor()
	for _ in range(int(10 * duration)):
		sys.stdout.write(next(spinner))
		sys.stdout.flush()
		time.sleep(0.1)
		sys.stdout.write('\b')


import base64


def Load_Images(image_path):
	"""
	Load en returned een image file als een bytearray
	"""
	with open(Path(image_path), "rb") as imageFile:
		imagestring = base64.b64encode(imageFile.read())
		return "data:image/gif;base64," + imagestring.decode()


def first_number(s):
	'''
	Returns the index of the first number in a string, including the sign + or -
	'''
	for i, c in enumerate(s):
		if c.isdigit() or c in ['-', '+']:
			return i
	return -1


# def getAttributes(clazz):
# 	"""
# 	Returns a dictionary with the class attributes and their values.
# 	Build_ins and methods are skipped and NOT part of the result
# 	:param clazz: The class instance to inspect
# 	:return: dict with attr:value pairs
# 	"""
# 	return {name: attr for name, attr in clazz.__dict__.items()
# 			if not name.startswith("__")
# 			and not callable(attr)
# 			and not type(attr) is staticmethod}


def getAttributes(clazz):
	"""
	Returns a dictionary with the class attributes and their values.
	Build_ins and methods are skipped and NOT part of the result
	:param clazz: The class instance to inspect
	:return: dict with attr:value pairs
	"""
	attrs = {}
	for name in vars(clazz):
		if name.startswith("__"):
			continue
		attr = getattr(clazz, name)
		if callable(attr):
			continue
		attrs[name] = attr
	return attrs


class Doc(object):
	def __init__(self, parent):
		self.descriptor = """documentation object for class attributes"""
		self.parent = parent
	
	def __call__(self, *args, **kwargs):
		pass


class Test(object):
	"""
	Dit is een Test object
	:param name: Naam van de boel
	:param cdrh: Cash Data
	:param economy_mode: Economy boel
	"""
	
	def __init__(self, name, cdrh, economy_mode):
		self.doc = Doc(self)
		self.name = "name"
		self.doc.name = "dit is een documentatie test"
		
		self.cdrh = 3000  # pipo de clown
		self.doc.cdrh = """ Cash Data Retention Hours"""
		
		self.economy_mode = True
		self.doc.economy_mode = "Dit is de documentatie van de economy mode"
		
		self.holdings = [1, 2, 3, 4, 5, 6, 7, 8, 9]


def main(args):
	test = Test("een", 3000, True)
	print(test.__doc__)
	
	print(getAttributes(test))
	for attr, value in getAttributes(test).items():
		print(attr, value, getattr(getattr(test, "doc"), attr))
	print("Finished...")


if __name__ == '__main__':
	
	sys.exit(main(sys.argv))

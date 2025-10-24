def is_child_of(child, parent):
	'''
	Determines if child Remi Widget is in any way a descendant of the parent Remi Widget
	:param child:
	:param parent:
	:return: True or False
	'''
	try:
		level_up = child.get_parent()
	except:
		return False
	if level_up is None:
		return False
	elif level_up is parent:
		return True
	else:
		return is_child_of(level_up, parent)


def set_mouse(*args, **kwargs):
	print("args: ", args)
	print("kwargs: ", kwargs)
	widget = args[0]
	event = kwargs.get("event", None)
	if event is None:
		print ("No event passed...")
		return
	if event == "onmouseover":
		widget.onmouseover.connect(None, None)
		widget.style["cursor"] = "grab"
	elif event == "onmousedown":
		widget.style["cursor"] = "grabbing"
	elif event == "onmouseup":
		widget.style["cursor"] = "grab"
	elif event == "onmouseleave":
		widget.onmouseover.connect(set_mouse, event="onmouseover")
		widget.style["cursor"] = "default"


def set_css_sizes(widget=None, *args, **kwargs):
	'''
	This routine reads the kwargs on css settings for a widget object
	and fills those css settings in the passed widget
	'''
	if widget is None: return
	
	if any(x in kwargs for x in ['top', 'bottom', 'left', 'right']):
		default_position = 'absolute'
	else:
		default_position = 'relative'
	widget.css_position = kwargs.get('position', default_position)
	
	# get font, top, left, width and height
	fontsize = str(kwargs.get("fontsize", ""))
	top = str(kwargs.get("top", ""))
	left = str(kwargs.get("left", ""))
	width = str(kwargs.get("width", ""))
	height = str(kwargs.get("height", ""))
	
	if fontsize.isnumeric(): fontsize += "px"
	if top.isnumeric(): top += "px"
	if left.isnumeric(): left += "px"
	if width.isnumeric(): width += "px"
	if height.isnumeric(): height += "px"
	
	if fontsize: widget.css_font_size = fontsize
	if top: widget.css_top = top
	if left: widget.css_left = left
	widget.css_width = width if width else "100%"
	widget.css_height = height if height else "100%"
	
	kwargs["css_font_size"] = widget.css_font_size
	# kwargs["css_top"] = widget.css_top
	# kwargs["css_left"] = widget.css_left
	# kwargs["css_width"] = widget.css_width
	# kwargs["css_height"] = widget.css_height
	
	kwargs.pop("fontsize", None)
	# kwargs.pop("top", None)
	# kwargs.pop("left", None)
	# kwargs.pop("width", None)
	# kwargs.pop("height", None)
	
	return kwargs

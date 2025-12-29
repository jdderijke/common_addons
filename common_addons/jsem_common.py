from enum import Enum


class Wakeup_Mode(Enum):
	in1hour = 3600
	in2hour = 7200
	in6hour = 21600
	in12hour = 43200
	in24hour = 86400
	in48hour = 172800
	hour = -1
	day = -2
	week = -3
	month = -4
	year = -5


def Calculate_Timerset(start_timestamp=None, wakeup_mode=None, interval=None):
	'''
	Routine calculates and returns the initial timerset (in seconds) and the repeating timerset (after the first one)
	The timerset is the time (in seconds) between NOW and the interval applied to the passed start_timstamp (or NOW if None)...
	so the time left from NOW if the interval was applied to the passed start_timstamp.

	If that time left is negative, the the timer should have fired already... then the interval is applied to NOW...

	for intervals in day, week month and year... the timerset is calculated to the NEXT appropriate moment from NOW,
	so the start_timestamp is not taken into account....NOW is used instead

	interval argument are either:
		- strings indicating an time and interval (e.g. hourly, daily etc):
				returns initial timerset to top of the hour/day/month etc
				returns repeat timerset as interval corresponding to hour/day/month etc
				Voor al deze modes wordt de timerset t.o.v. start_timestamp berekent als die meegegeven is, t.o.v. NU als niet meegegeven
		- strings indicating only an interval (e.g. in1hour, in2hour, in6hour etc)
				returns initial and repeat timerset as interval corresponding to hour, 2hours etc.
				Voor al deze modes wordt de timerset t.o.v. start_timestamp berekent als die meegegeven is, t.o.v. NU als niet meegegeven
		- integer values in seconds (e.g. 1, 3600 etc)
				returns initial and repeat timerset as interval corresponding integer value
		- negative integer values, indicating a one_time_poll only at start_up (handled by the poller_start routine of the interface)
				returns initial timerset as interval corresponding to absolute integer value
				returns repeat timerset as None
		- date-time strings:
				MM-DD UU:MM:SS.
				Dus 15 23:30:00 betekent de 15e van iedere maand om 23:30:00
				:15 betekent de 15e seconde van iedere minuut
				13:22 betekent 13 minuten en 22 seconden na ieder uur
				15:00:00 betekent iedere middag om 15:00 uur
				returns initial timerset as interval to the first occurence of the specified time/date
				returns repeat timerset as interval corresponding to the specified time/date interval
	wakeup_mode (Enum) (overrules interval):
			Same as the string definitions above
			Voor al deze modes wordt de timerset t.o.v. start_timestamp berekent als die meegegeven is, t.o.v. NU als niet meegegeven
				Wakeup_Mode.in1hour
				Wakeup_Mode.in2hour
				etc.
				Wakeup_Mode.day
				Wakeup_Mode.week
				Wakeup_Mode.month
				Wakeup_Mode.year
	'''
	timerset = None
	repeatset = None
	try:
		# bepaal de referentietijdstip en nu tijdstip
		start_ts = time.time() if start_timestamp is None else start_timestamp
		start_dt = datetime.fromtimestamp(start_ts)
		if wakeup_mode is not None:
			# wakeup_mode gaat VOOR interval
			interval = wakeup_mode
		else:
			if interval == None:
				raise ValueError("No valid input parameters: interval = None")
			elif str(interval).isnumeric():
				# de meest simpele case...gewoon een numerieke timerset
				timerset = int(float(interval))
				if timerset < 0:
					# negative means only 1 time, so no repeat timerset
					return abs(timerset), None
				else:
					return timerset, timerset
			elif ':' in interval or '-' in interval:
				# MM-DD UU:MM:SS string
				# this is an absolute timepoint, so we calculate it based on now and find the first occurence of the timepoint
				then = datetime.now().replace(microsecond=0)
				time_elements = ['second', 'minute', 'hour', 'day', 'month', 'year']
				delta_elements = ['seconds', 'minutes', 'hours', 'days', 'months', 'years']
				
				# maak een splitstr met alle elementen
				splitstr = interval.split(' ')
				if len(splitstr) == 1:
					splitstr = interval.split(':')
				else:
					splitstr = interval.split(' ')[0].split('-') + interval.split(' ')[1].split(':')
				
				# draai de volgorde om zodat seconden eerst komen
				splitstr.reverse()
				for teller, element in enumerate(splitstr):
					if splitstr[teller] != '':
						arg = {time_elements[teller]: int(splitstr[teller])}
						then = then.replace(**arg)
						# hou bij wat het hoogste gewijzigde element is in THEN
						highest_index = teller
				
				# print (str(then))
				delta_index = highest_index if highest_index == len(time_elements) - 1 else highest_index + 1
				arg = {delta_elements[delta_index]: 1}
				if int(datetime.timestamp(then)) - time.time() <= 0:
					# we zouden uitkomen op een tijdstip dat VOOR nu ligt, we verhogen het element BOVEN het hoogst gewijzigde element met 1
					then = then + relativedelta(**arg)
				# bepaal het eerste herhaal tijdstip
				repeat = then + relativedelta(**arg)
				
				# print (str(then))
				# convert to timestamp, rounded to seconds
				# print('then = %s' % then)
				then = int(datetime.timestamp(then))
				# print ('repeat = %s' % repeat)
				repeat = int(datetime.timestamp(repeat))
				timerset = then - int(time.time())
				repeatset = repeat - then
				return timerset, repeatset
			
			elif interval in ["1hour", "in1hour"]:
				interval = Wakeup_Mode.in1hour
			elif interval in ["2hour", "in2hour"]:
				interval = Wakeup_Mode.in2hour
			elif interval in ["6hour", "in6hour"]:
				interval = Wakeup_Mode.in6hour
			elif interval in ["12hour", "in12hour"]:
				interval = Wakeup_Mode.in12hour
			elif interval in ["24hour", "in24hour"]:
				interval = Wakeup_Mode.in24hour
			elif interval in ["48hour", "in48hour"]:
				interval = Wakeup_Mode.in48hour
			elif interval in ["hourly", "hour"]:
				interval = Wakeup_Mode.hour
			elif interval in ["daily", "day"]:
				interval = Wakeup_Mode.day
			elif interval in ["weekly", "week"]:
				interval = Wakeup_Mode.week
			elif interval in ["monthly", "month"]:
				interval = Wakeup_Mode.month
			elif interval in ["yearly", "year"]:
				interval = Wakeup_Mode.year
			else:
				raise ValueError("No valid input parameters: interval = " + str(interval))
		
		# als we hier terecht zijn gekomen dan is interval van het type enum Wakeup_Mode
		if interval in [Wakeup_Mode.in1hour, Wakeup_Mode.in2hour, Wakeup_Mode.in6hour, Wakeup_Mode.in12hour,
						Wakeup_Mode.in24hour, Wakeup_Mode.in48hour]:
			# bereken het eind timestamp van deze mode....based on start_ts (kan overruled zijn door bijv. last_resettimestamp)
			then = start_ts + interval.value
			# bereken hoe lang nog tot aan dit punt
			timerset = then - int(time.time())
			# controleer of dit punt al voorbij is.....neem anders het gewone interval
			return timerset if timerset > 0 else interval.value, interval.value
		elif interval in [Wakeup_Mode.hour, Wakeup_Mode.day, Wakeup_Mode.week, Wakeup_Mode.month, Wakeup_Mode.year]:
			# bereken het eind timestamp van deze mode....start_ts kan overruled zijn door een start_timestamp argument (bijv. last_resettimestamp)
			if interval.name == "hour":
				then = int(datetime.timestamp(
					datetime.now().replace(minute=0, second=0, microsecond=0) + relativedelta(hours=1)))
				return (then - int(time.time())), 60 * 60
			elif interval.name == "day":
				then = int(
					datetime.timestamp(datetime.now().replace(hour=0, minute=0, second=0) + relativedelta(days=1)))
				return (then - int(time.time())), 24 * 60 * 60
			elif interval.name == "week":
				weekday = datetime.now().weekday()
				weekday = weekday + 1  # correct weekday for sunday being the first day of the week rather than monday
				if weekday == 7: weekday = 0
				then = int(datetime.timestamp(
					datetime.now().replace(hour=0, minute=0, second=0) - relativedelta(days=weekday) + relativedelta(
						days=7)))
				return (then - int(time.time())), 7 * 24 * 60 * 60
			elif interval.name == "month":
				then = int(datetime.timestamp(
					datetime.now().replace(day=1, hour=0, minute=0, second=0) + relativedelta(months=1)))
				repeat = int(datetime.timestamp(
					datetime.now().replace(day=1, hour=0, minute=0, second=0) + relativedelta(months=2)))
				return (then - int(time.time())), repeat - then
			elif interval.name == "year":
				then = int(datetime.timestamp(
					datetime.now().replace(month=1, day=1, hour=0, minute=0, second=0) + relativedelta(years=1)))
				repeat = int(datetime.timestamp(
					datetime.now().replace(month=1, day=1, hour=0, minute=0, second=0) + relativedelta(years=2)))
				return (then - int(time.time())), repeat - then
		else:
			raise ValueError("No timerset can be calculated from interval = " + str(interval))
		# print ("Calculated timerset: " + str(timerset))
		return timerset, repeatset
	except ValueError as err:
		Logger.error(str(err))
	except Exception as err:
		Logger.exception(str(err))


def expandcollapse(expand_cont, collaps_cont, **kwargs):
	# print ("expandcollapse_clicked called")
	charts_parent = Common_Data.CHARTS_PARENT_CONTAINER
	data_parent = Common_Data.DATA_PARENT_CONTAINER
	# dont expand an empty charts area
	if expand_cont is charts_parent and len(charts_parent.children.keys()) == 0:
		return
	expand_cont.css_width = "90%"
	collaps_cont.css_width = "10%"
	if collaps_cont is charts_parent:
		visibility = 'hidden'
	else:
		visibility = 'visible'
	
	if len(charts_parent.children.keys()) > 0:
		# We have active charts..
		for child_key in charts_parent.children.keys():
			chart = charts_parent.children[child_key]
			if hasattr(chart, 'legendbox'): chart.legendbox.style['visibility'] = visibility
			if hasattr(chart, 'controlbox'): chart.controlbox.style['visibility'] = visibility
	
	pass  # debug point


def Calculate_Period(data_selection=None, re_timestamp=None):
	'''
	This routine returns the START and END timestamps for the data_selection period selected
	referenced from the re_timestamp provided or NOW if nothing is provided
	It return None, None if no timestamps can be calculated
	'''
	try:
		if data_selection is None: raise ValueError
		ts_now = time.time() if re_timestamp is None else int(re_timestamp)
		dt_now = datetime.fromtimestamp(ts_now)
		
		if data_selection in [DataSelection.All, DataSelection._Last50]:
			# no timestamps here
			return None, None
		elif data_selection in [DataSelection._48hr, DataSelection._24hr, DataSelection._12hr,
								DataSelection._6hr, DataSelection._2hr, DataSelection.Hour,
								DataSelection._10min, DataSelection._30min, DataSelection._1hr]:
			start_ts = ts_now - data_selection.value
			end_ts = ts_now
		elif data_selection == DataSelection.Day:
			start_ts = int(datetime.timestamp(dt_now.replace(hour=0, minute=0, second=0)))
			end_ts = int(datetime.timestamp(dt_now.replace(hour=0, minute=0, second=0) + relativedelta(days=1))) - 1
		elif data_selection == DataSelection.Week:
			weekday = dt_now.weekday()
			weekday = weekday + 1  # correct weekday for sunday being the first day of the week rather than monday
			if weekday == 7: weekday = 0
			sunday_thisweek = dt_now.replace(hour=0, minute=0, second=0) - relativedelta(days=weekday)
			sunday_nextweek = sunday_thisweek + relativedelta(days=7)
			start_ts = int(datetime.timestamp(sunday_thisweek))
			end_ts = int(datetime.timestamp(sunday_nextweek)) - 1
		elif data_selection == DataSelection.Month:
			start_ts = int(datetime.timestamp(dt_now.replace(day=1, hour=0, minute=0, second=0)))
			end_ts = int(
				datetime.timestamp(dt_now.replace(day=1, hour=0, minute=0, second=0) + relativedelta(months=1))) - 1
		elif data_selection == DataSelection.Year:
			start_ts = int(datetime.timestamp(dt_now.replace(month=1, day=1, hour=0, minute=0, second=0)))
			end_ts = int(datetime.timestamp(
				dt_now.replace(month=1, day=1, hour=0, minute=0, second=0) + relativedelta(years=1))) - 1
		
		return start_ts, end_ts
	except Exception as err:
		Logger.exception(str(err))


def cursor_to_dict(data=None, output=Dictionary.of_lists):
	'''
	Returns a dictionary with the columnnames as keys and de row values as listitems....
	Takes as input a Cursor object resulting from a conn.execute() command to sqlite
	'''
	result = dict()
	col_names = list()
	values = list()
	for col_info in data.description:
		col_names.append(col_info[0])
		# voor iedere column maken we een (nu nog lege) value list
		values.append([])
	# rows = data.fetchall()
	for row in data:
		# iedere row is een tuple met waarden met net zoveel elementen als er columns zijn
		teller = 0
		for col in row:
			values[teller].append(row[teller])
			teller += 1
	
	if len(values[0]) == 0 and (output == Dictionary.of_values or output == Dictionary.autoselect):
		# If NO row returned, then return a dictionary of None's'
		values = [None for x in values]
		result = dict(zip(col_names, values))
	elif len(values[0]) == 1 and (output == Dictionary.of_values or output == Dictionary.autoselect):
		# If Only one row returned, then return a dictionary of values
		values = [x[0] for x in values]
		result = dict(zip(col_names, values))
	else:
		# return a dictionary of valuelists....
		result = dict(zip(col_names, values))
	return result


def set_widget_colors(widget=None, dp=None):
	from Common_Data import CATEGORY_ID
	
	# Set the colors a widget based on its datapoint binding
	if widget is None or dp is None: return
	if Is_NOE(dp.categoryID): return
	
	# print ("cat ID is " + str(self.categoryID))
	cat = CATEGORY_ID[dp.categoryID]
	if not dp.enabled:
		widget.css_background_color = cat.disabled_BG_Color
		widget.css_color = cat.disabled_FG_Color
	else:
		widget.css_background_color = cat.BG_Color
		widget.css_color = cat.FG_Color

epex_data = 214	# Datapoint ID of the Epex data
epex_pred = 334
def get_all_epexinfo(start_dt=datetime.now(), plan_hours=None):
	from DB_Routines import get_df_from_database
	'''
	Deze routine returned een dataframe met epex_info die bestaat uit epex_data (voorzover beschikbaar)
	aangevuld met epex_pred (indien en voorzover beschikbaar). Alleen aaneensluitende uren worden meegenomen
	De serie wordt dus afgebroken als er uren beginnen te ontbreken
	indien er een plan_hours is opgegeven wordt tot maximaal dat aantal uren vanaf de start_dt meegenomen
	'''
	# dit uur kunnen we beginnen
	selected_startdate = start_dt.replace(minute=0, second=0, microsecond=0)
	start_ts = int(selected_startdate.timestamp())
	selected_enddate = None
	if plan_hours:
		end_ts = start_ts + (
					3600 * plan_hours)  # op deze manier bepalen van end_ts heeft geen last van zomer/wintertijd overgangen
		selected_enddate = datetime.fromtimestamp(end_ts)
	
	# now get all the epex_data starting from start_dt hour
	epex_data_df = get_df_from_database(dpIDs=[epex_data], selected_startdate=selected_startdate,
										selected_enddate=selected_enddate,
										add_datetime_column=True)
	# then get the predictions (if any)
	epex_pred_df = get_df_from_database(dpIDs=[epex_pred], selected_startdate=selected_startdate,
										selected_enddate=selected_enddate)
	
	# met een outer join/merge worden de rijen allemaal gecombineerd van beide dataframes, NaN voor missende values
	epex_df = epex_data_df.merge(epex_pred_df[['timestamp', 'epex_pred']], how='outer', on="timestamp")
	
	# maak nu een nieuwe kolom met de combi van epex_data en epex_pred waarbij epex_data voorgaat (als we die hebben)
	epex_df['epex_info'] = epex_df['epex_data'].fillna(epex_df['epex_pred'])
	
	# check of er NaN (ontbrekende epex data en of epex_pred) is gevonden in de epex_info, nan_idx is een arrays met de indexen van de NaN entries
	nan_idx = np.nonzero(np.array(epex_df['epex_info'].isnull()))[0]
	if nan_idx.size > 0:
		# er zijn blijkbaar NaN entries gevonden....bepaal de index van de eerste NaN
		firstnan_idx = nan_idx[0]
		if firstnan_idx < (len(epex_df) - 1):
			# purge the rest of the epex_data, we cant use them... they contain NaN's
			epex_df = epex_df[:firstnan_idx]
			last_valid_ts = epex_df['timestamp'].values[-1]
			Logger.info(
				'Plan horizon is gewijzigd naar %s ivm te weinig epex data en/of epex_predictie data' % datetime.fromtimestamp(
					last_valid_ts))
	
	return epex_df[['timestamp', 'datetime', 'epex_info']]

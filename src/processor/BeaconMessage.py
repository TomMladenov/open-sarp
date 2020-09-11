from bitarray import bitarray, util
import datetime
import logging
from countries import countries

logger = logging.getLogger('event_logger')

USER_PROTOCOLS = {
		0: "Orbitography Protocol",
		1: "ELT - Aviation User Protocol",
		2: "EPIRB - Marine User Protocol",
		3: "Serial User Protocol",
		4: "National User Protocol",
		5: "2nd Gen Beacon",
		6: "EPIRB - Radio Call Sign User Protocol",
		7: "Test User Protocol"
		}

USER_PROTOCOLS_SHORTENED = {
		0: "Orbitography",
		1: "ELT",
		2: "EPIRB User",
		3: "Serial User",
		4: "National User",
		5: "2nd Gen",
		6: "EPIRB - Radio Call",
		7: "Test User"
		}

POS_SOURCE_BIT = {
		False: "External",
		True: "Internal"
		}

POS_LAT_FLAG = {
		False: "N",
		True: "S"
		}

POS_LON_FLAG = {
		False: "E",
		True: "W"
		}

MODIFIED_BAUDOT = {
		56: "A",
		51: "B",
		46: "C",
		50: "D",
		48: "E",
		54: "F",
		43: "G",
		37: "H",
		44: "I",
		58: "J",
		62: "K",
		41: "L",
		39: "M",
		38: "N",
		35: "O",
		45: "P",
		61: "Q",
		42: "R",
		52: "S",
		33: "T",
		60: "U",
		47: "V",
		57: "W",
		55: "X",
		53: "Y",
		49: "Z",
		36: " ",
		24: "-",
		23: "/",
		13: "0",
		29: "1",
		25: "2",
		16: "3",
		10: "4",
		1: "5",
		21: "6",
		28: "7",
		12: "8",
		3: "9"
		}


class BeaconMessage(object):


	def __init__(self, beacon_bitarray, creation_time):
		length = beacon_bitarray.length()
		'''
		if int(length) != 88:
			raise ValueError("Supplied bitarray length is not compatible with a short beacon message (88), got {BITS} bits instead".format(BITS=length))
		elif int(length) != 120:
			raise ValueError("Supplied bitarray length is not compatible with a long beacon message (120), got {BITS} bits instead".format(BITS=length))
		'''

		self.bitarray = beacon_bitarray
		self.creation_time = creation_time

		self.data = {}
		self.data['type'] = 'N/A'
		self.data['BCH-1'] = 'N/A'
		self.data['BCH-2'] = 'N/A'
		self.data['format_flag'] = 'N/A'
		self.data['country_code'] = 'N/A'
		self.data['country_name'] = 'N/A'
		self.data['country_name_alpha2'] = 'N/A'
		self.data['protocol_num'] = 'N/A'
		self.data['protocol_name'] = 'N/A'
		self.data['protocol_name_shortened'] = 'N/A'
		self.data['beacon_hex'] = util.ba2hex(self.bitarray).decode('utf-8')

		if length == 88:
			self.data['type'] = 'SHORT'
			self.data['BCH-1'] = self.bitarray[61:82]
		else:
			self.data['type'] = 'LONG'
			self.data['BCH-1'] = self.bitarray[61:82]
			self.data['BCH-2'] = self.bitarray[107:119]


		self.data['format_flag'] = self.bitarray[0]
		self.data['protocol_flag'] = self.bitarray[1]
		self.data['country_code'] = util.ba2int(self.bitarray[2:12])
		try:
			self.data['country_name'] = countries[str(self.data['country_code'])][3]
			self.data['country_name_alpha2'] = countries[str(self.data['country_code'])][0]
		except Exception as e:
			pass

		if (self.data['type'] == 'SHORT' and self.data['protocol_flag']) or (self.data['type'] == 'LONG' and self.data['protocol_flag']):
			self.data['protocol'] = 'USER'
			self.data['protocol_num'] = util.ba2int(self.bitarray[11:14])
			self.data['protocol_name'] = USER_PROTOCOLS[self.data['protocol_num']]

			if self.data['protocol_name'] == 0:
				self.data['id'] = util.ba2int(self.bitarray[15:61])
				self.data['id_type'] = 'Orbitography data'
			elif self.data['protocol_name'] == 1:
				self.data['id'] = util.ba2int(self.bitarray[15:57])
				self.data['id_type'] = 'Aircraft Registration Marking'
			elif self.data['protocol_name'] == 2:
				self.data['id'] = util.ba2int(self.bitarray[15:57])
				self.data['id_type'] = 'MMSI or Call Sign'
			elif self.data['protocol_name'] == 3:
				self.data['id'] = util.ba2int(self.bitarray[19:49])
				self.data['id_type'] = 'Serial Number'
			'''
			elif self.data['protocol_name'] == 4:

			elif self.data['protocol_name'] == 5:

			elif self.data['protocol_name'] == 6:

			elif self.data['protocol_name'] == 7:
			'''

			if self.data['country_name_alpha2'] == 'FR' and self.data['type'] == 'LONG' and self.data['protocol_num'] == 4:
				#print(self.bitarray.to01())
				#print(self.data['BCH-2'].to01())
				pass



			self.data['protocol_name_shortened'] = USER_PROTOCOLS_SHORTENED[self.data['protocol_num']]
			if self.data['protocol_name'] == USER_PROTOCOLS[6]:
				self.data['radio_callsign'] = MODIFIED_BAUDOT.get(util.ba2int(self.bitarray[15:21]), '*') + MODIFIED_BAUDOT.get(util.ba2int(self.bitarray[21:27]), '*') + MODIFIED_BAUDOT.get(util.ba2int(self.bitarray[27:33]), '*') + MODIFIED_BAUDOT.get(util.ba2int(self.bitarray[33:39]), '*')

			if self.data['type'] == 'LONG':
				self.data['pos_source'] = POS_SOURCE_BIT[self.bitarray[82]]
				self.data['pos_lat_flag'] = POS_LAT_FLAG[self.bitarray[83]]
				self.data['pos_lat_deg'] = util.ba2int(self.bitarray[84:91])
				self.data['pos_lat_min'] = util.ba2int(self.bitarray[91:95])*(4.0/60)

				self.data['pos_lon_flag'] = POS_LON_FLAG[self.bitarray[95]]
				self.data['pos_lon_deg'] = util.ba2int(self.bitarray[95:103])
				self.data['pos_lon_min'] = util.ba2int(self.bitarray[103:107])*(4.0/60)

				#logger.info("Position is {NS}{LAT}°{LATMIN}' {EW}{LON}°{LONMIN}'".format(NS=self.data['pos_lat_flag'], LAT=self.data['pos_lat_deg'], LATMIN=self.data['pos_lat_min'], EW=self.data['pos_lon_flag'], LON=self.data['pos_lon_deg'], LONMIN=self.data['pos_lon_min']))
		else:
			self.data['protocol'] ='STANDARD_NATIONAL'

from bitarray import bitarray, util
from BeaconMessage import BeaconMessage
import datetime
import logging

logger = logging.getLogger('event_logger')

class SARPMessage(object):


	def __init__(self, sarp_message_bytes, creation_time, message_format):
		length = len(sarp_message_bytes)
		if length != 24:
			raise ValueError("SARP message does not have 24 bytes!, got {LEN} instead".format(LEN=length))
		self.bytes = sarp_message_bytes
		self.message_creation_time = creation_time

		self.data = {}
		self.data['message_creation_time'] = str(self.message_creation_time)
		self.data['message_format'] = message_format
		self.data['format'] = 'N/A'
		self.data['format_valid'] = 'N/A'
		self.data['level'] = 'N/A'
		self.data['level_dbm'] = 'N/A'
		self.data['rt/pb'] = 'N/A'
		self.data['latest'] = 'N/A'
		self.data['dru'] = 'N/A'
		self.data['pseudo'] = 'N/A'
		self.data['type'] = 'N/A'
		self.data['s/no'] = 'N/A'
		self.data['s/no_db'] = 'N/A'
		self.data['timecode'] = 'N/A'
		self.data['timecode_parity_valid'] = 'N/A'
		self.data['doppler_word'] = 'N/A'
		self.data['abs_freq'] = 'N/A'
		self.data['doppler_parity_valid'] = 'N/A'
		self.data['beacon_bits'] = 'N/A'
		self.data['beacon_hex'] = 'N/A'

		tmp = util.hex2ba(self.bytes.hex())
		self.bitarray = bitarray(tmp, endian='big')

		self.word0 = self.bitarray[0:24]
		self.word1 = self.bitarray[24:48]
		self.word2 = self.bitarray[48:72]
		self.word3 = self.bitarray[72:96]
		self.word4 = self.bitarray[96:120]
		self.word5 = self.bitarray[120:144]
		self.word6 = self.bitarray[144:168]
		self.word7 = self.bitarray[168:192]

		if 	util.ba2int(self.word2) == 13516288:
			self.data['format'] == 'HK'
		elif util.ba2int(self.word7) == 1: # if last word = 0x000001
			self.data['format'] = 'SHORT'
		else:
			self.data['format'] = 'LONG'

		#The 0x000001 above tells us with quite good cerntainty if this frame is LONG or SHORT, however there is also a bit indicating this,
		#We should check this bit as it allows us to detect if the frame format is wrong if it does not correspond with our findings above.

		if self.data['format'] != 'HK': #only proceed if the frame we are dealing with is not an HK frame

			#=============================== FORMAT CHECK ===================================
			if self.data['format'] == 'SHORT' and self.data['message_format'] == 'SARSAT SARP-2':
				if self.word0[15] == False:
					self.data['format_valid'] = True
				else:
					 self.data['format_valid'] = False
			elif self.data['format'] == 'LONG' and self.data['message_format'] == 'SARSAT SARP-2':
				if self.word0[15] == True:
					self.data['format_valid'] = True
				else:
					 self.data['format_valid'] = False
			elif self.data['format'] == 'SHORT' and self.data['message_format'] == 'SARSAT SARP-3':
				if self.word2[0] == False:
					self.data['format_valid'] = True
				else:
					 self.data['format_valid'] = False
			elif self.data['format'] == 'LONG' and self.data['message_format'] == 'SARSAT SARP-3':
				if self.word2[0] == True:
					self.data['format_valid'] = True
				else:
					 self.data['format_valid'] = False
			elif self.data['format'] == 'SHORT' and self.data['message_format'] == 'COSPAS SARP-2':
				if self.word3[0] == False:
					self.data['format_valid'] = True
				else:
					 self.data['format_valid'] = False
			elif self.data['format'] == 'LONG' and self.data['message_format'] == 'COSPAS SARP-2':
				if self.word3[0] == True:
					self.data['format_valid'] = True
				else:
					 self.data['format_valid'] = False





			#================================================================================

			#================================== WORD 0 ======================================
			if self.data['message_format'] == 'SARSAT SARP-2':
				self.data['level'] = util.ba2int(self.word0[18:24])
				self.data['level_dbm'] = round((0.55*util.ba2int(self.word0[18:24])) - 140.0, 2)

				if self.word0[17] == True:
					self.data['rt/pb'] = 'REALTIME'
					#print('RT/PB = REALTIME, bits {BITS}'.format(BITS=self.word0[17]))
				else:
					self.data['rt/pb'] = 'PLAYBACK'
					#print('RT/PB = PLAYBACK, bits {BITS}'.format(BITS=self.word0[17]))

				if self.word0[16] == True:
					self.data['latest'] = 'Most recent message'
					#print('Latest = MOST RECENT (PLAYBACK), bits {BITS}'.format(BITS=self.word0[16]))
				else:
					self.data['latest'] = 'Other'
					#print('Latest = OTHER, bits {BITS}'.format(BITS=self.word0[16]))

				self.data['dru'] = util.ba2int(self.word0[15:17])
				self.data['pseudo'] = self.word0[12]


			elif self.data['message_format'] == 'SARSAT SARP-3':
				self.data['level'] = util.ba2int(self.word0[18:24])
				self.data['level_dbm'] = round((0.55*util.ba2int(self.word0[18:24])) - 140.0, 2)

				if self.word0[17] == True:
					self.data['rt/pb'] = 'REALTIME'
					#print('RT/PB = REALTIME, bits {BITS}'.format(BITS=self.word0[17]))
				else:
					self.data['rt/pb'] = 'PLAYBACK'
					#print('RT/PB = PLAYBACK, bits {BITS}'.format(BITS=self.word0[17]))

				if self.word0[16] == True:
					self.data['latest'] = 'Most recent message'
					#print('Latest = MOST RECENT (PLAYBACK), bits {BITS}'.format(BITS=self.word0[16]))
				else:
					self.data['latest'] = 'Other'
					#print('Latest = OTHER, bits {BITS}'.format(BITS=self.word0[16]))

				if self.word0[15] == True:
					self.data['type'] = 'C/S T.001'
					#print('Type = Cospas-Sarsat Beacon (document C/S T.001)')
				else:
					self.data['type'] = 'New type'
					#print('Type = New type beacon')

				self.data['s/no'] = util.ba2int(self.word0[12:15])

				levels = {	0: "32.3",
							1: "34.8",
							2: "37.5",
							3: "41.1",
							4: "45.2",
							5: "50.1",
							6: "55.5",
							7: "62.1"}

				self.data['s/no_db'] = levels.get(self.data['s/no'])
			else: #COSPAS SARP-2
				pass
				 #self.data['message_format'] == 'SARSAT SARP-3':

			#=================================================================================



			#================================ TIMECODE =======================================
			if self.data['message_format'] == 'SARSAT SARP-2' or self.data['message_format'] == 'SARSAT SARP-3':
				timecode_bitarray = self.word1[0:23]
				self.data['timecode'] = util.ba2int(timecode_bitarray)
				high_bits = timecode_bitarray.count(True)

				timecode_parity = self.word1[23]
				if timecode_parity:
					if (high_bits % 2) != 0: #If the timecode parity bit is set we should have an odd number of ones
						self.data['timecode_parity_valid'] = True
					else:
						self.data['timecode_parity_valid'] = False
				else:
					if (high_bits % 2) == 0: #If the timecode parity bit is set we should have an odd number of ones
						self.data['timecode_parity_valid'] = True
					else:
						self.data['timecode_parity_valid'] = False
			else:
				print('COSPAS SARP-2 not yet supported!!')
			#=================================================================================



			#================================== BEACON DATA ==================================
			if self.data['format'] == 'SHORT' and self.data['format_valid']:
				if self.data['message_format'] == 'SARSAT SARP-2':
					beacon_bits = self.bitarray[48:135] #87 bits
					self.data['beacon_bits'] = '0' + beacon_bits.to01()
					self.data['beacon_hex'] = util.ba2hex(bitarray(self.data['beacon_bits'], endian='big')).decode('utf-8')
					self.beacon_message = BeaconMessage(bitarray(self.data['beacon_bits'], endian='big'), self.message_creation_time)
				elif self.data['message_format'] == 'SARSAT SARP-3':
					beacon_bits = self.bitarray[49:136] #87 bits
					self.data['beacon_bits'] = '0' + beacon_bits.to01()
					self.data['beacon_hex'] = util.ba2hex(bitarray(self.data['beacon_bits'], endian='big')).decode('utf-8')
					self.beacon_message = BeaconMessage(bitarray(self.data['beacon_bits'], endian='big'), self.message_creation_time)
				else:
					beacon_bits = self.bitarray[72:159] #87 bits
					self.data['beacon_bits'] = '0' + beacon_bits.to01()
					self.data['beacon_hex'] = util.ba2hex(bitarray(self.data['beacon_bits'], endian='big')).decode('utf-8')
					self.beacon_message = BeaconMessage(bitarray(self.data['beacon_bits'], endian='big'), self.message_creation_time)

			elif self.data['format'] == 'LONG' and self.data['format_valid']:
				if self.data['message_format'] == 'SARSAT SARP-2':
					beacon_bits = self.bitarray[48:167] #87 bits
					self.data['beacon_bits'] = '1' + beacon_bits.to01()
					self.data['beacon_hex'] = util.ba2hex(bitarray(self.data['beacon_bits'], endian='big')).decode('utf-8')
					self.beacon_message = BeaconMessage(bitarray(self.data['beacon_bits'], endian='big'), self.message_creation_time)
				elif self.data['message_format'] == 'SARSAT SARP-3':
					beacon_bits = self.bitarray[49:168] #87 bits
					self.data['beacon_bits'] = '1' + beacon_bits.to01()
					self.data['beacon_hex'] = util.ba2hex(bitarray(self.data['beacon_bits'], endian='big')).decode('utf-8')
					self.beacon_message = BeaconMessage(bitarray(self.data['beacon_bits'], endian='big'), self.message_creation_time)
				else:
					beacon_bits = self.bitarray[72:191] #87 bits
					self.data['beacon_bits'] = '1' + beacon_bits.to01()
					self.data['beacon_hex'] = util.ba2hex(bitarray(self.data['beacon_bits'], endian='big')).decode('utf-8')
					self.beacon_message = BeaconMessage(bitarray(self.data['beacon_bits'], endian='big'), self.message_creation_time)
			elif self.data['format_valid'] == False:
				pass

			#print(self.data['beacon_bits'])
			#=================================================================================


			#=============================== DOPPLER WORD ====================================
			if self.data['format'] == 'SHORT' and self.data['format_valid']:
				if self.data['message_format'] == 'SARSAT SARP-2' or self.data['message_format'] == 'SARSAT SARP-3':
					doppler_word_bitarray = self.word6[1:23]
					sign_bit = self.word6[0]
					if sign_bit:
						doppler_word_bitarray.invert()
						self.data['doppler_word'] = - (util.ba2int(doppler_word_bitarray) + 1)
					else:
						self.data['doppler_word'] = util.ba2int(doppler_word_bitarray)

					self.data['abs_freq'] = (8121.0/200.0)*10000000 + self.data['doppler_word']*0.015 #Assumes the spacecraft USO is still at 10 MHz
					doppler_word_bitarray_and_signbit = self.word6[0:23]
					high_bits = doppler_word_bitarray_and_signbit.count(True)
					doppler_parity = self.word6[23]
					if doppler_parity:
						if (high_bits % 2) != 0: #If the timecode parity bit is set we should have an odd number of ones
							self.data['doppler_parity_valid'] = True
							#print('parity CHECK OK')
						else:
							self.data['doppler_parity_valid'] = False
							#print('parity CHECK FAILED')
					else:
						if (high_bits % 2) == 0: #If the timecode parity bit is set we should have an odd number of ones
							self.data['doppler_parity_valid'] = True
							#print('parity CHECK OK')
						else:
							self.data['doppler_parity_valid'] = False
							#print('parity CHECK FAILED')
				else:
					print('COSPAS SARP-2 not yet supported!!')
			elif self.data['format'] == 'LONG' and self.data['format_valid']:
				#print('word7 = {W}'.format(W=util.ba2hex(self.word7)))
				doppler_word_bitarray = self.word7[1:23]
				sign_bit = self.word7[0]
				#print('extracted doppler word= {DW}'.format(DW=doppler_word))
				#print('extracted sign bit= {DW}'.format(DW=sign_bit))
				if sign_bit:
					doppler_word_bitarray.invert()
					self.data['doppler_word'] = - (util.ba2int(doppler_word_bitarray) + 1)
				else:
					self.data['doppler_word'] = util.ba2int(doppler_word_bitarray)

				self.data['abs_freq'] = (8121.0/200.0)*10000000 + self.data['doppler_word']*0.015 #Assumes the spacecraft USO is still at 10 MHz

				doppler_word_bitarray_and_signbit = self.word7[0:23]
				high_bits = doppler_word_bitarray_and_signbit.count(True)

				doppler_parity = self.word7[23]
				if doppler_parity:
					if (high_bits % 2) != 0: #If the timecode parity bit is set we should have an odd number of ones
						self.data['doppler_parity'] = True
					else:
						self.data['doppler_parity'] = False
				else:
					if (high_bits % 2) == 0: #If the timecode parity bit is set we should have an odd number of ones
						self.data['doppler_parity'] = True
					else:
						self.data['doppler_parity'] = False
			elif self.data['format_valid'] == False:
				pass

			#=================================================================================
		else:
			logger.warning('Parsing of HK packets is not supported!')

	def setMessageFormat(self, message_format):
		pass

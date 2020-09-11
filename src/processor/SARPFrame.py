from SARPMessage import SARPMessage
from bitarray import bitarray, util
import datetime
import logging

SYNCWORD = bytes.fromhex('42BB1F')
MARKER = bytes.fromhex('D6')

#Because the frames from gnuradio start right after the syncord was found, upon retrieving 1200 symbols the last bytes are the syncword of the next frame.

SYNC_WORD_START = 	72
SYNC_WORD_LEN = 	3

MARKER1_START = 0
MARKER1_LEN = 1
LMESSAGE1_START = 0
LMESSAGE1_LEN = 24

MARKER2_START = 24
MARKER2_LEN = 1
SMESSAGE_START = 24
SMESSAGE_LEN = 24

MARKER3_START = 48
MARKER3_LEN = 1
LMESSAGE2_START = 48
LMESSAGE2_LEN = 24

logger = logging.getLogger('event_logger')


class SARPFrame(object):

	valid = False
	message_format = None

	def __init__(self, sarp_bytes, message_format):
		length = len(sarp_bytes)
		if len(sarp_bytes) != 75:
			raise ValueError("SARP frame does not have 75 bytes!")

		self.frame_creation_time = datetime.datetime.utcnow()

		self.bytes = sarp_bytes
		self.length = length
		self.message_format = message_format

		if self.bytes[SYNC_WORD_START:SYNC_WORD_START + SYNC_WORD_LEN] != SYNCWORD:
			self.valid = False
		elif self.bytes[MARKER1_START:MARKER1_START + MARKER1_LEN] != MARKER:
			self.valid = False
		elif self.bytes[MARKER2_START:MARKER2_START + MARKER2_LEN] != MARKER:
			self.valid = False
		elif self.bytes[MARKER3_START:MARKER3_START + MARKER3_LEN] != MARKER:
			self.valid = False
		else:
			self.valid = True


		if self.valid:
			self.message1 = SARPMessage(self.bytes[LMESSAGE1_START:LMESSAGE1_START + LMESSAGE1_LEN], self.frame_creation_time, self.message_format)
			self.message2 = SARPMessage(self.bytes[SMESSAGE_START:SMESSAGE_START + SMESSAGE_LEN], self.frame_creation_time, self.message_format)
			self.message3 = SARPMessage(self.bytes[LMESSAGE2_START:LMESSAGE2_START + LMESSAGE2_LEN], self.frame_creation_time, self.message_format)

	def updateMessageFormats(self, message_format):
		self.message_format = message_format
		self.message1.setMessageFormat(message_format)
		self.message2.setMessageFormat(message_format)
		self.message3.setMessageFormat(message_format)

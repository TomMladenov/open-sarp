import matplotlib.pyplot as plt
import numpy as np
import argparse
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("-f", "--filename", help="path to recording")
args = parser.parse_args()

def decodeManchester(arr):
	length = len(arr)

	index = 0

	decoded_arr = []
	if not length % 2 == 0:
		raise Exception("array must be of even length!")

	while True:
		if arr[index] == False and arr[index + 1] == True:
			decoded_arr.append(False)
			index = index + 2
		elif arr[index] == True and arr[index + 1] == False:
			decoded_arr.append(True)
			index = index + 2
		else:
			raise Exception("Bad symbol decode at index {I}".format(I=index))

		if index + 1 > length:
			break

	return decoded_arr

symbols = []
file = open(args.filename, "rb")
byte = file.read(1)
while byte:
	val = ord(byte)
	byte = file.read(1)
	if val == 1:
		symbols.append(True)
	else:
		symbols.append(False)

file.close()

formatted_frames = np.array(symbols).reshape(-1,1200)

decoded_frames = []
good_frames = 0
bad_frames = 0
for frame in formatted_frames:
	try:
		decoded_frame = decodeManchester(frame)
		decoded_frames.append(decoded_frame)
		good_frames += 1
	except Exception as e:
		bad_frames += 1

print('Processed {N} frames:'.format(N=len(formatted_frames)))
print('{N} GOOD frames'.format(N=good_frames))
print('{N} BAD frames'.format(N=bad_frames))


fig = plt.figure()
fig.suptitle(args.filename)
ax = fig.add_subplot(111)
ax.imshow(decoded_frames, aspect='auto', cmap=plt.cm.gray, interpolation='nearest')
plt.show()

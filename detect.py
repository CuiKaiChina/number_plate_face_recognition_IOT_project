import cv2
import numpy as np
import pytesseract
import queue, threading, time

class VideoCapture:
	def __init__(self, num):
		self.cap = cv2.VideoCapture(num)
		self.q = queue.queue()
		t = threading.Thread(target=self._reader)
		t.daemon = True
		t.start()

	def _reader(self):
		while True:
			ret, frame = self.cap.read()
			if not ret:
				break
			if not self.q.empty():
				try:
					self.q.get_nowait()
				except queue.Empty:
					pass
			self.q.put(frame)

	def read(self):
		return self.q.get()

COLOR = (0,255,0)

ssdnet = cv2.dnn.readNetFromTensorflow('trained_model/frozen_inference_graph.pb','trained_model/graph.pbtxt')

# cam = cv2.VideoCapture('vid.mp4')
cam = cv2.VideoCapture(0)

cv2.namedWindow("output", cv2.WINDOW_NORMAL)
cv2.resizeWindow("output", 640,480)

f=0
while f<0:
	ret, img = cam.read()
	f+=1

while cam.isOpened():
	# print("\r",f,end=" ")
	# f+=1
	ret, img = cam.read()
	# img = cv2.flip(img, 1)
	# img = cv2.resize(img,(1280,720))
	rows,cols,channels = img.shape

	ssdnet.setInput(cv2.dnn.blobFromImage(img,size=(400,400),swapRB=True,crop=False))
	netout = ssdnet.forward()

	scores=[]
	for detection in netout[0,0]:
		scores.append(float(detection[2]))

	if len(scores)>2:
		first=np.argmax(scores)
		scores.pop(first)
		second=np.argmax(scores)
		idtxs=[first,second]
	else:
		idtxs = range(len(scores))

	for idx in idtxs:
		detection=netout[0,0][idx]
		score = float(detection[2])
		if score >0.2:
			left=int(detection[3]*cols)
			top=int(detection[4]*rows)-15
			right=int(detection[5]*cols)+10
			bottom=int(detection[6]*rows)+15

			cv2.rectangle(img, (left, top), (right, bottom), COLOR, 2)
			cv2.putText(img, str(score*100)[:5], (left, top),cv2.FONT_HERSHEY_SIMPLEX, 0.8, COLOR, 2)
			plate = img[top:bottom,left:right]
			try:
				plate = cv2.cvtColor(plate, cv2.COLOR_BGR2GRAY)
				plate = cv2.GaussianBlur(plate, (7, 7), 0)
				plate = cv2.erode(plate, (6, 6))
				plate = cv2.dilate(plate, (6, 6))
				# ret,plate = cv2.threshold(plate,127,255,cv2.THRESH_BINARY)
				plate = cv2.adaptiveThreshold(plate,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,7,2)
				text=pytesseract.image_to_string(plate,lang='eng',config="--oem 0 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ")
				if len(text)>6 and len(text)<16:
					print(text)
				cv2.imshow("plate",plate)
			except:
				pass

	cv2.imshow("output", img)
	key = cv2.waitKey(1) & 0xff
	if key == ord('q'):
		break

cam.release()
cv2.destroyAllWindows()

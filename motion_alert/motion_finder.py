import cv2
import numpy as np


# The MotionFinder class encapsulates looking for motion in a video stream
class MotionFinder:
    HIST_LEN = 60
    RESIZE_FACTOR = 4
    KERNEL_3 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    KERNEL_11 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))

    def __init__(self):
        self.hist = []
        self.histSum = None

    def addToHist(self, frame):
        # Internal use: add a frame to the history
        # Maintain both a list of previous frames
        # and the sum in the history, so average is O(1)
        blur = cv2.GaussianBlur(frame, (11,11), 0) #blur it to reduce noise
        intFrame = blur.astype(int) #convert each pixel color value to integer
                                    #(instead of byte) so addition of many frames works well
        if len(self.hist) < MotionFinder.HIST_LEN:
            self.hist.append(intFrame)
            if self.histSum is None:
                self.histSum = np.copy(intFrame)
            else:
                self.histSum += intFrame
        else:
            self.histSum -= self.hist[0]
            self.histSum += intFrame
            self.hist = self.hist[1:] + [intFrame]

    def diffFromHist(self, frame):
        # Internal use: find the delta between the frame and the average
        # of N previous frames, return the delta as a gray-scale frame.
        if len(self.hist) == 0: #no history, return zeros
            diff = np.zeros((len(frame), len(frame[0]), 3), np.uint8)
            return diff
        blur = cv2.GaussianBlur(frame, (11,11), 0)
        intFrame = blur.astype(int)
        intDelta = np.abs((self.histSum / len(self.hist)) - intFrame)
        delta = intDelta.astype(np.uint8)
        return delta

    def processFrame(self, frame):
        # Main function: check the delta of this frame to N previous frames
        # return the contours and bounding boxes where a delta exists

        # Work on a lower resolution frame
        smallFrame = cv2.resize(frame, None, fx = 1.0/MotionFinder.RESIZE_FACTOR, 
                        fy = 1.0/MotionFinder.RESIZE_FACTOR, interpolation = cv2.INTER_AREA)
        delta = self.diffFromHist(smallFrame)
        self.addToHist(smallFrame)
        #now process the delta
        [db, dg, dr] = cv2.split(delta)
        _, db = cv2.threshold(db, 50, 255, cv2.THRESH_BINARY)
        _, dg = cv2.threshold(dg, 50, 255, cv2.THRESH_BINARY)
        _, dr = cv2.threshold(dr, 50, 255, cv2.THRESH_BINARY)
        thresh = np.bitwise_or(np.bitwise_or(db, dg), dr)
        thresh = cv2.erode(thresh, MotionFinder.KERNEL_3) # remove noise
        thresh = cv2.dilate(thresh, MotionFinder.KERNEL_11) # close gaps
        _, contours, _ = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        smallBoxes = [cv2.boundingRect(cnt) for cnt in contours]
        #scale up the boxes to the original resolution
        bigBoxes = [(x1*MotionFinder.RESIZE_FACTOR,x2*MotionFinder.RESIZE_FACTOR,
                     x3*MotionFinder.RESIZE_FACTOR,x4*MotionFinder.RESIZE_FACTOR)
                    for (x1,x2,x3,x4) in smallBoxes]
        #scale up contours to the original resolution
        for cnt in contours:
            cnt[:,:,0] = cnt[:,:,0]*MotionFinder.RESIZE_FACTOR
            cnt[:,:,1] = cnt[:,:,1]*MotionFinder.RESIZE_FACTOR
        return bigBoxes, contours


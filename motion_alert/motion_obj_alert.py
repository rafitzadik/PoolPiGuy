######## Raspberry Pi Object Detection on Motion Areas Using Tensorflow Classifier #########
#

#move to the correct virtualenv
activate_this_file = "/home/pi/.virtualenvs/tf/bin/activate_this.py"
exec(open(activate_this_file).read(), {'__file__': activate_this_file})

# Import packages
import os
import cv2
import numpy as np
import sys
import time
import datetime
import requests
from motion_finder import MotionFinder
from tf_obj_det import TFClassify

    
def main():
    IM_WIDTH = 1920.0
    IM_HEIGHT = 1080.0
    OUTPUT_DIR = "/home/pi/poolpi/output" #keep images and videos here
    CUR_IMG_TMP = "cur_tmp.jpg"
    CUR_IMG_NAME = "cur_img.jpg"
    LAST_DET_TMP = "last_det_tmp.jpg"
    LAST_DET_LINK = "last_det.jpg"
    ifttt_url = open('/home/pi/poolpi/motion_alert/ifttt_url.txt').readline().rstrip() #get the IFTTT URL
    # Is there a graphical display attached?
    try:
        display_env = os.environ['DISPLAY']
        has_display = True
    except:
        has_display = False
    # Init a motion finder and an object detector
    motionFinder = MotionFinder()
    classifier = TFClassify()
    classifier.initClassifier()

    # Init the camera capture, set it to capture in HD
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, IM_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, IM_HEIGHT)

    # Init the video writer
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = None
    outStartTime = 0
    maxOutTime = 3600 #rotate video files after that long

    # Some last house keeping
    confThreshold =0.75 #ignore low confidence detections completely
    interestingClasses = [1, 16, 17, 18] #Person, bird, cat, dog
    muteNotifications = 600 #seconds to mute new notifications
    lastNotification = 0
    
    ret, frame = cap.read() #read one frame to get the actual dimensions
    print('Initialized and read first image, size({}x{})'.format(frame.shape[1], frame.shape[0]))
    while(True):
        nowNum = time.time()
        nowObj = datetime.datetime.now()
        nowStr = str(nowObj)
        if out is None: # Do we need to create a new video file?
            outFilename = os.path.join(OUTPUT_DIR, 'out-{:12.1f}.avi'.format(nowNum))
            outStartTime = time.time()
            out = cv2.VideoWriter(outFilename,fourcc, 1, (frame.shape[1], frame.shape[0]))

        # Grab a new frame
        ret, frame = cap.read()
        boxes, contours = motionFinder.processFrame(frame) #find motion areas
        dets = classifier.classify(frame) #find objects in frame
        runTime = time.time() - nowNum
        # Write some basics the frame
        cv2.putText(frame, 'Time: {}. Proc Time: {} ms'.format(nowObj.strftime("%m/%d/%Y %H:%M:%S"),
                                                               int(runTime*1000)),
                    (10, 100), cv2.FONT_HERSHEY_DUPLEX, 1.5, (0,0,255), 2)
        # Draw the object detections on the frame
        classifier.visualize(frame, dets)
        # Did we also have motion?
        if len(contours) > 0:
            # Draw the motion contours:
            cv2.drawContours(frame, contours, -1, (250,0,0), thickness = 2)
            # Keep the really high confidence and interesting dets:
            goodDets = [det for det in dets if (det[1] > confThreshold and det[2] in interestingClasses)]
            if len(goodDets) > 0:
                # So we have a high confidence, interesting detection and motion was detected.
                # Create a filename using the highest conf detections
                sortDets = sorted(goodDets, key = lambda det: det[1], reverse=True)
                detNames = ""
                numDetsToPrint = min(3, len(sortDets)) #name using the top 3 detections
                for i in range (numDetsToPrint):
                    if i > 0:
                        detNames += ','
                    detNames += sortDets[i][3]
                imgFilename = '{}-{:12.1f}.jpg'.format(detNames, nowNum)
                # Write the image to that file
                cv2.imwrite(os.path.join(OUTPUT_DIR, imgFilename), frame)
                # Create a simlink to a temporary filename, then rename which is an atomic operation
                os.symlink(os.path.join(OUTPUT_DIR, imgFilename), os.path.join(OUTPUT_DIR, LAST_DET_TMP))
                os.rename(os.path.join(OUTPUT_DIR, LAST_DET_TMP), os.path.join(OUTPUT_DIR, LAST_DET_LINK))
                # Should we send a notification? Only if we didn't send one recently
                if (nowNum - lastNotification) > muteNotifications:
                    lastNotification = nowNum
                    try:
                        r = requests.post(ifttt_url,
                                          json={"value1":"Detected {} ({:.1%})".format(sortDets[i][3], sortDets[i][1]),
                                                "value2":imgFilename})
                    except:
                        print('request failed')

        # Write the image as current image so it can be seen easily regardless of objects and motion
        cv2.imwrite(os.path.join(OUTPUT_DIR, CUR_IMG_TMP), frame)
        os.rename(os.path.join(OUTPUT_DIR, CUR_IMG_TMP), os.path.join(OUTPUT_DIR, CUR_IMG_NAME))
        out.write(frame)
        if (has_display):
            cv2.imshow('frame', frame)
        procTime = int((time.time() - nowNum)*1000)
        #print('Processing Time: ', procTime, ' ms')
        timeToWaitKey = max(200,  1000 - procTime) #add a bit of delay to let the OS run other things
        key = cv2.waitKey(timeToWaitKey) & 0xff
        if time.time() - outStartTime > maxOutTime: #should we rotate the video file?
            out.release()
            out = None
        if key == 27 or key == ord('q'):
            break
    cap.release()
    out.release()

main()


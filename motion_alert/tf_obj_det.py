# A class to encapsulate TensorFlow object detection
import os
import cv2
import numpy as np
import tensorflow as tf
import label_map_util
import visualization_utils_mod as vis_util

class TFClassify:
    MODEL_NAME = 'ssdlite_mobilenet_v2_coco_2018_05_09'
    TENSORFLOW_DIR = '/home/pi/tensorflow1/models/research/object_detection'
    PATH_TO_CKPT = os.path.join(TENSORFLOW_DIR,MODEL_NAME,'frozen_inference_graph.pb')
    PATH_TO_LABELS = os.path.join(TENSORFLOW_DIR,'data','mscoco_label_map.pbtxt')
    NUM_CLASSES = 90

    def initClassifier(this):
        # load the model into memory and prepare input and output tensors
        this.label_map = label_map_util.load_labelmap(TFClassify.PATH_TO_LABELS)
        this.categories = label_map_util.convert_label_map_to_categories(this.label_map, max_num_classes=TFClassify.NUM_CLASSES, use_display_name=True)
        this.category_index = label_map_util.create_category_index(this.categories)
        # Load the Tensorflow model into memory.
        detection_graph = tf.Graph()
        with detection_graph.as_default():
            od_graph_def = tf.GraphDef()
            with tf.gfile.GFile(TFClassify.PATH_TO_CKPT, 'rb') as fid:
                serialized_graph = fid.read()
                od_graph_def.ParseFromString(serialized_graph)
                tf.import_graph_def(od_graph_def, name='')

            this.sess = tf.Session(graph=detection_graph)
        # Input tensor is the image
        this.image_tensor = detection_graph.get_tensor_by_name('image_tensor:0')

        # Output tensors are the detection boxes, scores, and classes
        # Each box represents a part of the image where a particular object was detected
        this.detection_boxes = detection_graph.get_tensor_by_name('detection_boxes:0')

        # Each score represents level of confidence for each of the objects.
        # The score is shown on the result image, together with the class label.
        this.detection_scores = detection_graph.get_tensor_by_name('detection_scores:0')
        this.detection_classes = detection_graph.get_tensor_by_name('detection_classes:0')

        # Number of objects detected
        this.num_detections = detection_graph.get_tensor_by_name('num_detections:0')
    
    def classify(this, image):
        # Using the model loaded by initClassifier, run object detection on the image

        THRESHOLD = 0.3 #ignore lower confidence matches
        
        frame_expanded = image[:,:,[2,1,0]] #BGR to RGB to match standard TensorFlow image format
        # Expand frame dimensions to have shape: [1, None, None, 3]
        # i.e. a single-column array, where each item in the column has the pixel RGB value
        frame_expanded = np.expand_dims(frame_expanded, axis=0)
        (boxes, scores, classes, num) = this.sess.run(
            [this.detection_boxes, this.detection_scores, this.detection_classes, this.num_detections],
            feed_dict={this.image_tensor: frame_expanded})
        dets = []
        boxes = np.squeeze(boxes)
        classes = np.squeeze(classes)
        scores = np.squeeze(scores)
        for i in range(len(boxes)):
            if scores[i] > THRESHOLD:
                dets.append((boxes[i], scores[i], classes[i], this.category_index[classes[i]]['name']))
        return dets

    def visualize(this, frame, dets):
        # Use TensorFlow vis_utils to draw the object detections on the frame
        boxes = np.array([det[0] for det in dets])
        classes = np.array([det[2] for det in dets], dtype=int)
        scores = np.array([det[1] for det in dets])
        vis_util.visualize_boxes_and_labels_on_image_array(
            frame,
            boxes,
            classes, 
            scores,
            this.category_index,
            use_normalized_coordinates=True,
            line_thickness=4,
            min_score_thresh=0.40)
        return frame
    

"""SSD Object Detection for Coral"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import numpy as np
import time

from edgetpu.detection.engine import DetectionEngine
from PIL import Image


def load_labels(filename):
    my_labels = []
    input_file = open(filename, 'r')
    for l in input_file:
        my_labels.append(l.strip())
    return my_labels


if __name__ == "__main__":
    floating_model = False

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--image", default="edgetpu/test_data/parrot.jpg", \
                        help="image to be classified")
    parser.add_argument("-m", "--model_file", \
                        default="edgetpu/test_data/mobilenet_ssd_v2_coco_quant_postprocess_edgetpu.tflite", \
                        help=".tflite model to be executed")
    parser.add_argument("-l", "--label_file", default="edgetpu/edgetpu_models/coco_labels.txt", \
                        help="name of file containing labels")
    parser.add_argument("-k", "--top_k", default=5, help="top_k")
    parser.add_argument("-t", "--threshold", default=0.0, help="threshold")
    parser.add_argument("-c", "--loop_counts", default=1, help="loop counts")
    parser.add_argument("-s", "--show_image", default=False, help="show image")
    parser.add_argument("-d", "--device_path", help="device_path")
    args = parser.parse_args()

    if args.device_path:
        engine = DetectionEngine(args.model_file, device_path=args.device_path)
    else:
        engine = DetectionEngine(args.model_file)
    print("device path:", engine.device_path())

    output_sizes = engine.get_all_output_tensors_sizes()
    # print("output sizes:", output_sizes)

    count = 0
    indices = []
    for i in output_sizes:
        count = count + i;
        indices.append(count)
    # print("indices:", indices)

    input_tensor_shape = engine.get_input_tensor_shape()
    if (input_tensor_shape.size != 4 or input_tensor_shape[3] != 3 or
            input_tensor_shape[0] != 1):
        raise RuntimeError('Invalid input tensor shape! Expected: [1, height, width, 3]')
    _, height, width, _ = input_tensor_shape
    print("height, width:", height, width)

    img = Image.open(args.image)
    img = img.resize((width, height))

    input_tensor = np.asarray(img).flatten()

    loop_counts = int(args.loop_counts)
    if (loop_counts > 1):
        for a in range(5):
            engine.RunInference(input_tensor)

    start_time = time.time()
    for a in range(loop_counts):
        _, raw_results = engine.RunInference(input_tensor)
    stop_time = time.time()
    print("time: ", (stop_time - start_time) * 1000 / loop_counts)
    num_boxes = int(raw_results[indices[2]])
    detected_boxes = (raw_results[:indices[0]] * height).reshape(num_boxes, 4)
    detected_classes = raw_results[indices[0]:indices[1]]
    detected_scores = raw_results[indices[1]:indices[2]]
    print("detected boxes:", detected_boxes)
    print("detected classes:", detected_classes)
    print("detected scores:", detected_scores)
    print("detected num:", num_boxes)
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import math

import numpy as np
import tensorflow as tf

from tensorflow.contrib.slim.python.slim.nets import inception
from tensorflow.python.framework import ops
from tensorflow.python.ops import control_flow_ops
from tensorflow.python.ops import data_flow_ops
from tensorflow.python.ops import variables
from tensorflow.python.training import saver as tf_saver
from tensorflow.python.training import supervisor

slim = tf.contrib.slim
checkpoint = 'models/model.ckpt'
label_dict_file = "models/dict.csv"
labelmap_file = 'models/labelmap.txt'
food_names = 'models/openimages_food.txt'
predictions = None
labelmap = None
label_dict = None
food_list = None
sess = None
input_image = None


def PreprocessImage(image, central_fraction=0.875):
  image = tf.cast(tf.image.decode_jpeg(image, channels=3), tf.float32)
  image = tf.image.central_crop(image, central_fraction=central_fraction)
  image = tf.expand_dims(image, [0])
  image = tf.image.resize_bilinear(image,
                                 [299, 299],
                                 align_corners=False)
  image = tf.multiply(image, 1.0/127.5)
  return tf.subtract(image, 1.0)


def LoadLabelMaps(num_classes, labelmap_path, dict_path):
  labelmap = [line.rstrip() for line in tf.gfile.GFile(labelmap_path).readlines()]
  label_dict = {}
  for line in tf.gfile.GFile(dict_path).readlines():
    words = [word.strip(' "\n') for word in line.split(',', 1)]
    label_dict[words[0]] = words[1]
  return labelmap, label_dict


def predict_on_image(image_path):
  global predictions
  global labelmap
  global label_dict
  global sess
  global input_image
  img_data = tf.gfile.FastGFile(image_path).read()
  predictions_eval = np.squeeze(sess.run(predictions, {input_image: img_data}))
  top_k = predictions_eval.argsort()[-20:][::-1]
  results = []
  for idx in top_k:
    mid = labelmap[idx]
    display_name = label_dict.get(mid, 'unknown')
    score = predictions_eval[idx]
    # if display_name in food_list:
    results.append([display_name, str(score)])
  return results


def prep_graph():
  global predictions
  global labelmap
  global label_dict
  global sess
  global input_image
  global food_list
  food_list = []
  with open(food_names) as f:
  	for x in f.read():
  		food_list.append(x.rstrip())
  g = tf.Graph()
  with g.as_default():
    input_image = tf.placeholder(tf.string)
    processed_image = PreprocessImage(input_image)
    with slim.arg_scope(inception.inception_v3_arg_scope()):
      logits, end_points = inception.inception_v3(
          processed_image, num_classes=6012, is_training=False)
    predictions = end_points['multi_predictions'] = tf.nn.sigmoid(
        logits, name='multi_predictions')
    init_op = control_flow_ops.group(variables.initialize_all_variables(),
                                     variables.initialize_local_variables(),
                                     data_flow_ops.initialize_all_tables())
    saver = tf_saver.Saver()
    sess = tf.Session()
    saver.restore(sess, checkpoint)
    labelmap, label_dict = LoadLabelMaps(6012, labelmap_file, label_dict_file)

prep_graph()
print("Loaded openimages module")

if __name__ == '__main__':
  import sys
  im_name = sys.argv[1]
  ret_dict = {}
  predict_on_image(im_name, ret_dict)

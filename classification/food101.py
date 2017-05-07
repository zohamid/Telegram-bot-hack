# Headless import fix
import matplotlib
matplotlib.use('Agg')

import matplotlib.image as img
import numpy as np

import collections

from keras.applications.inception_v3 import preprocess_input
from keras.models import load_model

label_mapping = 'models/food101_mapping.json'
checkpoint = 'models/model4b.10-0.68.hdf5'
model = None
ix_to_class = None


def ready_module():
	global model
	global label_mapping
	global ix_to_class
	ix_to_class = json.loads(label_mapping)
	model = load_model(filepath=checkpoint)


def center_crop(x, center_crop_size, **kwargs):
	centerw, centerh = x.shape[0]//2, x.shape[1]//2
	halfw, halfh = center_crop_size[0]//2, center_crop_size[1]//2
	return x[centerw-halfw:centerw+halfw+1,centerh-halfh:centerh+halfh+1, :]


def predict_10_crop(img, ix, top_n=5, plot=False, preprocess=True, debug=False):
	flipped_X = np.fliplr(img)
	crops = [
		img[:299,:299, :], # Upper Left
		img[:299, img.shape[1]-299:, :], # Upper Right
		img[img.shape[0]-299:, :299, :], # Lower Left
		img[img.shape[0]-299:, img.shape[1]-299:, :], # Lower Right
		center_crop(img, (299, 299)),
		flipped_X[:299,:299, :],
		flipped_X[:299, flipped_X.shape[1]-299:, :],
		flipped_X[flipped_X.shape[0]-299:, :299, :],
		flipped_X[flipped_X.shape[0]-299:, flipped_X.shape[1]-299:, :],
		center_crop(flipped_X, (299, 299))
	]
	if preprocess:
		crops = [preprocess_input(x.astype('float32')) for x in crops]
	if plot:
		fig, ax = plt.subplots(2, 5, figsize=(10, 4))
		ax[0][0].imshow(crops[0])
		ax[0][1].imshow(crops[1])
		ax[0][2].imshow(crops[2])
		ax[0][3].imshow(crops[3])
		ax[0][4].imshow(crops[4])
		ax[1][0].imshow(crops[5])
		ax[1][1].imshow(crops[6])
		ax[1][2].imshow(crops[7])
		ax[1][3].imshow(crops[8])
		ax[1][4].imshow(crops[9])
	y_pred = model.predict(np.array(crops))
	preds = np.argmax(y_pred, axis=1)
	top_n_preds= np.argpartition(y_pred, -top_n)[:,-top_n:]
	if debug:
		print('Top-1 Predicted:', preds)
		print('Top-5 Predicted:', top_n_preds)
		print('True Label:', y_test[ix])
	return preds, top_n_preds


def classify_image(image_path):
	pic = img.imread(image_path)
	preds = predict_10_crop(np.array(pic), 0)[0]
	best_pred = collections.Counter(preds).most_common(1)[0][0]
	return ix_to_class[best_pred]
	

ready_module()

if __name__ == "__main__":
	import sys
	img_path = sys.argv[1]
	print classify_image(img_path)

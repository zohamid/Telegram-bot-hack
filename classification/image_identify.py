import openimages
import food101


def classify_image(image_path):
	o_c = openimages.predict_on_image(image_path)
	f_c = food101.classify_image(image_path)

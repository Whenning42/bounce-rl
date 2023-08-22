import model_lib
import PIL
import numpy as np
import matplotlib.pyplot as plt
import glob

if __name__ == "__main__":
    m = model_lib.SpeedRecognitionSVM("models/svm.pkl")
    for im_file in sorted(glob.glob("out/reward_out/0*.png")):
        x, y, w, h = [int(c * .5) for c in [688, 1023, 96, 32]]
        im = PIL.Image.open(im_file)
        arr = np.asarray(im)
        crop = arr[y : y + h, x : x + w]
        print(arr.shape)
        print(crop.shape)
        
        pred = "".join(list(m([crop])[0]))
        print(pred)
        plt.imshow(crop)
        plt.show()


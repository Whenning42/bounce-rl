import tqdm

class View():
    def __init__(self, dataset, operators):
        self.dataset = dataset
        self.operators = operators

    def __len__(self):
        return len(self.dataset)

    def __getitem__(self, index):
        data = self.dataset[index]
        for op in self.operators:
            data.images = op.call(data.images)
        return data

from torchvision import transforms
import os
def WriteView(view, write_dir):
    to_pil = transforms.ToPILImage()

    if not os.path.exists(write_dir):
        os.mkdir(write_dir)

    # for datum in view:
    #     print("Writing to: ", os.path.join(write_dir, datum.image_keys[0] + ".png"))
    #     to_pil(datum.image).save(os.path.join(write_dir, datum.image_keys[0] + ".png"))
    print("Writing data to disk")
    for i in tqdm.tqdm(range(len(view))):
        datum = view[i : i + 1]
        to_pil(datum.images[0]).save(os.path.join(write_dir, datum.image_keys[0]))

import tqdm
import dataset
import torch
import os
import glob

class View():
    def __init__(self, source_dir, save_dir, dataset_operators, image_operators, DEBUG = True):
        self.dataset_operators = dataset_operators
        self.image_operators = image_operators

        if self._MatchesSavedSpec(save_dir):
            print("Requested view will be loaded from cache.")
            # Load the materialized view if cached.
            self.materialized_view = dataset.LoadImagesFromDir(save_dir, DEBUG)
        else:
            print("Requested view is not cached and will be generated.")
            # Materialize the view if it hasn't been cached.
            source_data = dataset.LoadImagesFromDir(source_dir, DEBUG)
            for op in self.dataset_operators:
                source_data = op.call(source_data)

            materialized_image = self._SliceView(source_data[0:1]).images[0]
            materialized_images = torch.empty((len(source_data), *materialized_image.shape))
            print("Materializing requested view.")
            for i in tqdm.tqdm(range(len(source_data)), leave = False):
                data_slice = source_data[i : i + 1]
                materialized_images[i] = self._SliceView(data_slice).images[0]

            self.materialized_view = dataset.Dataset(source_data.image_keys, \
                                                     materialized_images)

            WriteView(self.materialized_view, save_dir)
            self._WriteSpec(save_dir)


    def __len__(self):
        return len(self.materialized_view)

    def __getitem__(self, index):
        return self.materialized_view[index]

    def _SliceView(self, dataset):
        dataset_view = dataset
        for op in self.image_operators:
            dataset_view.images = op.call(dataset_view.images)
        return dataset_view

    def _SpecString(self):
        spec = ""

        for op in self.dataset_operators:
            spec += type(op).__name__
            if hasattr(op, 'spec'):
                spec += str(op.spec)
            spec += "\n"

        for op in self.image_operators:
            spec += type(op).__name__
            if hasattr(op, 'spec'):
                spec += str(op.spec)
            spec += "\n"

        return spec

    def _WriteSpec(self, save_dir):
        if not os.path.exists(save_dir):
            os.mkdir(save_dir)

        spec_path = os.path.join(save_dir, "spec.txt")
        with open(spec_path, 'w') as sf:
            sf.write(self._SpecString())

    def _MatchesSavedSpec(self, save_dir):
        spec_path = os.path.join(save_dir, "spec.txt")
        return os.path.exists(spec_path) and open(spec_path, 'r').read() == self._SpecString()

from torchvision import transforms
import os
def WriteView(view, write_dir):
    to_pil = transforms.ToPILImage()

    if not os.path.exists(write_dir):
        os.mkdir(write_dir)


    old_data = glob.glob(os.path.join(write_dir, '*'))
    for f in old_data:
        os.remove(f)

    # for datum in view:
    #     print("Writing to: ", os.path.join(write_dir, datum.image_keys[0] + ".png"))
    #     to_pil(datum.image).save(os.path.join(write_dir, datum.image_keys[0] + ".png"))
    print("Writing view to disk")
    for i in tqdm.tqdm(range(len(view)), leave = False):
        datum = view[i : i + 1]
        to_pil(datum.images[0]).save(os.path.join(write_dir, datum.image_keys[0]))

def _WriteLine(*args):
    line = ""
    for arg in args:
        if isinstance(arg, str):
            line += arg + ","
        elif isinstance(arg, dict):
            line += '"' + str(arg).replace("'", '""') + '"' + ","
        elif isinstance(arg, int):
            line += str(arg) + ","
        else:
            raise TypeError("_WriteLine passed a non-string/dict argument.")
    return line[:-1]

def WriteSliceLabels(slices_for_image, file_sizes, out_file):
    lines = ["filename,file_size,file_attributes,region_count,region_id,region_shape_attributes,region_attributes"]
    for image in slices_for_image:
        n = len(slices_for_image[image])
        for i, image_slice in enumerate(slices_for_image[image]):
            region_shape_attributes = {"name": "rect",
                                       "x": image_slice["src_x"],
                                       "y": image_slice["src_y"],
                                       "width": image_slice["w"],
                                       "height": image_slice["h"]}
            region_attributes = {"name": ""}
            filename = image_slice["image_key"]
            lines.append( \
                _WriteLine(filename, file_sizes[filename], {}, n, i, region_shape_attributes, region_attributes))

    with open(out_file, 'w') as f:
        f.writelines(line + '\n' for line in lines)

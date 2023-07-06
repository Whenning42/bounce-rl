from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize

import numpy

setup(
    ext_modules = cythonize( \
        [Extension("image_capture", \
                   ["src/image_capture.pyx"], \
                   libraries=["image_capture"], \
                   include_dirs=[numpy.get_include()])], \
                   build_dir="build"),
    options={'build': {'build_lib': 'build/lib'}}
)

from distutils.core import setup
from distutils.extension import Extension

import numpy
from Cython.Build import cythonize


def build(setup_kwargs):
    setup(
        ext_modules=cythonize(
            [
                Extension(
                    "bounce_rl.core.image_capture.image_capture",
                    ["bounce_rl/core/image_capture/image_capture.pyx"],
                    libraries=["image_capture"],
                    library_dirs=["meson_build/bounce_rl/core/image_capture/"],
                    include_dirs=[numpy.get_include()],
                )
            ],
            build_dir="cython_build",
        ),
        options={"build": {"build_lib": "bounce_rl/libs"}},
    )

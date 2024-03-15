x11_dep = dependency('x11')
xext_dep = dependency('xext')
libimage_capture = shared_library('libimage_capture', 'image_capture.c',
                                  dependencies: [x11_dep, xext_dep])


python = import('python').find_installation()
python_dep = python.dependency()

numpy_inc_dir = run_command(python,
  ['-c', 'import os; os.chdir(".."); import numpy; print(numpy.get_include())'],
  check : true
).stdout().strip()
numpy_include = include_directories(numpy_inc_dir)
numpy_dep = declare_dependency(include_directories: numpy_include)

python.extension_module(
    'image_capture',
    ['image_capture.pyx'],
    dependencies : [python_dep, numpy_dep],
    link_with: libimage_capture,
)
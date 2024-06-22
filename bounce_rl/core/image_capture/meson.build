x11_dep = dependency('x11')
xext_dep = dependency('xext')
xcomposite_dep = dependency('xcomposite')
libimage_capture = shared_library('image_capture', 'image_capture.c',
                                  dependencies: [x11_dep, xext_dep, xcomposite_dep])

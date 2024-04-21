x11_dep = dependency('x11')
xext_dep = dependency('xext')
xtest_dep = dependency('xtst')
xinput_dep = dependency('xi')

libmpx_input = shared_library('mpx_input', 'lib_mpx_input.c',
                              dependencies: [x11_dep , xext_dep, xtest_dep, xinput_dep])

cc = meson.get_compiler('cpp')
ldl_dep = cc.find_library('dl', required: true)
latomic_dep = cc.find_library('atomic', required: true)

libtime_control = shared_library('time_control', 'time_control.cpp',
                        dependencies: [ldl_dep, latomic_dep],
                        cpp_args: ['-pthread', '-std=c++17', '-fPIC', '-shared', '-march=native', '-O3', '-DDLSYM_OVERRIDE'])
libtime_control32 = shared_library('time_control32', 'time_control.cpp',
                        dependencies: [ldl_dep, latomic_dep],
                        cpp_args: ['-pthread', '-std=c++17', '-fPIC', '-shared', '-march=native', '-O3', '-m32', '-DDLSYM_OVERRIDE'],
                        link_args: ['-m32'])
meson.add_install_script('install_time_control.sh')

# Unit tests aren't properly disabled in our release build yet. They're manually
# disabled until I have a fix.
#
# lgtest_dep = cc.find_library('gtest', required: false)
# lgtest_main_dep = cc.find_library('gtest_main', required: false)
# time_control_test_exe = executable('time_control_exe', ['time_control_test.cpp', 'time_control.cpp'],
#                        dependencies: [ldl_dep, latomic_dep, lgtest_dep, lgtest_main_dep, lpthread],
#                        cpp_args: ['-pthread', '-std=c++17'])
# test('time_control_test', time_control_test_exe)

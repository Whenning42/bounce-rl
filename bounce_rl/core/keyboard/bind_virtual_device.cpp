#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "virtual_device.h"

namespace py = pybind11;

PYBIND11_MODULE(UserKeyboard, m) {
  py::class_<UserKeyboard>(m, "UserKeyboard")
    .def(py::init<>())
    .def("disable", &UserKeyboard::Disable)
    .def("enable", &UserKeyboard::Enable)
    .def("key_state", &UserKeyboard::KeyState)
    .def("is_halted", &UserKeyboard::IsHalted);
}

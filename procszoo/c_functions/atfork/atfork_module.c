#include <Python.h>

#include <stdlib.h>
#include <stdio.h>
#include <assert.h>

#include "atfork.h"

#if PY_MAJOR_VERSION >= 3
#define IS_PY3K 1
#else
#define IS_PY3K 0
#endif

static PyMethodDef atfork_methods[] = {
    {"atfork", atfork_pthread_atfork, METH_VARARGS, ""},
    {NULL, NULL, 0, NULL},
};


#if IS_PY3K

// Python 3 module initialization
static struct PyModuleDef atfork_module = {
    PyModuleDef_HEAD_INIT,
    "atfork",
    NULL,
    -1,
    atfork_methods
};

PyMODINIT_FUNC PyInit_atfork(void)
{
    return PyModule_Create(&atfork_module);
}

#else

// Python 2 module initialization
PyMODINIT_FUNC initatfork(void)
{
    Py_InitModule("atfork", atfork_methods);
}

#endif /* IS_PY3K */

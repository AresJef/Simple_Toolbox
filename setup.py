from setuptools import setup
from Cython.Build import cythonize
from distutils.extension import Extension

setup(
    ext_modules=cythonize(
        [
            Extension(
                name="simple_toolkits.cython_core.dt_parser_c",
                sources=["src/simple_toolkits/cython_core/dt_parser_c.pyx"],
                extra_compile_args=[
                    "-Wno-unreachable-code-fallthrough",
                    "-Wno-unused-function",
                ],
            ),
            "src/simple_toolkits/cython_core/dt_util_c.pyx",
            "src/simple_toolkits/cython_core/math_util_c.pyx",
            "src/simple_toolkits/cython_core/path_util_c.pyx",
            "src/simple_toolkits/cython_core/str_util_c.pyx",
        ],
        compiler_directives={"language_level": "3"},
    ),
)

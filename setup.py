import os
from setuptools import setup
from Cython.Build import cythonize
from distutils.extension import Extension

__package__ = "simple_toolbox"


def build_extension(cython_pkg: str) -> tuple[list[Extension]]:
    dir = os.path.abspath(os.path.dirname(__file__)) + "/src/" + cython_pkg
    pyx_list = [i for i in os.listdir(dir) if i.endswith(".pyx")]
    pyx_src = [os.path.join(dir, i) for i in pyx_list]
    pyx_name = [
        cython_pkg.replace("/", ".") + "." + i[:-4].replace("/", ".") for i in pyx_list
    ]
    return [
        Extension(
            name=name,
            sources=[src],
            extra_compile_args=[
                "-Wno-unreachable-code-fallthrough",
                "-Wno-unused-function",
            ],
        )
        for name, src in zip(pyx_name, pyx_src)
    ]


setup(
    ext_modules=cythonize(
        build_extension(f"{__package__}/cython_core"),
        compiler_directives={"language_level": "3"},
    ),
)

import os
from Cython.Build import cythonize
from distutils.extension import Extension
from setuptools import setup, find_packages


def build_extension(cython_dir: str) -> list[Extension]:
    dir = os.path.abspath(os.path.dirname(__file__)) + cython_dir
    pyx_list = [i for i in os.listdir(dir) if i.endswith(".pyx")]
    return [
        Extension(
            name=pyx.replace(".pyx", ""),
            sources=[os.path.join(dir, pyx)],
            extra_compile_args=[
                "-Wno-unreachable-code-fallthrough",
                "-Wno-unused-function",
            ]
            if pyx == "dt_parser_c.pyx"
            else [],
        )
        for pyx in pyx_list
    ]


setup(
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    ext_modules=cythonize(
        build_extension("/src/simple_toolbox/cython_core"),
        compiler_directives={"language_level": "3"},
    ),
)

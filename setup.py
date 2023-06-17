import os
from Cython.Build import cythonize
from distutils.extension import Extension
from setuptools import setup, find_packages


def build_extension(cython_dir: str) -> list[Extension]:
    dir = os.path.abspath(os.path.dirname(__file__)) + "/src/" + cython_dir
    pyx_list = [i for i in os.listdir(dir) if i.endswith(".pyx")]
    pyx_src = [os.path.join(dir, i) for i in pyx_list]
    pyx_name = [
        cython_dir.replace("/", ".") + "." + i[:-4].replace("/", ".") for i in pyx_list
    ]
    return [
        Extension(
            name=name,
            sources=[src.replace(".pyx", ".c"), src],
            extra_compile_args=[
                "-Wno-unreachable-code-fallthrough",
                "-Wno-unused-function",
            ]
            if src.endswith("dt_parser_c.pyx")
            else [],
        )
        for name, src in zip(pyx_name, pyx_src)
    ]


setup(
    ext_modules=cythonize(
        build_extension("simple_toolbox/cython_core"),
        compiler_directives={"language_level": "3"},
    ),
)

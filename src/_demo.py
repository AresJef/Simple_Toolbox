#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import os, simple_toolbox


def demo():
    captcha = os.path.join(os.path.dirname(__file__), "captcha-test.png")
    reader = simple_toolbox.ocr_util.CaptchaReader(gpu=True)
    print(reader)
    reader = simple_toolbox.ocr_util.CaptchaReader(gpu=True)
    print(reader)
    print(reader.read(captcha))
    print(reader.read(captcha))
    print(reader.read(captcha))


if __name__ == "__main__":
    demo()

#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import os, simple_toolkits


def demo():
    captcha = os.path.join(os.path.dirname(__file__), "captcha-test.png")
    reader = simple_toolkits.ocr_util.CaptchaReader()
    print(reader.read(captcha))
    print(reader.read(captcha))
    print(reader.read(captcha))


if __name__ == "__main__":
    demo()

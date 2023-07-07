# /usr/bin/python
# -*- coding: UTF-8 -*-
from __future__ import annotations
import io as _io
from PIL import Image as _Image
from easyocr import Reader as _Reader


class CaptchaReader:
    """A simple wrapper for `easyocr.Reader`.

    For more information about `easyocr`, please refer to:
    https://github.com/JaidedAI/EasyOCR
    """

    __instances: dict[str, CaptchaReader] = {}
    DEFAULT_LANGS: tuple[str] = ("en",)

    def __new__(cls, *langs: str, gpu: bool = True) -> CaptchaReader:
        if (_key := hash((langs, gpu))) not in cls.__instances:
            cls.__instances[_key] = super().__new__(cls)
            cls.__instances[_key].__init__(*langs, gpu=gpu)
        return cls.__instances[_key]

    def __init__(self, *langs: str, gpu: bool = True) -> None:
        """Both the `langs` and `gpu` parameters will be used as the key
        to identify the OCR Reader instance. If the same instance has
        been created before, it will be returned directly. This helps
        to avoid unnecessary initialization.

        :param langs: The languages to be used for OCR. If not specified, defaults to `'en'`.
            - `'en'` for English
            - `'ch_sim'` for Simplified Chinese
            - `'ch_tra'` for Traditional Chinese
            - `'ja'` for Japanese
            - For other supported languages, please refer to EasyOCR:
              https://www.jaided.ai/easyocr/

        :param gpu: Whether to use GPU for OCR, defaults to `True`.
        """

        if not langs:
            langs = self.DEFAULT_LANGS
        self.reader = _Reader(
            lang_list=list(langs),
            gpu=gpu,
            verbose=False,
            download_enabled=True,
            detector=True,
            recognizer=True,
        )
        self.langs: tuple[str] = langs
        self.gpu: bool = gpu

    def read(self, img: str | bytes) -> str | None:
        """Read the captcha image and return the text.

        :param img: The captcha image to be read.
            Accepts both the path of the image or image bytes.
        :return: The text in the captcha image. If no text is detected,
            `None` will be returned.
        """

        if isinstance(img, str):
            img = self._load_img_from_path(img)

        result = self.reader.readtext(img)
        result = " ".join([r[-2] for r in result])
        return result if result else None

    def _load_img_from_path(self, src: str) -> bytes:
        if src.endswith(".png"):
            format = "png"
        elif src.endswith(".jpg"):
            format = "jpeg"
        else:
            raise ValueError("Unsupported image format: {}".format(src))

        with _Image.open(src, mode="r") as img:
            img_byte_array = _io.BytesIO()
            img.save(img_byte_array, format=format, subsampling=0, quality=100)
            img_byte_array = img_byte_array.getvalue()
            return img_byte_array

    def __repr__(self) -> str:
        return "<CaptchaReader (langs=%s, gpu=%s)>" % (self.langs, self.gpu)

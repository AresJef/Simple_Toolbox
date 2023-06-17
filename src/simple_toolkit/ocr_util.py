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

    def __new__(cls, *lang: str, gpu: bool = True) -> CaptchaReader:
        lang = list(lang) if lang else ["en"]
        _key = "-".join(map(str, lang)) + "-" + str(gpu)
        if _key not in cls.__instances:
            cls.__instances[_key] = super().__new__(cls)
            cls.__instances[_key].__init__(*lang, gpu=gpu)
        return cls.__instances[_key]

    def __init__(self, *lang: str, gpu: bool = True) -> None:
        """Both the `lang` and `gpu` parameters will be used as the key
        to identify the OCR Reader instance. If the same instance has
        been created before, it will be returned directly. This helps
        to avoid unnecessary initialization.

        :param lang: The languages to be used for OCR.
            If not specified, English will be used.
        :param gpu: Whether to use GPU for OCR.
        """

        self.reader = _Reader(
            lang_list=list(lang) if lang else ["en"],
            gpu=gpu,
            verbose=False,
            download_enabled=True,
            detector=True,
            recognizer=True,
        )

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

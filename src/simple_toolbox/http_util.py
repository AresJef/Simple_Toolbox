# /usr/bin/python
# -*- coding: UTF-8 -*-
import asyncio
from io import BytesIO as _BytesIO

from PIL.Image import open as _open_image
from selectolax.parser import HTMLParser as _HTMLParser
from aiohttp import ClientSession as _ClientSession, ClientResponse as _ClientResponse

__all__ = ["request_source", "request_json", "download_image", "parse"]


async def request_source(
    url: str,
    *,
    cookies: dict = None,
    headers: dict = None,
    params: dict = None,
    data: dict = None,
    proxy: str = None,
    timeout: int = None,
    retry: int = 1,
) -> _HTMLParser:
    """Request source code from a url

    :param url: url to be requested
    :param cookies: cookies to be sent with request
    :param headers: headers to be sent with request
    :param params: params to be sent with request
    :param data: data to be sent with request
    :param proxy: proxy to be used for request
    :param timeout: timeout for request
    :param retry: number of retries when failed
    :return: source code of url <class 'selectolax.parser.HTMLParser'>
    """

    async with _ClientSession() as session:
        exception: Exception = None
        for _ in range(retry):
            try:
                async with session.get(
                    url,
                    cookies=cookies,
                    headers=headers,
                    params=params,
                    data=data,
                    proxy=proxy,
                    timeout=timeout,
                ) as res:
                    return _HTMLParser(await res.read())

            except Exception as err:
                exception = err
                await asyncio.sleep(0.2)

        exception.add_note(
            f"<http_util.request_source> Failed to request source code from: '{url}'"
        )
        raise exception


async def request_json(
    url: str,
    *,
    cookies: dict = None,
    headers: dict = None,
    params: dict = None,
    data: dict = None,
    proxy: str = None,
    timeout: int = None,
    retry: int = 1,
) -> dict:
    """Request json from a url

    :param url: url to be requested
    :param cookies: cookies to be sent with request
    :param headers: headers to be sent with request
    :param params: params to be sent with request
    :param data: data to be sent with request
    :param proxy: proxy to be used for request
    :param timeout: timeout for request
    :param retry: number of retries when failed
    :return: json of url <class 'dict'>
    """

    async with _ClientSession() as session:
        exception: Exception = None
        for _ in range(retry):
            try:
                async with session.get(
                    url,
                    cookies=cookies,
                    headers=headers,
                    params=params,
                    data=data,
                    proxy=proxy,
                    timeout=timeout,
                ) as res:
                    return await res.json()

            except Exception as err:
                exception = err
                await asyncio.sleep(0.2)

        exception.add_note(
            f"<http_util.request_json> Failed to request json from: '{url}'"
        )
        raise exception


async def download_image(
    src: str,
    *,
    cookies: dict = None,
    headers: dict = None,
    params: dict = None,
    data: dict = None,
    proxy: str = None,
    timeout: int = None,
    retry: int = 1,
) -> bytes:
    """Download image from url

    :param src: url to be requested
    :param cookies: cookies to be sent with request
    :param headers: headers to be sent with request
    :param params: params to be sent with request
    :param data: data to be sent with request
    :param proxy: proxy to be used for request
    :param timeout: timeout for request
    :param retry: number of retries when failed
    :return: image <class 'bytes'>
    """

    async with _ClientSession() as session:
        exception: Exception = None
        for _ in range(retry):
            try:
                async with session.get(
                    src,
                    cookies=cookies,
                    headers=headers,
                    params=params,
                    data=data,
                    proxy=proxy,
                    timeout=timeout,
                ) as res:
                    img = _open_image(_BytesIO(await res.read()))
                    img_byte_arr = _BytesIO()
                    img.save(img_byte_arr, format="PNG")
                    return img_byte_arr.getvalue()
            except Exception as err:
                exception = err
                await asyncio.sleep(0.2)

        exception.add_note(
            f"<http_util.download_image> Failed to download image from: '{src}'"
        )
        raise exception


async def parse(res: _ClientResponse) -> _HTMLParser:
    """Return the parsed source code

    :param res: response from request
    :return: source code of url <class 'selectolax.parser.HTMLParser'>
    """

    return _HTMLParser(res.content)

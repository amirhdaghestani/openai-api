"""This module contains configs for Service"""
import os


class ServiceConfig:
    """Necessary configs for Service.

    Attributes:

    """
    port = int(os.getenv("PORT")) \
           if os.getenv("PORT") else 5000
    url_swagger = str(os.getenv("URL_SWAGGER")) \
                  if os.getenv("URL_SWAGGER") else None
    url_redoc = str(os.getenv("URL_REDOC")) \
                if os.getenv("URL_REDOC") else None


    def __init__(self, port: int=None,
                 url_swagger: str=None,
                 url_redoc: str=None) -> None:
        if port:
            self.port = port
        if url_swagger:
            self.url_swagger = url_swagger
        if url_redoc:
            self.url_redoc = url_redoc

from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Sequence, Type, Union

from fastapi.datastructures import Default
from fastapi.params import Depends
from fastapi.responses import JSONResponse, Response
from fastapi.routing import APIRoute, APIRouter
from fastapi.utils import generate_unique_id
from starlette.routing import BaseRoute
from starlette.types import ASGIApp, Lifespan


class ZephyrRouter(APIRouter):
    """Custom APIRouter"""

    def __init__(
        self,
        *,
        prefix: str = "",
        tags: Optional[List[Union[str, Enum]]] = None,
        dependencies: Optional[Sequence[Depends]] = None,
        default_response_class: Type[Response] = JSONResponse,
        responses: Optional[Dict[Union[int, str], Dict[str, Any]]] = None,
        callbacks: Optional[List[BaseRoute]] = None,
        redirect_slashes: bool = True,
        default: Optional[ASGIApp] = None,
        lifespan: Optional[Lifespan[Any]] = None,
        deprecated: Optional[bool] = None,
        include_in_schema: bool = True,
        generate_unique_id_function: Callable[[APIRoute], str] = Default(
            generate_unique_id
        ),
    ):
        super().__init__(
            prefix=prefix,
            tags=tags,
            dependencies=dependencies,
            default_response_class=default_response_class,
            responses=responses,
            callbacks=callbacks,
            redirect_slashes=redirect_slashes,
            default=default,
            lifespan=lifespan,
            deprecated=deprecated,
            include_in_schema=include_in_schema,
            generate_unique_id_function=generate_unique_id_function,
        )

# -*- coding: utf-8 -*-
"""Declaration of FastAPI application."""
from typing import List, Optional

from aiida import orm
from aiida.cmdline.utils.decorators import with_dbenv
from aiida.orm.querybuilder import QueryBuilder
from fastapi import APIRouter, Depends

from aiida_restapi.models import Computer, User

from .auth import get_current_active_user

router = APIRouter()

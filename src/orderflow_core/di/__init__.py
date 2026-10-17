from dishka import Scope

from orderflow_core.di.app import setup_di
from orderflow_core.di.decorators import injectable
from orderflow_core.di.registry import DIRegistry

__all__ = [
    'DIRegistry',
    'Scope',
    'injectable',
    'setup_di',
]

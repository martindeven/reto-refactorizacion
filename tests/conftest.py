# -*- coding: utf-8 -*-
"""Configuracion compartida de las pruebas."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest

import gestor


@pytest.fixture(autouse=True)
def sistema_limpio():
    """Deja el sistema sin datos antes y despues de cada prueba."""
    gestor.reiniciar_sistema()
    yield
    gestor.reiniciar_sistema()

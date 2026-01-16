# models/__init__.py
from .database import StarcuakDB
from .ia_model import AnalizadorIA
from .file_manager import FileManager

__all__ = ["StarcuakDB", "AnalizadorIA", "FileManager"]

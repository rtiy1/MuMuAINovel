"""Vercel Python Function 入口。

将 backend 目录加入 Python 路径，并暴露 FastAPI `app` 给 Vercel。
"""
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.main import app  # noqa: E402,F401


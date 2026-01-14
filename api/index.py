import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app

# Vercel Serverless Function handler
from mangum import Mangum

asgi_handler = Mangum(app, lifespan="off")


def handler(event, context):
    return asgi_handler(event, context)

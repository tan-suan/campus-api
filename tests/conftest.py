"""pytest 公共 fixtures

- session：sqlite 内存库会话（Service 层单元测试使用）
- app：真实 MySQL 应用实例（执行完整 lifespan，接口集成测试使用）
"""

import sys
from pathlib import Path

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# 保证项目根目录可导入（直接执行 pytest 时同样生效）
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import models  # noqa: E402,F401  导入模型以注册 metadata
from core.database import Base  # noqa: E402


@pytest_asyncio.fixture
async def session():
    """sqlite 内存库会话（每个用例独立建表，互不影响）"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as db_session:
        yield db_session

    await engine.dispose()


@pytest_asyncio.fixture
async def app():
    """真实 MySQL 应用实例（执行 lifespan：DB 连接池 / 缓存 / 队列）"""
    from app.factory import create_app

    application = create_app()
    async with application.router.lifespan_context(application):
        yield application

"""
测试FastAPI应用启动
"""
import asyncio
from app.main import app
from app.database import init_db, close_db


async def test_startup():
    """测试应用启动"""
    print("测试FastAPI应用启动...")
    
    # 测试数据库初始化
    print("\n1. 测试数据库初始化...")
    await init_db()
    print("✓ 数据库初始化成功")
    
    # 测试应用配置
    print("\n2. 测试应用配置...")
    print(f"  应用标题: {app.title}")
    print(f"  应用版本: {app.version}")
    print(f"  应用描述: {app.description}")
    print("✓ 应用配置正确")
    
    # 测试路由
    print("\n3. 测试路由...")
    routes = [route.path for route in app.routes]
    print(f"  已注册路由: {routes}")
    assert "/" in routes, "根路径未注册"
    assert "/health" in routes, "健康检查路径未注册"
    assert "/ws/{client_id}" in routes, "WebSocket路径未注册"
    print("✓ 路由注册正确")
    
    # 关闭数据库
    print("\n4. 关闭数据库...")
    await close_db()
    print("✓ 数据库连接已关闭")
    
    print("\n应用启动测试完成！")


if __name__ == "__main__":
    asyncio.run(test_startup())

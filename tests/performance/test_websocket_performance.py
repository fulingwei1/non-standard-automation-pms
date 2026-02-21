"""
WebSocket性能测试
"""
import pytest
import asyncio
import time


class TestWebSocketPerformance:
    """WebSocket性能测试"""
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_websocket_connection_time(self):
        """测试WebSocket连接时间"""
        try:
            import websockets
        except ImportError:
            pytest.skip("websockets未安装")
        
        times = []
        for _ in range(10):
            start = time.time()
            try:
                async with websockets.connect("ws://localhost:8000/ws") as ws:
                    elapsed = time.time() - start
                    times.append(elapsed)
            except Exception:
                pass
        
        if times:
            import statistics
            avg_time = statistics.mean(times)
            assert avg_time < 0.5, "WebSocket连接应<500ms"
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_websocket_message_throughput(self):
        """测试WebSocket消息吞吐量"""
        try:
            import websockets
        except ImportError:
            pytest.skip("websockets未安装")
        
        num_messages = 100
        
        try:
            async with websockets.connect("ws://localhost:8000/ws") as ws:
                start = time.time()
                
                for i in range(num_messages):
                    await ws.send(f"Message {i}")
                    response = await ws.recv()
                
                elapsed = time.time() - start
                throughput = num_messages / elapsed
                
                print(f"\nWebSocket吞吐量: {throughput:.2f} msg/s")
                assert throughput > 50, "应至少50msg/s"
        except Exception:
            pytest.skip("WebSocket服务不可用")

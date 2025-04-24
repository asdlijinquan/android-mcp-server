#!/bin/bash
# 设置与Claude Desktop相同的环境变量
export PATH="/Users/jinquanli/Library/Android/sdk/platform-tools:/Users/jinquanli/.local/bin:$PATH"

# 输出当前环境信息
echo "=== Environment Information ==="
echo "PATH: $PATH"
echo "Current directory: $(pwd)"
echo "=== Running server.py with uv ==="

# 使用uv运行server.py
/Users/jinquanli/.local/bin/uv --directory /Users/jinquanli/StudioProjects/android-mcp-server run server.py 
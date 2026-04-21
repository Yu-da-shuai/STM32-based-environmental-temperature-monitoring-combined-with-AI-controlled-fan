# system_test.py
import requests
import json
from config import Config


def test_deepseek_integration():
    """测试DeepSeek API集成"""
    headers = {
        "Authorization": f"Bearer {Config.DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "user", "content": "测试温度控制：当前温度28度，最佳温度25度，容差2度，应该开启风扇吗？"}
        ]
    }

    response = requests.post(
        f"{Config.DEEPSEEK_API_URL}/chat/completions",
        headers=headers,
        json=data
    )

    if response.status_code == 200:
        result = response.json()
        print("✅ 系统集成测试成功！")
        print(f"AI决策建议: {result['choices'][0]['message']['content']}")
        return True
    else:
        print(f"❌ 集成测试失败: {response.status_code}")
        return False


if __name__ == "__main__":
    test_deepseek_integration()
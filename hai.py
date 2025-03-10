#!/usr/bin/env python3
import sys
import json
import re
from openai import OpenAI
from swarm import Swarm, Agent

# 初始化 Ollama 客戶端
_client = OpenAI(
    base_url='https://lionai-ollama.jincoco.site/v1',
    api_key='ollama',  # required, but unused
)
client = Swarm(client=_client)

# 定義 Agent
agent_integrator = Agent(
    name="agent_integrator_彙整者",
    model="deepseek-r1:70b",
    instructions="""
    你是一個終端機 AI 助手，擅長生成指令建議。根據用戶輸入，提供簡潔的指令及其用途，格式為：[指令] - [簡短說明]。
    回應以 JSON 格式包裝，包含 "Tips" 字段。若有多條建議，"Tips" 為陣列；若只有一條，"Tips" 為單一字串。例如：
    多條建議：
    ```json
    {"Tips": ["[tail -f /var/log/syslog] - 即時查看系統日誌", "[journalctl -xe] - 查看詳細服務日誌"]}
    ```
    單一建議：
    ```json
    {"Tips": "[cat /var/log/apache2/error.log] - 查看 Apache 錯誤日誌"}
    ```
"""
)

def call_llm_backend(query):
    try:
        # 使用 Swarm 客戶端發送請求，指定 agent
        response = client.run(
            agent=agent_integrator,
            messages=[{"role": "user", "content": query}]
        )
        # 提取最後一條訊息的內容
        raw_content = response.messages[-1]["content"]
        # 從回應中提取 JSON 數據
        json_data = extract_data(raw_content, "json")
        # 將 JSON 字串轉為 Python 字典
        response_dict = json.loads(json_data)
        # 處理 "Tips" 字段
        tips = response_dict["Tips"]
        # 如果是字串（單一建議），直接返回；如果是陣列（多條建議），用換行符連接
        if isinstance(tips, str):
            return tips
        elif isinstance(tips, list):
            return "\n".join(tips)
        else:
            return "後端回應格式錯誤"
    except Exception as e:
        return f"無法連接到 LLM 後端：{e}"

def extract_data(input_string, data_type):
    # 提取指定數據類型（如 json）的內容
    pattern = f"```{data_type}" + r"(.*?)(```|$)"
    matches = re.findall(pattern, input_string, re.DOTALL)
    return matches[0][0].strip() if matches else input_string

def main():
    if len(sys.argv) < 2:
        print("請輸入指令，例如：hai 給我一些log指令建議")
        sys.exit(1)

    # 將輸入參數合併成一個字串
    user_input = " ".join(sys.argv[1:])
    print(f"收到指令：{user_input}")

    # 呼叫 LLM 後端並顯示結果
    result = call_llm_backend(user_input)
    print(result)

if __name__ == "__main__":
    main()
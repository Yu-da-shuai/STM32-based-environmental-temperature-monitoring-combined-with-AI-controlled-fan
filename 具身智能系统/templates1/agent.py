import  json
import requests
import time
from config import Config

class EnvironmentAgent:
    def __init__(self):
        self.api_key = Config.DEEPSEEK_API_KEY
        self.api_url = Config.DEEPSEEK_API_URL
        self.headers ={
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    def make_decision(self,environment_data):
        #根据环境数据使用deepseekAPI做出决策
        temperature = environment_data.get('temperature',0.0)
        humidity = environment_data.get('humidity',0.0)
        #构造提示语
        prompt = f"当前环境的温度为{temperature}摄氏度，湿度为{humidity}%，请判断这个环境温度是否适合，是否需要开启风扇来调节温度？，请用JSON格式返回，包含'statue'字段（正常/需要调节）和'command'字段(fan_on/fan_off或不包含)。"

        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json={
                    "model":"deepseek-chat",
                    "messages":[
                         {"role":"system","content":"你是一个环境智能体，你需要根据温度和湿度数据半段时候需要开启风扇"},
                         {"role":"user","content":prompt}
                    ],
                    "temperature":0.3,
                    "response_format":{"type":"json_object"}
                }
            )


            response.raise_for_status()
            result = response.json()

            decision_content = result['choices'][0]['message']['content']
            decision = json.loads(decision_content)

            if "status" not in decision:
                decision["status"] = "正常"
            return decision

        except requests.RequestException as e:
            print(f"DeepSeek API调用失败：{e}")
            return self.local_decision(temperature)
        except json.JSONDecodeError:
            print("DeepSeek API返回的JOSN格式错误")
            return self.local_decision(temperature)

    def local_decision(self,temperature):

        if temperature > Config.TEMPERATURE_OPTIMAL + Config.TEMPERATURE_TOLERANCE:
            return{
                "status":"温度过高，需要调节",
                "command":"fan_on"
            }
        elif temperature < Config.TEMPERATURE_OPTIMAL - Config.TEMPERATURE_TOLERANCE:
            return{
                "status": "温度过低，无需调节",
                "command": "fan_off"
            }
        else:
            return{
                "status": "温度适宜，无需调节",
                "command": "fan_off"
            }
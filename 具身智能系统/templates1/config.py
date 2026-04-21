
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    #FastAPI配置
    FASTAPI_HOST = os.getenv('FASTAPI_HOST',"192.168.190.64") #手机地址
    FASTAPI_PORT = int(os.getenv('FASTAPI_PORT',8002))

    #TCP服务器配置
    TCP_HOST = os.getenv('TCP_HOST',"192.168.190.64")
    TCP_PORT = int(os.getenv('TCP_PORT',8001))

    #deepseek api配置
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY","sk-cd7273084d3848dfaef9aee6aa80aacf")#DEEPSEEK_API_KEY','your_deepseek_api_key_here
    DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"#deepseek官网
    #环境参数阈值
    TEMPERATURE_OPTIMAL = float(os.getenv('TEMPERATURE_OPTIMAL',"25.0"))#最佳温度
    TEMPERATURE_TOLERANCE = float(os.getenv('TEMPERATURE_TOLERANCE','2.0'))#温度容差
    TEMPERATURE_DEEPSEEK_OPTIMAL = 3

    #风扇控制指令
    FAN_ON = {"command":"fan_on"}
    FAN_OFF = {"command":"fan_off"}
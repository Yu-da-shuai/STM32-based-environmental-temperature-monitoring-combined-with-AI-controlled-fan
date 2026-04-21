import pyautogui
import pyperclip
import time
text = '？'
count = 5
print('5s后发送消息，将光标移动到聊天框内')
time.sleep(5)
for i in range(5):
    pyperclip.copy(text)
    pyautogui.hotkey('ctrl', 'v')
    pyautogui.press('enter')
    print('已发送第{}条'.format(i+1))
    time.sleep(1)
    print('已发送完毕')

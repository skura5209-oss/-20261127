import os
import threading
import webbrowser

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from langchain.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI

HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8000"))

SYSTEM_PROMPT = "你是一个聊天助手，你的语言风格很幽默，可以参考郭德纲的语言风格，可以适当使用网络流行语"

model = ChatOpenAI(model="qwen4-max",api_key="sk-ws-H.XDMHYIE.cZDL.MEYCIQC-L2wL9pNNiogCoWU9JQxkR-erjWbUuH_JIeOKTXz3NAIhAPzDFPYDniB01K56pbgHtFWf_UePuUd4nSlBlbpriOQp",base_url="https://cn-beijing.maas.qianwenaiapi.com/compatible-mode/v1",
                    temperature=1.2,
                    top_p=0.9,
                    extra_body={"enable_thinking": False}
                   )

app = FastAPI(title="郭式聊天助手")

# 全局会话（单会话）
messages = [SystemMessage(content=SYSTEM_PROMPT)]


class ChatRequest(BaseModel):
    message: str


@app.post("/chat")
async def chat(req: ChatRequest):
    messages.append(HumanMessage(content=req.message))
    try:
        res = await model.ainvoke(messages)   # 异步调用，不阻塞服务器
    except Exception as e:
        messages.pop()                        # 失败回滚，别在会话里留半截
        raise HTTPException(status_code=502, detail=f"模型调用失败：{e}")
    messages.append(res)
    content = res.content
    return {"reply": content}


@app.get("/reset")
async def reset():
    global messages
    messages = [SystemMessage(content=SYSTEM_PROMPT)]
    return {"ok": True}


INDEX_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>郭式聊天助手</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  html, body { height: 100%; }
  body {
    font-family: -apple-system, "Segoe UI", "Microsoft YaHei", sans-serif;
    background: linear-gradient(160deg, #f5f7fb 0%, #e9eef7 100%);
    display: flex; justify-content: center;
  }
  .app {
    width: 100%; max-width: 820px; height: 100vh;
    display: flex; flex-direction: column;
    background: #fff;
    box-shadow: 0 0 40px rgba(40, 60, 100, .08);
  }
  header {
    display: flex; align-items: center; justify-content: space-between;
    padding: 14px 20px;
    background: #1f2937; color: #fff;
  }
  header .title { font-size: 16px; font-weight: 600; letter-spacing: .5px; }
  #reset {
    border: 1px solid rgba(255,255,255,.35); background: transparent;
    color: #fff; padding: 6px 14px; border-radius: 8px; cursor: pointer;
    font-size: 13px; transition: background .2s;
  }
  #reset:hover { background: rgba(255,255,255,.12); }
  #reset:disabled { opacity: .5; cursor: not-allowed; }
  main {
    flex: 1; overflow-y: auto; padding: 20px;
    display: flex; flex-direction: column; gap: 12px;
    background: #f7f8fa;
  }
  .msg {
    max-width: 78%; padding: 10px 14px; border-radius: 14px;
    font-size: 15px; line-height: 1.6; white-space: pre-wrap; word-break: break-word;
  }
  .msg.user {
    align-self: flex-end; background: #2563eb; color: #fff;
    border-bottom-right-radius: 4px;
  }
  .msg.bot {
    align-self: flex-start; background: #fff; color: #1f2937;
    border: 1px solid #e5e7eb; border-bottom-left-radius: 4px;
  }
  .msg.error { border-color: #fca5a5; color: #b91c1c; background: #fef2f2; }
  .msg.typing { color: #9ca3af; font-style: italic; }
  footer {
    display: flex; gap: 10px; padding: 14px 20px;
    border-top: 1px solid #e5e7eb; background: #fff;
  }
  #input {
    flex: 1; resize: none; height: 46px; max-height: 140px;
    padding: 12px 14px; font-size: 15px; font-family: inherit;
    border: 1px solid #d1d5db; border-radius: 10px; outline: none;
    transition: border-color .2s;
  }
  #input:focus { border-color: #2563eb; }
  #send {
    width: 88px; border: none; border-radius: 10px; cursor: pointer;
    background: #2563eb; color: #fff; font-size: 15px;
    transition: background .2s, opacity .2s;
  }
  #send:hover { background: #1d4ed8; }
  #send:disabled { opacity: .55; cursor: not-allowed; }
</style>
</head>
<body>
  <div class="app">
    <header>
      <div class="title">🎭 郭式聊天助手</div>
      <button id="reset">清空会话</button>
    </header>
    <main id="chat">
      <div class="msg bot">您好，我是助手，有事儿您说话。（Enter 发送，Shift+Enter 换行）</div>
    </main>
    <footer>
      <textarea id="input" placeholder="输入消息…"></textarea>
      <button id="send">发送</button>
    </footer>
  </div>

<script>
const chat = document.getElementById('chat');
const input = document.getElementById('input');
const sendBtn = document.getElementById('send');
const resetBtn = document.getElementById('reset');
let busy = false;

function addMsg(text, who, cls) {
  const div = document.createElement('div');
  div.className = 'msg ' + who + (cls ? ' ' + cls : '');
  div.textContent = text;
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
  return div;
}

function autoGrow() {
  input.style.height = 'auto';
  input.style.height = Math.min(input.scrollHeight, 140) + 'px';
}

async function send() {
  const text = input.value.trim();
  if (!text || busy) return;
  busy = true;
  sendBtn.disabled = true;
  input.value = '';
  autoGrow();

  addMsg(text, 'user');
  const typing = addMsg('正在输入…', 'bot', 'typing');

  try {
    const res = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text })
    });
    const data = await res.json();
    typing.remove();
    if (!res.ok) {
      addMsg('出错了：' + (data.detail || res.status), 'bot', 'error');
    } else {
      const reply = typeof data.reply === 'string' ? data.reply : JSON.stringify(data.reply);
      addMsg(reply, 'bot');
    }
  } catch (e) {
    typing.remove();
    addMsg('网络错误：' + e, 'bot', 'error');
  } finally {
    busy = false;
    sendBtn.disabled = false;
    input.focus();
  }
}

sendBtn.addEventListener('click', send);
input.addEventListener('input', autoGrow);
input.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    send();
  }
});

resetBtn.addEventListener('click', async () => {
  resetBtn.disabled = true;
  try {
    await fetch('/reset');
    chat.innerHTML = '';
    addMsg('已清空，咱重新聊。', 'bot');
  } finally {
    resetBtn.disabled = false;
    input.focus();
  }
});
</script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def index():
    return INDEX_HTML


if __name__ == "__main__":
    url = f"http://{HOST}:{PORT}"
    print(f"\n✅ 聊天页面已启动：{url}\n")
    threading.Timer(1.2, webbrowser.open, args=(url,)).start()  # 自动打开浏览器
    uvicorn.run(app, host=HOST, port=PORT)

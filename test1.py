from openai import OpenAI
import os

client = OpenAI(
    # 如果没有配置环境变量，请用阿里云百炼API Key替换：api_key="sk-xxx"
    api_key="sk-ws-H.XDMIIYD.3ZsE.MEUCIQCeIi6-GB_GKbpvKtRS5YRv27225sydYxGwvzZ-WC3ouQIgbzHFlQ3Jf0bDvyil0SPO_0aUc1d0biD77bPc2SpIRtQ",
    base_url="https://ws-l1una3qgrxi4dqsc.cn-beijing.maas.aliyuncs.com/compatible-mode/v1",
)

messages = [{"role": "user", "content": "请帮我写一首以大雾为主题的诗，参考李清照的风格"}]
completion = client.chat.completions.create(
    model="qwen3.8-flash",  # 您可以按需更换为其它深度思考模型
    messages=messages,
    extra_body={"enable_thinking": True},
    stream=True,
    temperature=1.2,
    top_p=0.9
)
is_answering = False  # 是否进入回复阶段
print("\n" + "=" * 20 + "思考过程" + "=" * 20)
for chunk in completion:
    if not chunk.choices:
        continue
    delta = chunk.choices[0].delta
    if hasattr(delta, "reasoning_content") and delta.reasoning_content is not None:
        if not is_answering:
            print(delta.reasoning_content, end="", flush=True)
    if hasattr(delta, "content") and delta.content:
        if not is_answering:
            print("\n" + "=" * 20 + "完整回复" + "=" * 20)
            is_answering = True
        print(delta.content, end="", flush=True)
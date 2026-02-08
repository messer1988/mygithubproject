# gradio_chat_ru_pro.py — улучшенный интерфейс с очисткой и подсветкой кода

import gradio as gr
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from pathlib import Path
import re

# === Настройки модели ===
model_path = Path(__file__).resolve().parent
device = "mps" if torch.backends.mps.is_available() else "cpu"

print(f"🚀 Загружаем модель из: {model_path}")
print(f"💻 Используем устройство: {device}")

tokenizer = AutoTokenizer.from_pretrained(str(model_path))
model = AutoModelForCausalLM.from_pretrained(str(model_path)).to(device)
model.eval()


# === Очистка текста и подсветка кода ===
def clean_and_format(text):
    # удаляем все <|prompt|> <|answer|> и лишние повторы
    text = re.sub(r"<\|prompt\|>|<\|answer\|>", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()

    # распознаём shell-команды и подсвечиваем
    def highlight_code(match):
        code = match.group(1)
        return f"```bash\n{code.strip()}\n```"

    text = re.sub(r"(sudo .*?)(?=\n|$)", highlight_code, text)
    return text


# === Логика диалога ===
def chat(message, history):
    if history is None:
        history = []

    # используем только последний вопрос из истории
    prompt = f"<|prompt|> {message}\n<|answer|>"

    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, padding=True, max_length=1024).to(device)

    outputs = model.generate(
        **inputs,
        max_new_tokens=250,
        temperature=0.8,
        top_p=0.95,
        do_sample=True,
        pad_token_id=tokenizer.eos_token_id,
        eos_token_id=tokenizer.convert_tokens_to_ids("<|prompt|>"),
    )

    reply = tokenizer.decode(outputs[0], skip_special_tokens=True)
    reply = clean_and_format(reply.split("<|answer|>")[-1])

    history.append((message, reply))
    return history, history


# === Интерфейс ===
with gr.Blocks(theme=gr.themes.Soft(primary_hue="purple", secondary_hue="orange")) as demo:
    gr.Markdown(
        """
        ## 🤖 DevOps-LLM (ruGPT3small)
        Твоя персональная LLM-модель, обученная на 10 000 DevOps-промптах.  
        Спрашивай про Jenkins, Ansible, Helm, Nginx, Groovy, OpenShift и многое другое.
        """
    )

    chatbot = gr.Chatbot(label="Диалог", height=500, show_label=False)
    msg = gr.Textbox(label="Сообщение", placeholder="Напиши вопрос и нажми Enter...")
    clear = gr.Button("🧹 Очистить историю")

    msg.submit(chat, [msg, chatbot], [chatbot, chatbot])
    clear.click(lambda: None, None, chatbot, queue=False)

demo.queue()
demo.launch()
# gradio_chat_ru_pro.py — ChatGPT-подобный интерфейс для твоей модели DevOps-LLM на ruGPT3small

import gradio as gr
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from pathlib import Path

# === Настройки модели ===
model_path = Path(__file__).resolve().parent
device = "mps" if torch.backends.mps.is_available() else "cpu"

print(f"🚀 Загрузка модели из: {model_path}")
print(f"💻 Используем устройство: {device}")

tokenizer = AutoTokenizer.from_pretrained(str(model_path))
model = AutoModelForCausalLM.from_pretrained(str(model_path)).to(device)
model.eval()

# === Логика диалога ===
def chat(message, history):
    if history is None:
        history = []

    # Формируем весь контекст истории
    dialogue = ""
    for user, bot in history:
        dialogue += f"<|prompt|> {user}\n<|answer|> {bot}\n"

    # Добавляем текущий вопрос
    dialogue += f"<|prompt|> {message}\n<|answer|>"

    inputs = tokenizer(dialogue, return_tensors="pt", truncation=True, padding=True, max_length=1024).to(device)

    outputs = model.generate(
        **inputs,
        max_new_tokens=300,
        temperature=0.8,
        top_p=0.95,
        do_sample=True,
        pad_token_id=tokenizer.eos_token_id,
    )

    reply = tokenizer.decode(outputs[0], skip_special_tokens=True)
    reply = reply.split("<|answer|>")[-1].strip()

    history.append((message, reply))
    return history, history


# === UI ===
with gr.Blocks(theme=gr.themes.Soft(primary_hue="purple", secondary_hue="orange")) as demo:
    gr.Markdown(
        """
        ## 🤖 DevOps-LLM (ruGPT3small)
        Твоя персональная LLM-модель, обученная на 10 000 DevOps-промптах.  
        Спрашивай про Jenkins, Ansible, Helm, Nginx, Groovy и многое другое.
        """
    )

    chatbot = gr.Chatbot(label="Диалог", height=500, show_label=False)
    msg = gr.Textbox(label="Сообщение", placeholder="Напиши вопрос и нажми Enter...")
    clear = gr.Button("🧹 Очистить историю")

    msg.submit(chat, [msg, chatbot], [chatbot, chatbot])
    clear.click(lambda: None, None, chatbot, queue=False)

demo.queue()
demo.launch()
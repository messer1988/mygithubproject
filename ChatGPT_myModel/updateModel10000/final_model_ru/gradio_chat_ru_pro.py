import gradio as gr
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from pathlib import Path

model_path = Path(__file__).resolve().parent
device = "mps" if torch.backends.mps.is_available() else "cpu"

print(f"🚀 Loading model from: {model_path}")
print(f"💻 device: {device}")

tokenizer = AutoTokenizer.from_pretrained(str(model_path))
model = AutoModelForCausalLM.from_pretrained(str(model_path)).to(device)
model.eval()

STOP_PROMPT = "<|prompt|>"
ANSWER_TAG = "<|answer|>"

def generate_answer(user_text: str) -> str:
    prompt = f"{STOP_PROMPT} {user_text}\n{ANSWER_TAG}"
    inputs = tokenizer(prompt, return_tensors="pt").to(device)

    outputs = model.generate(
        **inputs,
        max_new_tokens=220,
        temperature=0.7,
        top_p=0.9,
        do_sample=True,
        repetition_penalty=1.15,
        no_repeat_ngram_size=3,
        pad_token_id=tokenizer.eos_token_id,
    )

    text = tokenizer.decode(outputs[0], skip_special_tokens=True)

    # оставляем только кусок после <|answer|>
    if ANSWER_TAG in text:
        text = text.split(ANSWER_TAG, 1)[1]

    # если модель “поползла” в следующий prompt — обрезаем
    if STOP_PROMPT in text:
        text = text.split(STOP_PROMPT, 1)[0]

    return text.strip()

def chat(message, history):
    history = history or []
    reply = generate_answer(message)
    history.append((message, reply))
    return history, history

with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("## 🤖 DevOps-LLM (ruGPT3small) — local")
    chatbot = gr.Chatbot(height=520, show_label=False)
    msg = gr.Textbox(placeholder="Напиши вопрос и нажми Enter…", label="Сообщение")
    clear = gr.Button("🧹 Очистить")

    msg.submit(chat, [msg, chatbot], [chatbot, chatbot])
    clear.click(lambda: None, None, chatbot, queue=False)

demo.queue()
demo.launch()
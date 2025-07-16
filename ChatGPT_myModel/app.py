import gradio as gr
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

# Имя модели на Hugging Face
model_id = "PythonDevops/devops-llm"

# Загружаем токенизатор и модель
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(model_id)

# Функция общения с моделью
def chat_with_model(message, history=[]):
    # Токенизируем вход
    inputs = tokenizer(message, return_tensors="pt")

    # Генерируем ответ
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=200,
            pad_token_id=tokenizer.eos_token_id
        )

    # Декодируем полный текст
    full_output = tokenizer.decode(outputs[0], skip_special_tokens=True)

    # Удаляем повтор вопроса в начале
    if full_output.startswith(message):
        reply = full_output[len(message):].strip()
    else:
        reply = full_output.strip()

    return reply

# Интерфейс Gradio
chat_ui = gr.Interface(
    fn=chat_with_model,
    inputs=gr.Textbox(lines=2, placeholder="Задай вопрос по DevOps..."),
    outputs="text",
    title="💬 DevOps Chat — твоя модель",
    description="Спрашивай о Jenkins, Ansible, Linux, Docker, Go и т.д.",
    theme="default"
)

# Запуск
if __name__ == "__main__":
    chat_ui.launch()
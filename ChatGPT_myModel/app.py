import gradio as gr
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

model_id = "PythonDevops/devops-llm"

# Загрузка токенизатора и модели
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(model_id)

# Функция общения с моделью
def chat_with_model(message, history=[]):
    # Добавляем историю в prompt (если нужно)
    prompt = message
    inputs = tokenizer(prompt, return_tensors="pt")

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=200,
            pad_token_id=tokenizer.eos_token_id
        )

    reply = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return reply

# Интерфейс Gradio
chat_ui = gr.Interface(
    fn=chat_with_model,
    inputs="text",
    outputs="text",
    title="💬 DevOps LLM Chat",
    description="Задай вопрос по Jenkins, Ansible, Linux и т.д.",
)

# Запуск
if __name__ == "__main__":
    chat_ui.launch()
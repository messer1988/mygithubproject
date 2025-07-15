from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

model_name = "./trained_model"  # Папка с твоей дообученной моделью

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

# Текст запроса
input_text = "Как перезапустить Jenkins?"

# Токенизация входа
inputs = tokenizer(input_text, return_tensors="pt")

# Генерация ответа
outputs = model.generate(
    inputs["input_ids"],
    max_length=50,
    num_return_sequences=1,
    do_sample=True,
    top_p=0.95,
    top_k=50,
)

# Раскодируем ответ
generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)

print("=== Запрос ===")
print(input_text)
print("\n=== Ответ модели ===")
print(generated_text)
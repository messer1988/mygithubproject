from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

# === Путь к дообученной модели ===
model_path = "./trained_model"

# === Загрузка модели и токенизатора ===
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(model_path)

# === Ввод запроса ===
input_text = "Как перезапустить Jenkins?"

# === Токенизация с attention_mask ===
inputs = tokenizer(
    input_text,
    return_tensors="pt",
    padding=True,
    truncation=True,
)

# === Генерация с параметрами управления ===
outputs = model.generate(
    input_ids=inputs["input_ids"],
    attention_mask=inputs["attention_mask"],
    max_length=64,
    num_return_sequences=1,
    do_sample=True,
    top_k=50,
    top_p=0.95,
    temperature=0.7,
    pad_token_id=tokenizer.eos_token_id,  # важно для корректного вывода
)

# === Раскодировка и вывод ===
generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)

print("\n=== Запрос ===")
print(input_text)
print("\n=== Ответ модели ===")
print(generated_text)
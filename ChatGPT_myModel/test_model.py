from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

# === Путь к дообученной модели ===
model_path = "D:/ChatGPT_myModel/final_model"

# === Загрузка модели и токенизатора ===
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(model_path)

# === Запрос от пользователя
while True:
    input_text = input("\n🔍 Вопрос (или 'exit'): ")
    if input_text.lower() in ["exit", "quit", "выход"]:
        break

    inputs = tokenizer(
        input_text,
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=128
    )

    # === Генерация
    outputs = model.generate(
        input_ids=inputs["input_ids"],
        attention_mask=inputs["attention_mask"],
        max_length=128,
        num_return_sequences=1,
        do_sample=True,
        top_k=50,
        top_p=0.9,
        temperature=0.7,
        pad_token_id=tokenizer.eos_token_id
    )

    # === Раскодировка
    result = tokenizer.decode(outputs[0], skip_special_tokens=True)

    print("\n🤖 Ответ модели:\n", result)
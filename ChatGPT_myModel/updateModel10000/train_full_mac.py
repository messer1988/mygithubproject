# train_rugpt3small.py — обучение русской GPT2 (ruGPT3small) на DevOps датасете

from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from datasets import load_dataset
import torch

# 🚀 Определяем устройство (GPU M1)
device = "mps" if torch.backends.mps.is_available() else "cpu"
print(f"Используем устройство: {device}")

# 🧠 Берём русскую GPT2 от Сбера
model_id = "sberbank-ai/rugpt3small_based_on_gpt2"

# Загружаем токенизатор и модель
tokenizer = AutoTokenizer.from_pretrained(model_id)
tokenizer.pad_token = tokenizer.eos_token  # GPT2 не имеет pad_token
model = AutoModelForCausalLM.from_pretrained(model_id).to(device)

# 📘 Загружаем твой датасет
dataset = load_dataset("json", data_files="devops_dataset_10000.jsonl")

# 🧩 Преобразуем формат
def preprocess(example):
    text = f"<|prompt|> {example['prompt']}\n<|answer|> {example['completion']}"
    return tokenizer(text, truncation=True, padding="max_length", max_length=512)

tokenized = dataset["train"].map(preprocess, remove_columns=dataset["train"].column_names)

# ⚙️ Параметры обучения
training_args = TrainingArguments(
    output_dir="./final_model_ru",
    overwrite_output_dir=True,
    per_device_train_batch_size=1,  # экономия памяти M1
    gradient_accumulation_steps=4,
    num_train_epochs=3,
    warmup_steps=100,
    save_strategy="epoch",
    logging_dir="./logs_ru",
    logging_steps=10,
    fp16=False,
    report_to="none"
)

# 🧑‍🏫 Trainer — основа обучения
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized,
    data_collator=DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False),
)

# 🚀 Запуск
trainer.train()

# 💾 Сохраняем итоговую модель
trainer.save_model("./final_model_ru")
tokenizer.save_pretrained("./final_model_ru")
print("✅ Обучение завершено. Модель сохранена в ./final_model_ru")
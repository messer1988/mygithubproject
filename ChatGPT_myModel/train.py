from transformers import AutoTokenizer, AutoModelForCausalLM, Trainer, TrainingArguments
from datasets import load_dataset

# === Параметры ===
model_name = "gpt2"
data_path = "devops_1000.jsonl"  # Убедись, что файл лежит рядом с train.py
output_dir = "./final_model"

# === Загрузка токенизатора и модели ===
tokenizer = AutoTokenizer.from_pretrained(model_name)
tokenizer.pad_token = tokenizer.eos_token  # GPT-2 не имеет pad_token

model = AutoModelForCausalLM.from_pretrained(model_name)

# === Загрузка датасета
dataset = load_dataset("json", data_files=data_path, split="train")

# === Токенизация
def tokenize_function(examples):
    tokens = tokenizer(
        examples["text"],
        truncation=True,
        padding="max_length",
        max_length=128,
    )
    tokens["labels"] = tokens["input_ids"].copy()
    return tokens

tokenized_dataset = dataset.map(tokenize_function, batched=True)

# === Настройки обучения
training_args = TrainingArguments(
    output_dir="./results",
    num_train_epochs=5,                          # Можно увеличить при необходимости
    per_device_train_batch_size=4,
    gradient_accumulation_steps=2,               # Для экономии памяти
    warmup_steps=20,
    weight_decay=0.01,
    logging_dir="./logs",
    logging_steps=10,
    save_steps=200,
    save_total_limit=1,
    report_to="none",                            # отключить wandb, tensorboard и т.п.
    fp16=False,                                  # True если на GPU с поддержкой FP16
)

# === Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset,
)

# === Старт обучения
trainer.train()

# === Сохраняем модель
model.save_pretrained(output_dir)
tokenizer.save_pretrained(output_dir)

print("\n✅ Модель успешно обучена и сохранена в:", output_dir)
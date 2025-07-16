# train_full.py — продвинутое обучение на 10,000 примерах

from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments, Trainer, DataCollatorForLanguageModeling
from datasets import load_dataset
import torch

# Параметры модели и токенизатора
model_id = "gpt2"
tokenizer = AutoTokenizer.from_pretrained(model_id)
tokenizer.pad_token = tokenizer.eos_token

model = AutoModelForCausalLM.from_pretrained(model_id)

# Загрузка нашего JSONL датасета
dataset = load_dataset("json", data_files="devops_dataset_10000.jsonl")

# Преобразование текстов

def preprocess(example):
    formatted = f"<|prompt|> {example['prompt']}\n<|answer|> {example['completion']}"
    return tokenizer(formatted, truncation=True, padding="max_length", max_length=512)

# Применим токенизацию
tokenized = dataset["train"].map(preprocess, remove_columns=dataset["train"].column_names)

# Аргументы обучения
args = TrainingArguments(
    output_dir="./final_model",
    per_device_train_batch_size=2,
    gradient_accumulation_steps=2,
    num_train_epochs=3,
    warmup_steps=100,
    logging_dir="./logs",
    logging_steps=10,
    save_strategy="epoch",
    save_total_limit=2,
    fp16=torch.cuda.is_available(),
    report_to="none"
)

trainer = Trainer(
    model=model,
    args=args,
    train_dataset=tokenized,
    data_collator=DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False),
)

# Запуск обучения
trainer.train()

# Сохраняем финальную модель
trainer.save_model("./final_model")
tokenizer.save_pretrained("./final_model")
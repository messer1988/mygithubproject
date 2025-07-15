from transformers import AutoModelForCausalLM, AutoTokenizer, Trainer, TrainingArguments
import datasets

# Используем базовую GPT-2
model_name = "gpt2"

# Загружаем токенизатор и модель
tokenizer = AutoTokenizer.from_pretrained(model_name)
tokenizer.pad_token = tokenizer.eos_token  # GPT-2 не имеет pad_token — используем eos

model = AutoModelForCausalLM.from_pretrained(model_name)

# Простейший мини-датасет (можно расширить позже)
data = {
    "train": [
        {"text": "Как перезапустить Jenkins? Перезапустить systemctl jenkins."},
        {"text": "Как сделать деплой через Ansible? Использовать ansible-playbook."},
    ]
}

# Токенизация + добавление labels
def tokenize_function(examples):
    tokenized = tokenizer(
        examples["text"],
        truncation=True,
        padding="max_length",
        max_length=64,
    )
    tokenized["labels"] = tokenized["input_ids"].copy()
    return tokenized

# Создание и токенизация датасета
dataset = datasets.Dataset.from_list(data["train"])
tokenized_dataset = dataset.map(tokenize_function, batched=True)

# Параметры обучения
training_args = TrainingArguments(
    output_dir="./results",
    num_train_epochs=1,
    per_device_train_batch_size=2,
    logging_steps=2,
    save_steps=10,
    save_total_limit=1,
)

# Создаём Trainer и запускаем обучение
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset,
)

trainer.train()

# 💾 Сохраняем обученную модель и токенизатор
model.save_pretrained("./trained_model")
tokenizer.save_pretrained("./trained_model")
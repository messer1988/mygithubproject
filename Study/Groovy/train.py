from transformers import AutoModelForCausalLM, AutoTokenizer, Trainer, TrainingArguments
import datasets

# 1. Название модели — лёгкая модель для обучения
model_name = "gpt2"  # Можно заменить на другую легкую модель

# 2. Загрузка модели и токенизатора
tokenizer = AutoTokenizer.from_pretrained(model_name)
tokenizer.pad_token = tokenizer.eos_token   # <- добавь эту строку
model = AutoModelForCausalLM.from_pretrained(model_name)

# 3. Мини-датасет: пара "вопрос-ответ"
data = {
    "train": [
        {"text": "Как перезапустить Jenkins? Перезапустить systemctl jenkins."},
        {"text": "Как сделать деплой через Ansible? Использовать ansible-playbook."},
    ]
}

# 4. Преобразование данных в Dataset
def tokenize_function(examples):
    return tokenizer(examples["text"], truncation=True, padding="max_length", max_length=64)

dataset = datasets.Dataset.from_list(data["train"])
tokenized_dataset = dataset.map(tokenize_function, batched=True)

# 5. Параметры обучения
training_args = TrainingArguments(
    output_dir="./results",
    num_train_epochs=1,
    per_device_train_batch_size=2,
    logging_steps=2,
    save_steps=10,
    save_total_limit=1,
)

# 6. Инициализация тренера
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset,
)

# 7. Запуск обучения
trainer.train()
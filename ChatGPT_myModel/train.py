from transformers import AutoModelForCausalLM, AutoTokenizer, Trainer, TrainingArguments
import datasets

model_name = "gpt2"

# Загрузка токенизатора и модели
tokenizer = AutoTokenizer.from_pretrained(model_name)
tokenizer.pad_token = tokenizer.eos_token  # Устанавливаем pad_token

model = AutoModelForCausalLM.from_pretrained(model_name)

# Мини-датасет с парой "вопрос-ответ"
data = {
    "train": [
        {"text": "Как перезапустить Jenkins? Перезапустить systemctl jenkins."},
        {"text": "Как сделать деплой через Ansible? Использовать ansible-playbook."},
    ]
}

# Функция токенизации с добавлением labels
def tokenize_function(examples):
    tokenized = tokenizer(
        examples["text"],
        truncation=True,
        padding="max_length",
        max_length=64,
    )
    tokenized["labels"] = tokenized["input_ids"].copy()
    return tokenized

dataset = datasets.Dataset.from_list(data["train"])
tokenized_dataset = dataset.map(tokenize_function, batched=True)

training_args = TrainingArguments(
    output_dir="./results",
    num_train_epochs=1,
    per_device_train_batch_size=2,
    logging_steps=2,
    save_steps=10,
    save_total_limit=1,
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset,
)

trainer.train()
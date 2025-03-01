import pandas as pd 
import numpy as np
import matplotlib as plt
import seaborn as sns
import torch
from transformers import BertTokenizer, BertForSequenceClassification
from datasets import load_dataset
from transformers import Trainer, TrainingArguments
from sklearn.metrics import accuracy_score,precision_recall_fscore_support, confusion_matrix

dataset = load_dataset("imdb")
tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')

def tokenizing_function(example):
    return tokenizer(example['text'], paddind='max_length', truncation=True, max_length=512)

tokenized_datasets = dataset.map(tokenizing_function, batched=True)
tokenized_datasets = tokenized_datasets.rename_column("label", "labels")
tokenized_datasets.set_format('torch', colums=['input_ids','attention_mask', 'labels'])

train_dataset = tokenized_datasets['train']
test_dataset = tokenized_datasets['test']

model = BertForSequenceClassification.from_pretrained('bert-base-uncased', num_labels=2)

device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')
model.to(device)

training_args = TrainingArguments(
    output_dir='./results',
    num_train_epochs=2,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=16,
    warmup_steps=500,
    weight_decay=0.01,
    logging_dir='./logs',
    logging_steps=10,
    evaluation_strategy="epoch",
    save_strategy="epoch",
    load_best_model_at_end=True,
    report_to="none"
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=test_dataset
)

trainer.train()

#evaluation
def compute_metrics(eval_pred):
    logits, labels = eval_pred
    predictions = torch.argmax(torch.tensor(logits), dim=1).numpy()
    labels = labels
    accuracy = accuracy_score(labels, predictions)
    precision, recall, f1, _ = precision_recall_fscore_support(labels, predictions, average='binary')
    return {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1': f1
    }

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=test_dataset,
    compute_metrics=compute_metrics
)

result = trainer.evaluate()

##confusion Matrix

predictions = trainer.predict(test_dataset)
preds = np.argmax(predictions.predictions, axis=1)
labels = predictions.label_ids

cm = confusion_matrix(labels, preds)
sns.heatmap(cm, annot=True, fmt='d', cmap='Red', xticklabels=['Negative', 'Positive'], yticklabels=['Negative', 'Positive'])

plt.xlabel('predicted')
plt.ylabel('True')
plt.title('Confusion Matrix')

plt.show()

## testing the model:

example_sentences = [
    "I absolutely loved this movie! The performances were outstanding.",
    "This was the worst film I have ever seen. Completely disappointing.",
    "The plot was intriguing, but the characters were underdeveloped.",
    "An average movie with some good moments and some bad ones.",
    "I was not impressed by the storyline or the acting.",
    "Fantastic visuals and a gripping story. Highly recommend!",
    "The movie was okay, nothing special but not terrible either.",
    "I didn't enjoy this movie at all. It was a waste of time.",
    "A masterpiece of modern cinema. Truly inspiring.",
    "Mediocre at best. I expected much more from this director."
]

def predict_sentiment(sentence):

    inputs = tokenizer.encode_plus(
        sentence,
        add_special_tokens=True,
        max_length=512,
        truncation=True,
        padding='max_length',
        return_tensors='pt'
    )

    input_ids = inputs['input_ids'].to(device)
    attention_mask = inputs['attention_mask'].to(device)

    with torch.no_grad():
        outputs = model(input_ids=input_ids, attention_mask=attention_mask)

    logits = outputs.logistpredicted_class_id = logits.argmax().item()
    predicted_class_id = logits.argmax().item()
    label = 'Positive' if predicted_class_id == 1 else 'Negative'

    return label

results = []

for sentences in example_sentences:
    prediction = predict_sentiment(sentences)
    results.append({"sentence":sentences, "Sentiment":prediction})

dataframe_result = pd.DataFrame(results)

print(dataframe_result)

# backend/app/services/finbert_utils.py
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import gc

# Check device availability
device = "cuda:0" if torch.cuda.is_available() else "cpu"

tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert").to(device)
labels = ["positive", "negative", "neutral"]

def estimate_sentiment(news):
    if news:
        # CRITICAL: Use no_grad() to save 50% memory during inference
        with torch.no_grad():
            tokens = tokenizer(news, return_tensors="pt", padding=True).to(device)
            # Pass inputs correctly to model
            outputs = model(tokens["input_ids"], attention_mask=tokens["attention_mask"])
            result = outputs.logits
            result = torch.nn.functional.softmax(torch.sum(result, 0), dim=-1)
            
            probability = result[torch.argmax(result)].item() # Convert tensor to float immediately
            sentiment = labels[torch.argmax(result)]
            
            # Delete tensors immediately to free RAM
            del tokens
            del result
            del outputs
            
        # Force cleanup
        if device == "cuda":
            torch.cuda.empty_cache()
        gc.collect()

        return probability, sentiment
    else:
        return 0, labels[-1]

if __name__ == "__main__":
    tensor, sentiment = estimate_sentiment(['markets responded negatively to the news!','traders were displeased!'])
    print(tensor, sentiment)
    print(torch.cuda.is_available())
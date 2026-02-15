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
            
            # Sum the logits across all headlines first
            summed_logits = torch.sum(result, 0)
            
            # Apply Softmax to get probabilities [Pos, Neg, Neu]
            probs = torch.nn.functional.softmax(summed_logits, dim=-1)
            
            # Extract raw scores (Indices: 0=Positive, 1=Negative, 2=Neutral)
            pos_score = probs[0].item()
            neg_score = probs[1].item()
            # We ignore neu_score = probs[2].item()
            
            # Delete tensors immediately to free RAM
            del tokens
            del result
            del outputs
            
        # Force cleanup
        if device == "cuda":
            torch.cuda.empty_cache()
        gc.collect()

        # --- LOGIC UPDATE: BINARY FORCING ---
        # Instead of letting "Neutral" win, we compare Positive vs Negative directly.
        # We re-normalize the probability to be: Score / (Pos + Neg)
        # This dramatically boosts the confidence score for the dominant sentiment.
        
        total_non_neutral = pos_score + neg_score + 1e-6 # Add epsilon to prevent div by zero
        
        if pos_score > neg_score:
            sentiment = "positive"
            probability = pos_score / total_non_neutral
        else:
            sentiment = "negative"
            probability = neg_score / total_non_neutral

        return probability, sentiment
    else:
        return 0, labels[-1]

if __name__ == "__main__":
    # Test with a neutral-heavy sentence to see if it forces a decision
    tensor, sentiment = estimate_sentiment(['Apple announces earnings call date.', 'Small increase in revenue reported.'])
    print(f"Forced Sentiment: {sentiment}, Probability: {tensor:.4f}")
    print(f"CUDA Available: {torch.cuda.is_available()}")
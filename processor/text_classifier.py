"""
Sentinel Text Classifier

This module provides transformer-based text classification capabilities
for the Sentinel Democracy Watchdog System. It uses pre-trained models
to classify text according to democratic threat categories.
"""

import os
import json
from typing import Dict, Any, List, Optional
from utils.logging_config import setup_logger

# Set up logging
logger = setup_logger(__name__)

class TransformerClassifier:
    """Text classifier using transformer models."""
    
    def __init__(self, model_name: str = "distilbert-base-uncased"):
        """
        Initialize the transformer-based classifier.
        
        Args:
            model_name: Name of the pre-trained transformer model to use
        """
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        self.initialized = False
        
        # Initialize the model on first use to avoid loading unless needed
        
    def _initialize_model(self):
        """Initialize the transformer model and tokenizer."""
        if self.initialized:
            return
            
        try:
            from transformers import AutoModelForSequenceClassification, AutoTokenizer
            
            # Check if we're using a fine-tuned local model
            if os.path.exists(self.model_name):
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
                logger.info(f"Loaded fine-tuned model from {self.model_name}")
            else:
                # Use a pre-trained model from Hugging Face
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
                logger.info(f"Loaded pre-trained model: {self.model_name}")
                
            self.initialized = True
            
        except Exception as e:
            logger.error(f"Error initializing transformer model: {e}")
            self.initialized = False
    
    def classify_text(self, text: str, threshold: float = 0.5) -> Dict[str, float]:
        """
        Classify text using the transformer model.
        
        Args:
            text: Text to classify
            threshold: Confidence threshold for classification
            
        Returns:
            Dictionary of category labels and confidence scores
        """
        # Initialize model if needed
        if not self.initialized:
            self._initialize_model()
            
        if not self.initialized or not text:
            return {}
            
        try:
            import torch
            from torch.nn.functional import softmax
            
            # Truncate text if too long
            max_length = self.tokenizer.model_max_length
            if len(text) > max_length * 4:  # Rough character to token ratio
                text = text[:max_length * 4]
            
            # Tokenize and classify
            inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True)
            with torch.no_grad():
                outputs = self.model(**inputs)
                
            # Get probabilities
            probabilities = softmax(outputs.logits, dim=1)[0].tolist()
            
            # Map to labels
            result = {}
            id2label = self.model.config.id2label
            
            for i, prob in enumerate(probabilities):
                if prob > threshold:
                    label = id2label.get(i, f"LABEL_{i}")
                    result[label] = float(prob)
            
            return result
            
        except Exception as e:
            logger.error(f"Error during text classification: {e}")
            return {}
    
    def classify_chunks(self, text: str, chunk_size: int = 512, overlap: int = 128, threshold: float = 0.5) -> Dict[str, float]:
        """
        Classify long text by breaking it into overlapping chunks.
        
        Args:
            text: Text to classify
            chunk_size: Size of each chunk in characters
            overlap: Overlap between chunks in characters
            threshold: Confidence threshold for classification
            
        Returns:
            Dictionary of category labels and aggregated confidence scores
        """
        if not text:
            return {}
            
        # Break text into chunks
        chunks = []
        for i in range(0, len(text), chunk_size - overlap):
            chunk = text[i:i + chunk_size]
            if len(chunk) > chunk_size / 2:  # Only include substantial chunks
                chunks.append(chunk)
                
        if not chunks:
            return {}
            
        # Classify each chunk
        all_results = {}
        for chunk in chunks:
            chunk_results = self.classify_text(chunk, threshold)
            
            # Aggregate results
            for category, score in chunk_results.items():
                if category in all_results:
                    all_results[category] = max(all_results[category], score)
                else:
                    all_results[category] = score
        
        return all_results
    
    def train_model(self, training_data: List[Dict], output_dir: str = "models/sentinel-classifier", epochs: int = 3):
        """
        Fine-tune the transformer model on democracy threat data.
        
        Args:
            training_data: List of training examples with 'text' and 'labels' fields
            output_dir: Directory to save the fine-tuned model
            epochs: Number of training epochs
        """
        try:
            from transformers import AutoModelForSequenceClassification, AutoTokenizer, Trainer, TrainingArguments
            from transformers import DataCollatorWithPadding
            import torch
            from datasets import Dataset
            
            # Format training data
            texts = [item['text'] for item in training_data]
            label_sets = [item['labels'] for item in training_data]
            
            # Get unique labels
            all_labels = set()
            for label_set in label_sets:
                all_labels.update(label_set)
                
            label_list = sorted(list(all_labels))
            label2id = {label: i for i, label in enumerate(label_list)}
            id2label = {i: label for i, label in enumerate(label_list)}
            
            # Convert labels to multi-hot encoding
            labels = []
            for label_set in label_sets:
                label_vector = [1 if label in label_set else 0 for label in label_list]
                labels.append(label_vector)
            
            # Create dataset
            dataset = Dataset.from_dict({
                'text': texts,
                'labels': labels
            })
            
            # Split dataset
            dataset = dataset.train_test_split(test_size=0.1)
            
            # Load tokenizer
            tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            
            # Tokenize dataset
            def tokenize_function(examples):
                return tokenizer(examples['text'], padding='max_length', truncation=True)
                
            tokenized_dataset = dataset.map(tokenize_function, batched=True)
            
            # Data collator
            data_collator = DataCollatorWithPadding(tokenizer=tokenizer)
            
            # Initialize model for multi-label classification
            model = AutoModelForSequenceClassification.from_pretrained(
                self.model_name,
                problem_type="multi_label_classification",
                num_labels=len(label_list),
                id2label=id2label,
                label2id=label2id
            )
            
            # Training arguments
            training_args = TrainingArguments(
                output_dir=output_dir,
                evaluation_strategy="epoch",
                save_strategy="epoch",
                learning_rate=2e-5,
                per_device_train_batch_size=8,
                per_device_eval_batch_size=8,
                num_train_epochs=epochs,
                weight_decay=0.01,
                load_best_model_at_end=True,
                metric_for_best_model="eval_loss",
                save_total_limit=2
            )
            
            # Initialize trainer
            trainer = Trainer(
                model=model,
                args=training_args,
                train_dataset=tokenized_dataset["train"],
                eval_dataset=tokenized_dataset["test"],
                tokenizer=tokenizer,
                data_collator=data_collator
            )
            
            # Train
            trainer.train()
            
            # Save model
            trainer.save_model(output_dir)
            tokenizer.save_pretrained(output_dir)
            
            # Update our model to use the fine-tuned version
            self.model_name = output_dir
            self.initialized = False  # Force reinitialization with new model
            
            logger.info(f"Model fine-tuned and saved to {output_dir}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error training transformer model: {e}")
            return False
    
    def prepare_training_data_from_alerts(self, alert_dir: str = "alerts") -> List[Dict]:
        """
        Prepare training data from existing alert documents.
        
        Args:
            alert_dir: Directory containing alert JSON files
            
        Returns:
            List of training examples with text and labels
        """
        training_data = []
        
        try:
            import glob
            
            # Find all JSON files in the alerts directory
            json_files = glob.glob(os.path.join(alert_dir, "*.json"))
            
            for file_path in json_files:
                try:
                    with open(file_path, 'r') as f:
                        alert = json.load(f)
                        
                    if 'summary' in alert and 'threat_categories' in alert:
                        text = alert.get('summary', '')
                        
                        # Get top threat categories
                        categories = []
                        for cat in alert.get('threat_categories', []):
                            if isinstance(cat, dict) and 'category' in cat and 'score' in cat:
                                if cat['score'] > 0.6:  # Only include high-confidence categories
                                    categories.append(cat['category'])
                            
                        if text and categories:
                            training_data.append({
                                'text': text,
                                'labels': categories
                            })
                            
                except Exception as e:
                    logger.error(f"Error processing alert file {file_path}: {e}")
            
            logger.info(f"Prepared {len(training_data)} training examples from alerts")
            
        except Exception as e:
            logger.error(f"Error preparing training data: {e}")
            
        return training_data 
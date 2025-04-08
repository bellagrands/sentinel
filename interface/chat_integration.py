# interface/chat_integration.py
"""
Sentinel Chat Integration

This module handles integration with OpenAI's GPT API for enhanced
document summarization, question answering, and contextual analysis.
"""

import os
import json
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from utils.logging_config import setup_logger

# Load environment variables
load_dotenv()

# Set up logging
logger = setup_logger(__name__)

# Set up OpenAI API
openai.api_key = os.getenv("OPENAI_API_KEY")

class ChatIntegration:
    """Integration with OpenAI's GPT API for enhanced document analysis."""
    
    def __init__(self, config_path: str = "config.yml"):
        """Initialize the chat integration with configuration."""
        import yaml
        
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
            
        self.model = self.config.get('openai', {}).get('model', 'gpt-3.5-turbo')
        
    def generate_summary(self, text: str, max_length: int = 150) -> str:
        """
        Generate a concise summary of the text.
        
        Args:
            text: Text to summarize
            max_length: Maximum length of summary in words
            
        Returns:
            Generated summary
        """
        if not text:
            return ""
            
        # Truncate text if extremely long to save tokens
        if len(text) > 8000:
            text = text[:8000] + "..."
            
        try:
            prompt = f"""
            Summarize the following text in a concise manner, focusing on any potential 
            threats to democratic norms, civil rights, or public institutions.
            Keep the summary under {max_length} words.
            
            TEXT:
            {text}
            """
            
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert analyst of government documents, focusing on identifying potential threats to democracy, civil rights, and public institutions."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_length * 2,
                temperature=0.3
            )
            
            summary = response.choices[0].message.content.strip()
            logger.info(f"Generated summary of {len(summary)} chars")
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return text[:max_length * 5] + "..."  # Fallback to simple truncation
    
    def analyze_threat_level(self, document: Dict) -> Dict:
        """
        Analyze the threat level of a document using GPT.
        
        Args:
            document: Document dictionary with text content
            
        Returns:
            Dictionary with threat analysis
        """
        # Extract text content
        text = document.get('text', document.get('content', document.get('body', '')))
        title = document.get('title', 'Untitled Document')
        
        if not text:
            return {
                "threat_score": 0,
                "analysis": "No text content to analyze",
                "recommendations": []
            }
            
        # Truncate text if extremely long
        if len(text) > 8000:
            text = text[:8000] + "..."
            
        try:
            prompt = f"""
            Analyze the following government document for potential threats to democratic norms, 
            civil rights, public education, transparency, or other aspects of an open society.
            
            DOCUMENT TITLE: {title}
            
            DOCUMENT TEXT:
            {text}
            
            Provide your analysis as a valid JSON object with the following fields:
            - threat_score: A numerical score from 0 to 1 representing the overall threat level
            - analysis: A paragraph explaining your assessment
            - categories: An object with category names as keys and threat scores (0-1) as values
            - recommended_actions: A list of recommended actions for civil society organizations
            """
            
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert analyst of government documents with deep expertise in democratic norms, civil rights law, and threats to open society. Provide factual, nuanced analysis without political bias."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )
            
            analysis_text = response.choices[0].message.content.strip()
            
            # Extract JSON from response (sometimes GPT adds explanatory text)
            import re
            json_match = re.search(r'```json\n(.*?)\n```', analysis_text, re.DOTALL)
            if json_match:
                analysis_json = json_match.group(1)
            else:
                analysis_json = analysis_text
                
            try:
                analysis = json.loads(analysis_json)
                logger.info(f"Generated threat analysis with score: {analysis.get('threat_score', 'N/A')}")
                return analysis
            except json.JSONDecodeError:
                logger.error("Failed to parse JSON from GPT response")
                return {
                    "threat_score": 0.5,  # Default to middle score on error
                    "analysis": "Error parsing analysis results",
                    "categories": {},
                    "recommended_actions": []
                }
                
        except Exception as e:
            logger.error(f"Error generating threat analysis: {e}")
            return {
                "threat_score": 0,
                "analysis": f"Error during analysis: {str(e)}",
                "categories": {},
                "recommended_actions": []
            }
    
    def answer_question(self, document: Dict, question: str) -> str:
        """
        Answer a natural language question about the document.
        
        Args:
            document: Document dictionary
            question: Question to answer
            
        Returns:
            Answer to the question
        """
        # Extract text content
        text = document.get('text', document.get('content', document.get('body', '')))
        title = document.get('title', 'Untitled Document')
        
        if not text:
            return "No document content available to answer the question."
            
        # Truncate text if extremely long
        if len(text) > 6000:
            text = text[:6000] + "..."
            
        try:
            prompt = f"""
            Document Title: {title}
            
            Document Content:
            {text}
            
            Question: {question}
            
            Please answer the question directly and precisely based only on the information in the document.
            If the answer cannot be determined from the document, say so clearly.
            """
            
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a precision-focused research assistant that provides factual answers based strictly on the provided document."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )
            
            answer = response.choices[0].message.content.strip()
            logger.info(f"Generated answer of {len(answer)} chars")
            return answer
            
        except Exception as e:
            logger.error(f"Error answering question: {e}")
            return f"Error generating answer: {str(e)}"

def main():
    """Main function to demonstrate chat integration."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test OpenAI API integration for document analysis.')
    parser.add_argument('--document', required=True, help='Path to document JSON file')
    parser.add_argument('--summary', action='store_true', help='Generate summary')
    parser.add_argument('--analysis', action='store_true', help='Generate threat analysis')
    parser.add_argument('--question', help='Question to answer about the document')
    args = parser.parse_args()
    
    # Load document
    with open(args.document, 'r') as f:
        document = json.load(f)
    
    chat = ChatIntegration()
    
    # Generate summary if requested
    if args.summary:
        summary = chat.generate_summary(chat.extract_text_field(document))
        print("SUMMARY:")
        print(summary)
        print()
    
    # Generate analysis if requested
    if args.analysis:
        analysis = chat.analyze_threat_level(document)
        print("ANALYSIS:")
        print(json.dumps(analysis, indent=2))
        print()
    
    # Answer question if provided
    if args.question:
        answer = chat.answer_question(document, args.question)
        print(f"QUESTION: {args.question}")
        print("ANSWER:")
        print(answer)


if __name__ == "__main__":
    main()
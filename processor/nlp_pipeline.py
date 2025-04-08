"""
Sentinel NLP Pipeline

This module handles natural language processing of collected documents
to analyze, categorize, and flag potential threats to democracy, civil rights,
and other areas of concern.

Usage:
    python -m processor.nlp_pipeline
"""

import os
import json
import logging
import glob
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any, Set
import re
import sys
import time
import traceback
import spacy
from spacy.tokens import Doc, Span
from spacy.matcher import PhraseMatcher, Matcher
from spacy.language import Language
from utils.logging_config import setup_logger

# Set up logging
logger = setup_logger(__name__)

# Add file handler only if running outside container or if directory is writable
log_handlers = []
try:
    # Check if we're running in a container
    running_in_container = os.environ.get('RUNNING_IN_CONTAINER', 'false').lower() == 'true'
    
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)
    
    # Try to create a test file to check write permissions
    test_file_path = os.path.join('logs', 'permission_test.txt')
    try:
        with open(test_file_path, 'w') as f:
            f.write('test')
        os.remove(test_file_path)
        
        # If we can write to the directory, add the file handler
        log_file = os.path.join('logs', f"nlp_pipeline_{datetime.now().strftime('%Y%m%d')}.log")
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(file_handler)
        log_handlers.append(file_handler)
        logger.info(f"Logging to file: {log_file}")
    except (IOError, PermissionError) as e:
        logger.warning(f"Unable to write to logs directory: {e}. Logging to console only.")
except Exception as e:
    logger.warning(f"Error setting up file logging: {e}. Logging to console only.")

# Attempt to load spaCy - install if not available
try:
    try:
        nlp = spacy.load("en_core_web_md")
        logger.info("Loaded spaCy model: en_core_web_md")
    except OSError:
        logger.warning("Could not find spaCy model. Downloading en_core_web_md...")
        spacy.cli.download("en_core_web_md")
        nlp = spacy.load("en_core_web_md")
        
    # Custom entity patterns for government agencies and legal terms
    GOV_AGENCIES = [
        "Department of Justice", "DOJ", "FBI", "Department of Homeland Security", "DHS", 
        "ICE", "Department of Defense", "DOD", "Department of State", "Department of the Interior",
        "Department of Education", "Department of Energy", "Department of Health and Human Services",
        "HHS", "Federal Election Commission", "FEC", "Federal Communications Commission", "FCC",
        "Environmental Protection Agency", "EPA", "Federal Trade Commission", "FTC",
        "Securities and Exchange Commission", "SEC", "Internal Revenue Service", "IRS",
        "Department of Treasury", "Federal Reserve", "Customs and Border Protection", "CBP"
    ]
    
    LEGAL_TERMS = [
        "U.S. Code", "USC", "Title", "Section", "Public Law", "U.S.C.", 
        "Code of Federal Regulations", "CFR", "Federal Register", "Fed. Reg.",
        "Executive Order", "Presidential Memorandum", "Proclamation", "Rule", "Regulation",
        "Bill", "Act", "Amendment", "Constitution", "Constitutional", "Statute", "Statutory",
        "Federal Rules", "Administrative Procedure Act", "Freedom of Information Act", "FOIA"
    ]
    
    # Add custom entity recognition component
    @Language.component("gov_law_entities")
    def gov_law_entities(doc):
        # Add government agency entities
        gov_matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
        
        # Process patterns one by one to avoid recursion issues
        gov_patterns = []
        for text in GOV_AGENCIES:
            try:
                pattern_doc = nlp.make_doc(text)  # Use make_doc instead of nlp() to avoid recursion
                gov_patterns.append(pattern_doc)
            except Exception as e:
                logger.warning(f"Error creating pattern for '{text}': {e}")
        
        gov_matcher.add("GOV_AGENCY", gov_patterns)
        
        # Add legal terminology entities
        law_matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
        
        # Process patterns one by one
        law_patterns = []
        for text in LEGAL_TERMS:
            try:
                pattern_doc = nlp.make_doc(text)  # Use make_doc instead of nlp()
                law_patterns.append(pattern_doc)
            except Exception as e:
                logger.warning(f"Error creating pattern for '{text}': {e}")
                
        law_matcher.add("LAW_TERM", law_patterns)
        
        # Additional law pattern for U.S. Code citations like "5 U.S.C. § 552" or "42 U.S.C. 2000d"
        citation_matcher = Matcher(nlp.vocab)
        citation_matcher.add(
            "USC_CITATION", 
            [[{"IS_DIGIT": True}, {"LOWER": {"IN": ["u.s.c.", "usc", "u.s.c"]}}, 
              {"LOWER": {"IN": ["§", "sec.", "section"]}, "OP": "?"}, {"IS_DIGIT": True, "OP": "?"}]]
        )
        
        # Find matches and add entities
        spans = []
        
        try:
            matches = gov_matcher(doc)
            for match_id, start, end in matches:
                spans.append(Span(doc, start, end, label="GOV_AGENCY"))
        except Exception as e:
            logger.warning(f"Error in government agency matching: {e}")
            
        try:    
            law_matches = law_matcher(doc)
            for match_id, start, end in law_matches:
                spans.append(Span(doc, start, end, label="LAW_TERM"))
        except Exception as e:
            logger.warning(f"Error in legal term matching: {e}")
            
        try:
            citation_matches = citation_matcher(doc)
            for match_id, start, end in citation_matches:
                spans.append(Span(doc, start, end, label="USC_CITATION"))
        except Exception as e:
            logger.warning(f"Error in citation matching: {e}")
            
        # Only add non-overlapping spans
        try:
            filtered_spans = spacy.util.filter_spans(spans)
            if filtered_spans:
                doc.ents = list(doc.ents) + filtered_spans
        except Exception as e:
            logger.warning(f"Error filtering spans: {e}")
            
        return doc
    
    # Add the component to the pipeline if spaCy is available
    if "gov_law_entities" not in nlp.pipe_names:
        nlp.add_pipe("gov_law_entities", after="ner")
        logger.info("Added custom government and legal entity recognition component")
        
except ImportError:
    logger.error("spaCy is not installed. Install it with: pip install spacy")
    nlp = None

# Add necessary import for memory optimization
from processor.memory_optimization import memory_tracker, limit_text_length, batch_process, should_use_transformer

class SentinelNLP:
    """NLP processing pipeline for Sentinel documents."""
    
    def __init__(self):
        """Initialize the NLP pipeline."""
        self.threat_categories = {
            "voting_rights": [
                "voter suppression", "voter id", "voter purge", "registration restriction",
                "polling location", "early voting", "mail-in ballot", "absentee ballot",
                "ballot access", "voter disenfranchisement", "electoral college"
            ],
            "civil_liberties": [
                "free speech", "freedom of assembly", "privacy rights", "surveillance",
                "due process", "search and seizure", "first amendment", "fourth amendment",
                "fifth amendment", "fourteenth amendment", "civil liberties", "racial profiling"
            ],
            "edu_rights": [
                "book ban", "curriculum restriction", "education funding", "school privatization",
                "student rights", "public education", "education access", "school voucher",
                "academic freedom", "segregation", "education equity", "library access"
            ],
            "executive_power": [
                "executive order", "emergency power", "war power", "regulatory authority",
                "agency discretion", "presidential directive", "executive privilege", 
                "executive branch", "separation of powers", "checks and balances",
                "unitary executive", "signing statement"
            ],
            "transparency": [
                "freedom of information", "government transparency", "open records", 
                "public disclosure", "whistleblower", "classified information",
                "state secrets", "sunshine law", "open meeting", "records retention",
                "media access", "press freedom"
            ],
            "immigration": [
                "detention", "deportation", "asylum", "refugee", "border enforcement",
                "immigration enforcement", "sanctuary", "birthright citizenship",
                "family separation", "migrant rights", "immigration court", "visa restriction"
            ],
            # Adding new category specifically for anti-democratic content
            "anti_democratic": [
                "restrict voting", "gerrymandering", "purge voter", "voter id requirement", 
                "polling place closure", "election interference", "electoral integrity", 
                "ballot harvesting", "cancel election", "postpone election", "delay election",
                "election certification", "electoral certification", "election challenge",
                "overturn election", "emergency powers", "presidential immunity", 
                "executive privilege", "martial law", "insurrection act", "suspend constitution", 
                "constitutional convention", "term limits repeal", "impeachment restriction",
                "judicial independence", "court packing", "court reform", "media censorship",
                "freedom of press", "press credentials", "press access", "legislative override",
                "state legislature", "independent commission", "election commission",
                "federal overreach", "states rights", "legislative immunity"
            ]
        }
        
        # Precompute embeddings for threat categories if spaCy is available
        self.category_embeddings = {}
        if nlp:
            for category, terms in self.threat_categories.items():
                category_text = " ".join(terms)
                self.category_embeddings[category] = nlp(category_text).vector
        
        # Anti-democratic patterns dictionary
        self.anti_democratic_patterns = [
            r'restrict(?:ing|s|ed)?\s+(?:voting|ballot|election)',
            r'remov(?:e|ing|ed)\s+(?:voters?|names)\s+(?:from|off)\s+(?:rolls?|registration)',
            r'(?:close|reduce|limit|restrict)\s+polling\s+(?:stations?|places?|locations?)',
            r'voter\s+identification',
            r'strict(?:er)?\s+voter\s+id',
            r'delay(?:ing|ed)?\s+(?:the\s+)?election',
            r'postpon(?:e|ing|ed)\s+(?:the\s+)?election',
            r'cancel(?:ing|ed|lation of)?\s+(?:the\s+)?election',
            r'(?:reject|challeng(?:e|ing)|contest(?:ing|ed)?|invalidat(?:e|ing|ed)?)\s+(?:election|electoral)\s+results',
            r'(?:refus(?:e|ing|al)|declin(?:e|ing)|reject(?:ing|ed)?)\s+to\s+certify',
            r'expand(?:ing|ed)?\s+(?:presidential|executive)\s+powers',
            r'emergency\s+powers',
            r'(?:invok(?:e|ing)|implement(?:ing|ed)?)\s+(?:the\s+)?martial\s+law',
            r'suspend(?:ing|ed)?\s+(?:the\s+)?constitution',
            r'limit(?:ing|ed|s)?\s+(?:judicial|court)\s+review',
            r'pack(?:ing)?\s+(?:the\s+)?(?:court|supreme court)',
            r'restrict(?:ing|s|ed)?\s+(?:press|media|journalist)\s+access',
            r'(?:censor(?:ing|ed|ship)?|restrict(?:ing|s|ed)?)\s+(?:the\s+)?(?:press|media|news)',
            r'(?:classify|seal|restrict)\s+(?:government|public)\s+(?:documents|records|information)',
            r'(?:bypass(?:ing|ed)?|circumvent(?:ing|ed)?)\s+(?:legislative|congressional)\s+(?:approval|process|oversight)',
            r'limit(?:ing|s|ed)?\s+(?:legislative|congressional)\s+oversight',
            r'override\s+(?:legislative|congressional)\s+(?:authority|power)'
        ]
        
        # Initialize transformer classifier (lazy loading)
        try:
            from processor.text_classifier import TransformerClassifier
            self.transformer_classifier = TransformerClassifier()
            self.has_transformer = True
            logger.info("Transformer classifier initialized")
        except ImportError:
            logger.warning("Transformer-based classifier not available - install 'transformers' package for enhanced classification")
            self.has_transformer = False
        except Exception as e:
            logger.error(f"Error initializing transformer classifier: {e}")
            self.has_transformer = False
    
    def load_documents(self, data_dirs: List[str]) -> List[Dict]:
        """
        Load documents from specified directories.
        
        Args:
            data_dirs: List of directory paths to load documents from
            
        Returns:
            List of document dictionaries
        """
        documents = []
        
        for data_dir in data_dirs:
            if not os.path.exists(data_dir):
                logger.warning(f"Directory does not exist: {data_dir}")
                continue
                
            # Load JSON files
            json_files = glob.glob(os.path.join(data_dir, "*.json"))
            for file_path in json_files:
                try:
                    with open(file_path, 'r') as f:
                        doc = json.load(f)
                        
                        # Handle both single documents and arrays
                        if isinstance(doc, list):
                            # This is a file with multiple documents (like all_bills_*.json)
                            for item in doc:
                                item['source_file'] = file_path
                                item['source_type'] = os.path.basename(data_dir)
                                documents.append(item)
                        else:
                            # Single document
                            doc['source_file'] = file_path
                            doc['source_type'] = os.path.basename(data_dir)
                            documents.append(doc)
                except Exception as e:
                    logger.error(f"Error loading {file_path}: {e}")
        
        logger.info(f"Loaded {len(documents)} documents from {len(data_dirs)} directories")
        return documents
    
    def extract_text_field(self, document: Dict) -> str:
        """
        Extract the main text content from a document based on source type.
        
        Args:
            document: Document dictionary
            
        Returns:
            Extracted text content
        """
        source_type = document.get('source_type', '')
        
        # Federal Register documents
        if source_type == 'federal_register':
            text_parts = []
            
            # Title
            if 'title' in document:
                text_parts.append(document['title'])
                
            # Abstract
            if 'abstract' in document:
                text_parts.append(document['abstract'])
                
            # HTML content - using body or raw_text_url would require another fetch
            
            return ' '.join(text_parts)
        
        # Congress documents
        elif source_type == 'congress':
            text_parts = []
            
            # Title
            if 'title' in document:
                text_parts.append(document['title'])
                
            # Latest action
            if 'latest_action' in document:
                text_parts.append(document['latest_action'])
                
            # Search term that matched it
            if 'search_term' in document:
                text_parts.append(f"This document matched the search term: {document['search_term']}")
                
            return ' '.join(text_parts)
        
        # Default case: try common field names
        for field in ['text', 'content', 'body', 'description', 'summary']:
            if field in document and document[field]:
                return document[field]
        
        # Concatenate all string fields as a last resort
        text_parts = []
        for key, value in document.items():
            if isinstance(value, str) and len(value) > 20:  # Only include substantial text fields
                text_parts.append(value)
        
        return ' '.join(text_parts)
    
    def preprocess_text(self, text: str) -> str:
        """
        Preprocess text for analysis.
        
        Args:
            text: Raw text string
            
        Returns:
            Preprocessed text
        """
        if not text or not isinstance(text, str):
            return ""
            
        # Convert to lowercase
        text = text.lower()
        
        # Remove URLs
        text = re.sub(r'https?://\S+|www\.\S+', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract named entities from text.
        
        Args:
            text: Text to extract entities from
            
        Returns:
            Dictionary of entity types and values
        """
        if not text or not nlp:
            return {}
            
        doc = nlp(text[:100000])  # Limit text length for performance
        
        entities = {
            "PERSON": [],
            "ORG": [],
            "GPE": [],  # Countries, cities, states
            "LAW_TERM": [],  # Legal terminology
            "USC_CITATION": [],  # U.S. Code citations
            "GOV_AGENCY": [],  # Government agencies
            "LAW": [],
            "DATE": [],
            "NORP": [],  # Nationalities, religious or political groups
            "EVENT": []  # Events (protests, hearings, etc.)
        }
        
        # Process recognized entities
        for ent in doc.ents:
            if ent.label_ in entities:
                # Deduplicate entities
                if ent.text.lower() not in [e.lower() for e in entities[ent.label_]]:
                    entities[ent.label_].append(ent.text)
        
        # Add regex-based entity detection for additional patterns
        
        # Detect bill numbers (e.g., "H.R. 1234", "S. 567")
        bill_pattern = re.compile(r'\b(H\.R\.|HR|S\.|H\. Con\. Res\.|S\. Con\. Res\.|H\. Res\.|S\. Res\.|H\. J\. Res\.|S\. J\. Res\.)\s*(\d+)\b')
        bill_matches = bill_pattern.findall(text)
        
        if "BILL" not in entities:
            entities["BILL"] = []
            
        for bill_type, bill_num in bill_matches:
            bill_id = f"{bill_type} {bill_num}".strip()
            if bill_id.lower() not in [b.lower() for b in entities["BILL"]]:
                entities["BILL"].append(bill_id)
        
        # Detect Federal Register citations
        fr_pattern = re.compile(r'\b(\d+)\s*Fed\.\s*Reg\.\s*(\d+)\b')
        fr_matches = fr_pattern.findall(text)
        
        if "FR_CITATION" not in entities:
            entities["FR_CITATION"] = []
            
        for vol, page in fr_matches:
            fr_citation = f"{vol} Fed. Reg. {page}"
            if fr_citation not in entities["FR_CITATION"]:
                entities["FR_CITATION"].append(fr_citation)
        
        return entities
    
    def analyze_threat_categories(self, text: str) -> Dict[str, float]:
        """
        Analyze text for threat categories.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary of threat categories and confidence scores
        """
        if not text or not nlp:
            return {}
            
        # Create document embedding
        doc_vector = nlp(text).vector
        
        # Calculate similarity to each category
        similarities = {}
        for category, embedding in self.category_embeddings.items():
            # Cosine similarity
            similarity = np.dot(doc_vector, embedding) / (np.linalg.norm(doc_vector) * np.linalg.norm(embedding))
            similarities[category] = float(similarity)
        
        # Normalize scores to 0-1 range
        min_sim = min(similarities.values())
        max_sim = max(similarities.values())
        
        if max_sim > min_sim:
            normalized = {
                category: (score - min_sim) / (max_sim - min_sim)
                for category, score in similarities.items()
            }
        else:
            normalized = similarities
        
        return normalized
    
    def keyword_based_scoring(self, text: str) -> Dict[str, float]:
        """
        Alternative threat category scoring using keyword matching.
        This is used as a fallback when spaCy is not available.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary of threat categories and scores
        """
        if not text:
            return {}
            
        text = self.preprocess_text(text)
        scores = {}
        
        for category, keywords in self.threat_categories.items():
            count = 0
            for keyword in keywords:
                count += text.count(keyword.lower())
            
            # Normalize by number of keywords
            scores[category] = min(1.0, count / len(keywords))
        
        return scores
    
    def generate_summary(self, text: str, max_length: int = 150) -> str:
        """
        Generate a more sophisticated summary of text.
        Uses key sentence extraction based on entity density and keyword relevance.
        
        Args:
            text: Text to summarize
            max_length: Maximum length of summary in characters
            
        Returns:
            Generated summary
        """
        if not text:
            return ""
            
        # If spaCy is available, use it for better summarization
        if nlp:
            # Process the text
            doc = nlp(text[:50000])  # Limit for performance
            
            # Split into sentences
            sentences = list(doc.sents)
            
            if not sentences:
                return text[:max_length] + "..." if len(text) > max_length else text
                
            # Score sentences based on several factors
            sentence_scores = {}
            
            for i, sentence in enumerate(sentences):
                # Don't consider very short sentences
                if len(sentence.text.split()) < 5:
                    continue
                
                score = 0
                
                # More weight to earlier sentences (especially first 3)
                if i < 3:
                    score += (3 - i) * 0.2
                
                # Count entities (more entities = more informative)
                entities = [ent for ent in sentence.ents]
                score += len(entities) * 0.1
                
                # Check for threat category keywords
                for category, terms in self.threat_categories.items():
                    for term in terms:
                        if term.lower() in sentence.text.lower():
                            score += 0.15
                            break
                
                # Check for anti-democratic patterns
                for pattern in self.anti_democratic_patterns:
                    if re.search(pattern, sentence.text, re.IGNORECASE):
                        score += 0.2
                        break
                
                sentence_scores[sentence] = score
            
            # Get top scoring sentences (up to 3)
            top_sentences = sorted(sentence_scores.items(), key=lambda x: x[1], reverse=True)[:3]
            
            # Sort sentences by their original order
            top_sentences = sorted(top_sentences, key=lambda x: list(sentences).index(x[0]))
            
            # Combine sentences
            summary = " ".join([s[0].text for s in top_sentences])
            
            # Truncate if too long
            if len(summary) > max_length:
                summary = summary[:max_length] + "..."
                
            return summary
        else:
            # Fallback to simple extractive summarization
            sentences = text.split('.')
            summary = '.'.join(sentences[:3]) + '.'
            
            if len(summary) > max_length:
                summary = summary[:max_length] + "..."
                
            return summary
    
    def calculate_threat_score(self, category_scores: Dict[str, float]) -> float:
        """
        Calculate an overall threat score from category scores.
        
        Args:
            category_scores: Dictionary of category scores
            
        Returns:
            Overall threat score
        """
        if not category_scores:
            return 0.0
            
        # Average of the top 3 category scores
        top_scores = sorted(category_scores.values(), reverse=True)[:3]
        return sum(top_scores) / len(top_scores) if top_scores else 0.0
    
    def analyze_document(self, document: Dict) -> Dict:
        """
        Analyze a document for threats.
        
        Args:
            document: Document dictionary
            
        Returns:
            Document with added analysis
        """
        # Extract and preprocess text
        text = self.extract_text_field(document)
        text = self.preprocess_text(text)
        
        # Skip empty documents
        if not text:
            logger.warning(f"No text found in document: {document.get('source_file', 'unknown')}")
            return document
        
        # Add text to document
        document['processed_text'] = text
        
        # Extract entities
        document['entities'] = self.extract_entities(text)
        
        # Analyze threat categories using embeddings
        if nlp:
            document['threat_categories'] = self.analyze_threat_categories(text)
        else:
            document['threat_categories'] = self.keyword_based_scoring(text)
            
        # Use transformer-based classification if available
        if self.has_transformer:
            try:
                # Classify with transformer model
                transformer_results = self.transformer_classifier.classify_chunks(text, threshold=0.4)
                document['transformer_classifications'] = transformer_results
                
                # If we have transformer results, combine with traditional method
                if transformer_results:
                    # Convert to common format and merge with embedding-based scores
                    for category, score in transformer_results.items():
                        category_key = category.lower().replace(" ", "_")
                        if category_key in document['threat_categories']:
                            # Average the scores if category exists in both
                            document['threat_categories'][category_key] = (
                                document['threat_categories'][category_key] + score
                            ) / 2
                        else:
                            # Add new categories from transformer
                            document['threat_categories'][category_key] = score
            except Exception as e:
                logger.error(f"Error in transformer classification: {e}")
            
        # Detect anti-democratic patterns
        document['anti_democratic_matches'] = self.detect_anti_democratic_patterns(text)
        
        # Calculate anti-democratic score (average of matched pattern scores)
        anti_democratic_scores = list(document['anti_democratic_matches'].values())
        if anti_democratic_scores:
            document['anti_democratic_score'] = sum(anti_democratic_scores) / len(anti_democratic_scores)
        else:
            document['anti_democratic_score'] = 0.0
            
        # Extract entity relationships that may pose threats
        document['entity_relationships'] = self.detect_entity_relationship_threats(text, document['entities'])
        
        # Add relationship threat score (max of relationship threat scores)
        relationship_scores = [rel.get('threat_score', 0) for rel in document.get('entity_relationships', [])]
        document['relationship_threat_score'] = max(relationship_scores) if relationship_scores else 0.0
        
        # Calculate overall threat score - weighted average of different scores
        category_threat_score = self.calculate_threat_score(document['threat_categories'])
        
        # Weighted combination of different threat measures
        document['threat_score'] = (
            0.4 * category_threat_score +
            0.4 * document['anti_democratic_score'] +
            0.2 * document['relationship_threat_score']
        )
        
        # Generate summary
        document['summary'] = self.generate_summary(text)
        
        # Add timestamp
        document['analysis_timestamp'] = datetime.now().isoformat()
        
        return document
    
    def process_documents(self, documents: List[Dict], output_dir: str = "data/analyzed", batch_size: int = 10, use_transformers: bool = True) -> List[Dict]:
        """
        Process multiple documents using batch processing to optimize memory usage.
        
        Args:
            documents: List of documents to process
            output_dir: Directory to save processed documents
            batch_size: Size of batches for processing
            use_transformers: Whether to use transformer models for classification
            
        Returns:
            List of processed documents
        """
        self.logger.info(f"Processing {len(documents)} documents in batches of {batch_size}")
        
        # Define batch processing function
        def process_batch(batch):
            results = []
            for doc in batch:
                # For each document, first do a basic analysis
                basic_result = self.analyze_document_basic(doc)
                
                # Determine if we should use the transformer based on initial results
                if use_transformers and should_use_transformer(
                    doc, 
                    initial_nlp_score=basic_result.get('threat_score', 0)
                ):
                    # Use full analysis with transformers
                    result = self.analyze_document(doc)
                else:
                    # Use basic result to save memory/time
                    result = basic_result
                
                results.append(result)
                
                # Save to output directory if specified
                if output_dir:
                    self._save_document(result, output_dir)
                
            return results
        
        # Use batch processing
        processed_docs = batch_process(
            documents,
            process_batch,
            batch_size=batch_size
        )
        
        self.logger.info(f"Completed processing {len(processed_docs)} documents")
        return processed_docs
    
    def analyze_document_basic(self, document):
        """
        Perform basic analysis of a document without using transformer models.
        
        This method is faster and uses less memory than the full analyze_document method.
        It can be used for initial screening before deciding to use the more resource-intensive
        full analysis.
        
        Args:
            document: Document to analyze
            
        Returns:
            Dictionary with analysis results
        """
        self.logger.info(f"Performing basic analysis of document: {document.get('title', 'Untitled')}")
        
        # Extract content and limit length to prevent memory issues
        content = document.get('content', '')
        content = limit_text_length(content, self.max_text_length)
        
        # Create document ID if not present
        if 'document_id' not in document:
            document['document_id'] = self._generate_document_id(document)
        
        # Process with spaCy without custom components
        # This avoids the heavier transformer-based components
        basic_doc = self.nlp.make_doc(content)
        
        # Extract basic entities using only the tokenizer and basic NER
        entities = {}
        for ent in basic_doc.ents:
            if ent.label_ not in entities:
                entities[ent.label_] = []
            entities[ent.label_].append({
                'text': ent.text,
                'start': ent.start_char,
                'end': ent.end_char
            })
        
        # Match patterns without transformer classification
        anti_democratic_matches = {}
        for name, matcher in self.matchers.items():
            matches = matcher(basic_doc)
            if matches:
                # Assign a simpler score based on match count
                score = min(1.0, len(matches) / 10)  # Cap at 1.0
                anti_democratic_matches[name] = score
        
        # Calculate a basic threat score
        threat_score = 0.0
        if anti_democratic_matches:
            threat_score = sum(anti_democratic_matches.values()) / len(anti_democratic_matches)
        
        # Determine threat categories based on patterns
        threat_categories = self._determine_threat_categories(anti_democratic_matches)
        
        # Create simplified result
        result = {
            'document_id': document['document_id'],
            'title': document.get('title', 'Untitled'),
            'content': content,
            'entities': entities,
            'anti_democratic_matches': anti_democratic_matches,
            'threat_categories': threat_categories,
            'threat_score': threat_score,
            'analysis_level': 'basic'  # Flag that this is basic analysis
        }
        
        self.logger.info(f"Basic analysis complete. Threat score: {threat_score:.2f}")
        return result
    
    def detect_anti_democratic_patterns(self, text: str) -> Dict[str, float]:
        """
        Detects anti-democratic patterns in text using regex patterns and assigns threat scores.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with matched patterns and their threat scores
        """
        if not text:
            return {}
            
        text = self.preprocess_text(text)
        matches = {}
        
        for pattern in self.anti_democratic_patterns:
            pattern_matches = re.findall(pattern, text, re.IGNORECASE)
            if pattern_matches:
                # Use the pattern as key and the highest score if multiple matches
                key = pattern.replace(r'\s+', ' ').replace(r'(?:', '').replace(')?', '').replace('|', '/')
                matches[key] = 0.9
        
        return matches
        
    def detect_entity_relationship_threats(self, text: str, entities: Dict[str, List[str]]) -> List[Dict]:
        """
        Detect relationships between entities that may indicate democratic threats.
        
        Args:
            text: Text to analyze
            entities: Dictionary of extracted entities
            
        Returns:
            List of detected entity relationships that may pose threats
        """
        if not text or not nlp or not entities:
            return []
            
        # Convert text to spaCy doc
        doc = nlp(text[:100000])  # Limit text for performance
        
        # Define threat patterns involving entity relationships
        threat_relationships = []
        
        # Check for government agencies affecting voting rights
        gov_agencies = set(entities.get("GOV_AGENCY", []))
        laws = set(entities.get("LAW_TERM", []) + entities.get("LAW", []) + entities.get("USC_CITATION", []))
        
        # Voting rights restrictions by agencies
        voting_keywords = ["vote", "voting", "ballot", "election", "poll", "polling", "voter", "registration"]
        voting_verbs = ["restrict", "limit", "reduce", "eliminate", "curtail", "constrain", "obstruct", "impede", "block"]
        
        # Look for sentences with both agency and voting terms
        for sent in doc.sents:
            sent_text = sent.text.lower()
            
            # Find agencies in this sentence
            agencies_in_sent = []
            for agency in gov_agencies:
                if agency.lower() in sent_text:
                    agencies_in_sent.append(agency)
                    
            if not agencies_in_sent:
                continue
                
            # Check if this is about voting and restrictions
            has_voting_keyword = any(keyword in sent_text for keyword in voting_keywords)
            has_restriction_verb = any(verb in sent_text for verb in voting_verbs)
            
            if has_voting_keyword and has_restriction_verb:
                for agency in agencies_in_sent:
                    threat_relationships.append({
                        "type": "agency_voting_restriction",
                        "agency": agency,
                        "sentence": sent.text,
                        "threat_score": 0.8
                    })
        
        # Check for laws affecting civil liberties
        civil_liberty_keywords = ["speech", "assembly", "protest", "privacy", "press", "religion", 
                                 "search", "seizure", "due process", "rights"]
                                 
        for sent in doc.sents:
            sent_text = sent.text.lower()
            
            # Find laws in this sentence
            laws_in_sent = []
            for law in laws:
                if law.lower() in sent_text:
                    laws_in_sent.append(law)
                    
            if not laws_in_sent:
                continue
                
            # Check if this is about civil liberties
            has_civil_liberty_keyword = any(keyword in sent_text for keyword in civil_liberty_keywords)
            has_restriction_verb = any(verb in sent_text for verb in voting_verbs)
            
            if has_civil_liberty_keyword and has_restriction_verb:
                for law in laws_in_sent:
                    threat_relationships.append({
                        "type": "law_civil_liberty_restriction",
                        "law": law,
                        "sentence": sent.text,
                        "threat_score": 0.75
                    })
                    
        return threat_relationships
    
    def train_transformer_classifier(self, alert_dir: str = "alerts", output_dir: str = "models/sentinel-classifier", epochs: int = 3) -> bool:
        """
        Train the transformer classifier with existing alert data.
        
        Args:
            alert_dir: Directory containing alert JSON files
            output_dir: Directory to save the fine-tuned model
            epochs: Number of training epochs
            
        Returns:
            Success flag
        """
        if not self.has_transformer:
            logger.error("Transformer classifier not available")
            return False
            
        try:
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Prepare training data from existing alerts
            training_data = self.transformer_classifier.prepare_training_data_from_alerts(alert_dir)
            
            if not training_data:
                logger.warning("No training data found in alerts directory")
                return False
                
            # Train the model
            result = self.transformer_classifier.train_model(
                training_data=training_data,
                output_dir=output_dir,
                epochs=epochs
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error training transformer classifier: {e}")
            return False


def main():
    """Command-line interface for NLP pipeline."""
    import argparse
    parser = argparse.ArgumentParser(description='Process documents with NLP')
    parser.add_argument('--input-dirs', nargs='+', default=['data/federal_register', 'data/congress'], 
                        help='Input directories containing documents')
    parser.add_argument('--output-dir', default='data/analyzed', help='Output directory for processed documents')
    parser.add_argument('--train-classifier', action='store_true', 
                        help='Train the transformer classifier with existing alerts')
    parser.add_argument('--classifier-output', default='models/sentinel-classifier',
                        help='Output directory for trained classifier model')
    parser.add_argument('--train-epochs', type=int, default=3,
                        help='Number of epochs for classifier training')
    
    args = parser.parse_args()
    
    processor = SentinelNLP()
    
    # Train transformer classifier if requested
    if args.train_classifier:
        print("Training transformer classifier...")
        success = processor.train_transformer_classifier(
            alert_dir="alerts",
            output_dir=args.classifier_output,
            epochs=args.train_epochs
        )
        if success:
            print(f"Transformer classifier trained successfully and saved to {args.classifier_output}")
        else:
            print("Failed to train transformer classifier")
        return
    
    # Load documents
    documents = processor.load_documents(args.input_dirs)
    
    # Process documents
    processed = processor.process_documents(documents, args.output_dir)
    
    print(f"Processed {len(processed)} documents")
    
    # Print threat information for high-threat documents
    high_threat = [doc for doc in processed if doc.get('threat_score', 0) > 0.6]
    if high_threat:
        print(f"\nFound {len(high_threat)} high-threat documents:")
        for doc in high_threat:
            print(f"- {doc.get('title', 'Untitled')} (Score: {doc.get('threat_score', 0):.2f})")
            top_categories = sorted(
                doc.get('threat_categories', {}).items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]
            print(f"  Top categories: {', '.join(f'{cat} ({score:.2f})' for cat, score in top_categories)}")
    else:
        print("No high-threat documents found")


if __name__ == "__main__":
    main()
"""
Sentinel Rules Engine

This module defines and applies rules for determining which documents
need alerts and which don't, based on content analysis and threat scores.
"""

import logging
import json
import os
import yaml
import smtplib
import requests
import socket
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/rules_engine.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AlertEngine:
    """Engine for processing analyzed documents and triggering alerts."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the alert engine with configuration."""
        self.config = {}
        
        # Default configuration if no file exists
        if not os.path.exists(config_path):
            self.config = {
                "nlp": {
                    "threat_threshold": 0.65,
                    "similarity_threshold": 0.75,
                },
                "alerts": {
                    "email_enabled": False,
                    "email_recipients": [],
                    "slack_enabled": False,
                    "slack_webhook": ""
                }
            }
        else:
            # Load configuration
            try:
                with open(config_path, 'r') as f:
                    self.config = yaml.safe_load(f)
            except Exception as e:
                logger.error(f"Error loading configuration: {e}")
                self.config = {
                    "nlp": {"threat_threshold": 0.65},
                    "alerts": {"email_enabled": False, "slack_enabled": False}
                }
            
        self.alert_dir = "alerts"
        os.makedirs(self.alert_dir, exist_ok=True)
        
    def evaluate_document(self, doc: Dict) -> bool:
        """
        Evaluate a document against rules to determine if it needs an alert.
        
        Args:
            doc: Document dictionary with analysis results
            
        Returns:
            Boolean indicating if alert should be triggered
        """
        # Default threshold if not specified in config
        threshold = self.config.get('nlp', {}).get('threat_threshold', 0.65)
        
        # Check if document meets threat threshold
        if doc.get('threat_score', 0) >= threshold:
            logger.info(f"Document meets overall threat threshold: {doc.get('threat_score', 0):.2f} >= {threshold}")
            return True
            
        # Check if document has high scores in specific threat categories
        for category, score in doc.get('threat_categories', {}).items():
            higher_threshold = threshold * 1.2  # Higher threshold for individual categories
            if score >= higher_threshold:
                logger.info(f"Document has high score in {category}: {score:.2f} >= {higher_threshold}")
                return True
                
        # Check for key entities of concern
        entities = doc.get('entities', {})
        agency_keywords = ["ICE", "DHS", "DOJ", "FBI", "Election", "Commission"]
        
        for org in entities.get('ORG', []):
            for keyword in agency_keywords:
                if keyword.lower() in org.lower():
                    logger.info(f"Document contains sensitive organization: {org}")
                    return True
        
        # Check for key law references
        for law in entities.get('LAW', []):
            if any(term.lower() in law.lower() for term in ["amendment", "act", "rights", "regulation"]):
                logger.info(f"Document contains sensitive law reference: {law}")
                return True
                    
        # Document doesn't meet alert criteria
        return False
        
    def generate_alert(self, doc: Dict) -> Dict:
        """
        Generate an alert object for a document.
        
        Args:
            doc: Document dictionary with analysis results
            
        Returns:
            Alert dictionary
        """
        # Extract document identification
        doc_id = doc.get('id', doc.get('document_number', doc.get('bill_id', str(hash(str(doc))))))
        source_type = doc.get('source_type', 'unknown')
        
        # Get document title
        title = doc.get('title', doc.get('description', 'Untitled Document'))
        
        # Get document URL if available
        url = doc.get('url', doc.get('html_url', doc.get('full_details_url', '')))
        
        # Extract top threat categories
        top_threats = []
        for category, score in sorted(
            doc.get('threat_categories', {}).items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:3]:
            threshold = self.config.get('nlp', {}).get('threat_threshold', 0.65)
            if score >= threshold * 0.8:  # Using lower threshold for including in alerts
                top_threats.append({"category": category, "score": score})
                
        # Create alert object
        alert = {
            "id": f"{source_type}_{doc_id}",
            "timestamp": datetime.now().isoformat(),
            "source": source_type,
            "document_id": doc_id,
            "title": title,
            "url": url,
            "threat_score": doc.get('threat_score', 0),
            "threat_categories": top_threats,
            "summary": doc.get('summary', ''),
            "entities": doc.get('entities', {}),
            "acknowledged": False
        }
        
        return alert
        
    def save_alert(self, alert: Dict):
        """
        Save an alert to the alerts directory.
        
        Args:
            alert: Alert dictionary
        """
        filename = f"{self.alert_dir}/{alert['id']}.json"
        
        with open(filename, 'w') as f:
            json.dump(alert, f, indent=2)
            
        logger.info(f"Alert saved to {filename}")
        
    def send_email_alert(self, alert: Dict):
        """
        Send an email alert if configured.
        
        Args:
            alert: Alert dictionary
        """
        if not self.config.get('alerts', {}).get('email_enabled', False) or not self.config.get('alerts', {}).get('email_recipients', []):
            return
            
        try:
            # Set up email message
            msg = MIMEMultipart()
            msg['Subject'] = f"Sentinel Alert: {alert['title']}"
            msg['From'] = "sentinel@example.com"  # Configure actual sender
            msg['To'] = ", ".join(self.config['alerts']['email_recipients'])
            
            # Create email body
            body = f"""
            <h2>⚠️ Sentinel Alert: Potential Threat Detected</h2>
            <p><strong>Document:</strong> {alert['title']}</p>
            <p><strong>Source:</strong> {alert['source']}</p>
            <p><strong>Threat Score:</strong> {alert['threat_score']:.2f}</p>
            <p><strong>Threat Categories:</strong> {', '.join(f"{c.get('category')} ({c.get('score', 0):.2f})" for c in alert.get('threat_categories', []))}</p>
            <p><strong>Summary:</strong> {alert.get('summary', '')}</p>
            {"<p><a href='" + alert.get('url', '') + "'>View Original Document</a></p>" if alert.get('url') else ""}
            """
            
            msg.attach(MIMEText(body, 'html'))
            
            # Send email (this is a placeholder - configure actual SMTP server)
            # with smtplib.SMTP('smtp.example.com', 587) as server:
            #     server.starttls()
            #     server.login('user', 'password')
            #     server.send_message(msg)
                
            logger.info(f"Email alert would be sent for {alert['id']} - email sending not configured")
            print(f"Email alert would be sent for document: {alert['title']}")
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
            
    def send_slack_alert(self, alert: Dict):
        """
        Send a Slack alert if configured.
        
        Args:
            alert: Alert dictionary
        """
        if not self.config.get('alerts', {}).get('slack_enabled', False) or not self.config.get('alerts', {}).get('slack_webhook', ''):
            return
            
        try:
            # Format Slack message
            message = {
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": f"⚠️ Sentinel Alert: {alert['title']}"
                        }
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Source:*\n{alert['source']}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Threat Score:*\n{alert['threat_score']:.2f}"
                            }
                        ]
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*Threat Categories:*\n" + ', '.join(f"{cat.get('category', '')} ({cat.get('score', 0):.2f})" for cat in alert.get('threat_categories', []))
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Summary:*\n{alert['summary']}"
                        }
                    }
                ]
            }
            
            # Add View Document button if URL is available
            if alert.get('url'):
                message["blocks"].append({
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "View Document"
                            },
                            "url": alert['url']
                        }
                    ]
                })
            
            # Send to Slack webhook (commented out for now)
            # response = requests.post(
            #    self.config['alerts']['slack_webhook'],
            #    json=message
            # )
            # response.raise_for_status()
            
            logger.info(f"Slack alert would be sent for {alert['id']} - Slack integration not configured")
            print(f"Slack alert would be sent for document: {alert['title']}")
            
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")
            
    def process_analyzed_documents(self, documents: List[Dict]):
        """
        Process analyzed documents and generate alerts as needed.
        
        Args:
            documents: List of documents with analysis results
        """
        alerts_generated = 0
        
        for doc in documents:
            if self.evaluate_document(doc):
                # Generate and save alert
                alert = self.generate_alert(doc)
                self.save_alert(alert)
                
                # Send notifications
                self.send_email_alert(alert)
                self.send_slack_alert(alert)
                
                logger.info(f"Alert triggered for document {alert['document_id']}")
                alerts_generated += 1
            else:
                logger.debug(f"No alert needed for document {doc.get('id', 'unknown')}")
                
        logger.info(f"Processed {len(documents)} documents, generated {alerts_generated} alerts")
        print(f"Processed {len(documents)} documents, generated {alerts_generated} alerts")
                
    def get_pending_alerts(self) -> List[Dict]:
        """
        Get list of unacknowledged alerts.
        
        Returns:
            List of alert dictionaries
        """
        alerts = []
        
        for filename in os.listdir(self.alert_dir):
            if filename.endswith('.json'):
                try:
                    with open(os.path.join(self.alert_dir, filename), 'r') as f:
                        alert = json.load(f)
                        if not alert.get('acknowledged', False):
                            alerts.append(alert)
                except Exception as e:
                    logger.error(f"Error loading alert from {filename}: {e}")
        
        return alerts
    
    def acknowledge_alert(self, alert_id: str):
        """
        Mark an alert as acknowledged.
        
        Args:
            alert_id: ID of the alert to acknowledge
        """
        filename = f"{self.alert_dir}/{alert_id}.json"
        
        if not os.path.exists(filename):
            logger.error(f"Alert file not found: {filename}")
            return False
            
        try:
            with open(filename, 'r') as f:
                alert = json.load(f)
                
            alert['acknowledged'] = True
            alert['acknowledged_at'] = datetime.now().isoformat()
            
            with open(filename, 'w') as f:
                json.dump(alert, f, indent=2)
                
            logger.info(f"Alert {alert_id} marked as acknowledged")
            return True
            
        except Exception as e:
            logger.error(f"Error acknowledging alert {alert_id}: {e}")
            return False


def main():
    """Main function to run the rules engine."""
    import argparse
    import glob
    
    parser = argparse.ArgumentParser(description='Process analyzed documents and generate alerts.')
    parser.add_argument('--input-dir', default='data/analyzed', help='Directory containing analyzed documents')
    parser.add_argument('--config', default='config.yaml', help='Path to configuration file')
    parser.add_argument('--list-pending', action='store_true', help='List pending alerts')
    parser.add_argument('--acknowledge', help='Acknowledge an alert by ID')
    args = parser.parse_args()
    
    engine = AlertEngine(args.config)
    
    # Handle alert acknowledgment
    if args.acknowledge:
        success = engine.acknowledge_alert(args.acknowledge)
        if success:
            print(f"Alert {args.acknowledge} acknowledged successfully")
        else:
            print(f"Failed to acknowledge alert {args.acknowledge}")
        return
    
    # List pending alerts
    if args.list_pending:
        alerts = engine.get_pending_alerts()
        if alerts:
            print(f"Found {len(alerts)} pending alerts:")
            for alert in alerts:
                print(f"- ID: {alert['id']}")
                print(f"  Title: {alert['title']}")
                print(f"  Threat Score: {alert['threat_score']:.2f}")
                categories = ', '.join(f"{cat.get('category', '')} ({cat.get('score', 0):.2f})" for cat in alert.get('threat_categories', []))
                print(f"  Categories: {categories}")
                print()
        else:
            print("No pending alerts found")
        return
    
    # Load analyzed documents
    documents = []
    for file_path in glob.glob(f"{args.input_dir}/*.json"):
        # Skip index files
        if "index_" in os.path.basename(file_path):
            continue
            
        try:
            with open(file_path, 'r') as f:
                doc = json.load(f)
                documents.append(doc)
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
    
    # Process documents
    engine.process_analyzed_documents(documents)


if __name__ == "__main__":
    main()
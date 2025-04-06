from flask import Blueprint, jsonify, request, send_file
from datetime import datetime
import json
import os
from typing import Dict, List, Optional

from ....services.collectors.congress import CongressCollector
from ....utils.auth import require_auth
from ....utils.pagination import paginate_results

congress_bp = Blueprint('congress', __name__)

@congress_bp.route('/documents', methods=['GET'])
@require_auth
def get_documents():
    """Get Congress.gov documents with filtering and pagination."""
    try:
        # Get query parameters
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        search = request.args.get('search')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        congress = request.args.getlist('congress')
        document_types = request.args.getlist('document_types')
        categories = request.args.getlist('categories')
        chamber = request.args.get('chamber')

        # Build filter criteria
        filters = {}
        if search:
            filters['search'] = search
        if start_date:
            filters['start_date'] = datetime.strptime(start_date, '%Y-%m-%d')
        if end_date:
            filters['end_date'] = datetime.strptime(end_date, '%Y-%m-%d')
        if congress:
            filters['congress'] = congress
        if document_types:
            filters['document_types'] = document_types
        if categories:
            filters['categories'] = categories
        if chamber:
            filters['chamber'] = chamber

        # Get documents from data directory
        documents = []
        data_dir = os.path.join('data', 'congress')
        for root, _, files in os.walk(data_dir):
            for file in files:
                if not file.endswith('.json'):
                    continue
                
                with open(os.path.join(root, file), 'r') as f:
                    doc = json.load(f)
                
                # Apply filters
                if not _matches_filters(doc, filters):
                    continue
                
                documents.append(doc)

        # Sort documents by date (newest first)
        documents.sort(key=lambda x: x.get('date', ''), reverse=True)

        # Paginate results
        paginated = paginate_results(documents, page, per_page)
        
        return jsonify(paginated)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@congress_bp.route('/documents/<document_id>', methods=['GET'])
@require_auth
def get_document(document_id: str):
    """Get a specific Congress.gov document by ID."""
    try:
        # Search for document in data directory
        data_dir = os.path.join('data', 'congress')
        for root, _, files in os.walk(data_dir):
            for file in files:
                if not file.endswith('.json'):
                    continue
                
                file_path = os.path.join(root, file)
                with open(file_path, 'r') as f:
                    doc = json.load(f)
                    
                if doc.get('document_id') == document_id:
                    return jsonify(doc)
        
        return jsonify({'error': 'Document not found'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@congress_bp.route('/documents/<document_id>/download', methods=['GET'])
@require_auth
def download_document(document_id: str):
    """Download a Congress.gov document as PDF."""
    try:
        # Search for document in data directory
        data_dir = os.path.join('data', 'congress')
        for root, _, files in os.walk(data_dir):
            for file in files:
                if not file.endswith('.json'):
                    continue
                
                file_path = os.path.join(root, file)
                with open(file_path, 'r') as f:
                    doc = json.load(f)
                    
                if doc.get('document_id') == document_id:
                    # Get PDF path from metadata
                    pdf_path = doc.get('metadata', {}).get('pdf_path')
                    if not pdf_path or not os.path.exists(pdf_path):
                        return jsonify({'error': 'PDF not found'}), 404
                    
                    return send_file(
                        pdf_path,
                        mimetype='application/pdf',
                        as_attachment=True,
                        download_name=f"congress_document_{document_id}.pdf"
                    )
        
        return jsonify({'error': 'Document not found'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@congress_bp.route('/documents/export', methods=['GET'])
@require_auth
def export_documents():
    """Export filtered Congress.gov documents as JSON."""
    try:
        # Get filter parameters
        filters = {
            'search': request.args.get('search'),
            'start_date': request.args.get('start_date'),
            'end_date': request.args.get('end_date'),
            'congress': request.args.getlist('congress'),
            'document_types': request.args.getlist('document_types'),
            'categories': request.args.getlist('categories'),
            'chamber': request.args.get('chamber')
        }

        # Convert date strings to datetime objects
        if filters['start_date']:
            filters['start_date'] = datetime.strptime(filters['start_date'], '%Y-%m-%d')
        if filters['end_date']:
            filters['end_date'] = datetime.strptime(filters['end_date'], '%Y-%m-%d')

        # Get documents from data directory
        documents = []
        data_dir = os.path.join('data', 'congress')
        for root, _, files in os.walk(data_dir):
            for file in files:
                if not file.endswith('.json'):
                    continue
                
                with open(os.path.join(root, file), 'r') as f:
                    doc = json.load(f)
                
                # Apply filters
                if not _matches_filters(doc, filters):
                    continue
                
                documents.append(doc)

        # Sort documents by date (newest first)
        documents.sort(key=lambda x: x.get('date', ''), reverse=True)

        # Create temporary export file
        export_file = os.path.join('temp', f'congress_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        os.makedirs('temp', exist_ok=True)
        
        with open(export_file, 'w') as f:
            json.dump(documents, f, indent=2)

        return send_file(
            export_file,
            mimetype='application/json',
            as_attachment=True,
            download_name=f"congress_documents_{datetime.now().strftime('%Y-%m-%d')}.json"
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500

def _matches_filters(doc: Dict, filters: Dict) -> bool:
    """Check if a document matches the given filters."""
    try:
        # Search filter
        if filters.get('search'):
            search_term = filters['search'].lower()
            searchable_text = ' '.join([
                str(doc.get('title', '')),
                str(doc.get('content', '')),
                str(doc.get('metadata', {}).get('number', '')),
                str(doc.get('metadata', {}).get('congress', '')),
                str(doc.get('metadata', {}).get('chamber', ''))
            ]).lower()
            
            if search_term not in searchable_text:
                return False

        # Date range filter
        if filters.get('start_date') or filters.get('end_date'):
            doc_date = datetime.strptime(doc.get('date', ''), '%Y-%m-%d')
            
            if filters.get('start_date') and doc_date < filters['start_date']:
                return False
            if filters.get('end_date') and doc_date > filters['end_date']:
                return False

        # Congress filter
        if filters.get('congress'):
            if str(doc.get('metadata', {}).get('congress')) not in filters['congress']:
                return False

        # Document type filter
        if filters.get('document_types'):
            if doc.get('metadata', {}).get('document_type') not in filters['document_types']:
                return False

        # Categories filter
        if filters.get('categories'):
            doc_categories = doc.get('metadata', {}).get('categories', [])
            if not any(cat in doc_categories for cat in filters['categories']):
                return False

        # Chamber filter
        if filters.get('chamber'):
            if doc.get('metadata', {}).get('chamber') != filters['chamber']:
                return False

        return True

    except Exception:
        return False 
from datetime import datetime
from database.db import db

class SystemMetric(db.Model):
    __tablename__ = 'system_metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    cpu_usage = db.Column(db.Float)
    memory_usage = db.Column(db.Float)
    disk_usage = db.Column(db.Float)
    network_load = db.Column(db.Float)
    
    def __init__(self, cpu_usage=None, memory_usage=None, disk_usage=None, network_load=None):
        self.cpu_usage = cpu_usage
        self.memory_usage = memory_usage
        self.disk_usage = disk_usage
        self.network_load = network_load

    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'cpu_usage': self.cpu_usage,
            'memory_usage': self.memory_usage,
            'disk_usage': self.disk_usage,
            'network_load': self.network_load
        } 
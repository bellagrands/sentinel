import os

class DatabaseConfig:
    DB_USER = os.environ.get('DB_USER', 'postgres')
    DB_PASS = os.environ.get('DB_PASSWORD', 'postgres')
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_NAME = os.environ.get('DB_NAME', 'postgres')
    DB_PORT = os.environ.get('DB_PORT', '5432')

    @classmethod
    def get_database_url(cls):
        return f'postgresql://{cls.DB_USER}:{cls.DB_PASS}@{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}'

    @classmethod
    def get_config(cls):
        return {
            'SQLALCHEMY_DATABASE_URI': cls.get_database_url(),
            'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        }

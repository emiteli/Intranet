import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = 'Emiteli@123'
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://user:user_password@db/intranet'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
    DEBUG = True

    
    
    LDAP_HOST = '10.0.21.1'  
    LDAP_BASE_DN = 'dc=emiteli,dc=com,dc=br'  
    LDAP_USER_DN = 'ou=users'
    LDAP_USER_RDN = 'uid'

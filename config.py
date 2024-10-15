import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = 'Emiteli@123'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'site.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(basedir, 'static/uploads')
    EXCEL_FOLDER = os.path.join(UPLOAD_FOLDER, 'excel')
    PROFILE_PICS_FOLDER = os.path.join(UPLOAD_FOLDER, 'png')

    DEBUG = True

    # Configurações do LDAP
    LDAP_HOST = '10.0.21.1'
    LDAP_BASE_DN = 'dc=emiteli,dc=com,dc=br'
    LDAP_USER_DN = 'ou=users'
    LDAP_USER_RDN = 'uid'
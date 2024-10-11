import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = 'Emiteli@123'  # Chave secreta para segurança
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'site.db') 
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
    DEBUG = True
    
    # Configurações do LDAP
    LDAP_HOST = '10.0.21.1'  # Endereço do servidor LDAP
    LDAP_BASE_DN = 'dc=emiteli,dc=com,dc=br'  # Corrigido: use vírgulas para separar os componentes
    LDAP_USER_DN = 'ou=users'
    LDAP_USER_RDN = 'uid'

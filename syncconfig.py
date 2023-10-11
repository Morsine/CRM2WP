# config file
DATABASE_SERVER = "192.168.3.10" #MSSQL IP/Hostname
DATABASE_INSTANCE = "PAYAMGOSTAR2" #MSSQL Database instance
DATABASE_NAME = "PayamGostar2" #MSSQL Database name
SQL_USERNAME = "sa" #MSSQL Username
SQL_PASSWORD = "CHANGE_ME" #MSSQL Password
WPWCADDR = "http://192.168.3.160/" #Wordpress/Woocommerce Address
WPWCKEY = "ck_e8d845a9cf6161679b63ef4654ad896d6f26bab8" #Wordpress/Woocommerce Key
WPWCSEC = "cs_675fa52c850f10a703992e0188d79a3da6679b74" #Wordpress/Woocommerce Secret
WPWCVER = "wc/v3" #Wordpress/Woocommerce API Version
CRM_ADMIN_PASSWORD = "CHANGE_ME" #CRM Admin password
debug = "no" #debugging mode (yes/no)
sqldriver = "SQL Server" #WINDOWS
#sqldriver = "/opt/microsoft/msodbcsql18/lib64/libmsodbcsql-18.3.so.1.1" #LINUX
Encrypt = "no" #encrypt connection from sync service to WPWC
TrustServerCertificate = "yes" #trust WPWC certificate?

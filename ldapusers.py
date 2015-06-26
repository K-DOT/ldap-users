#!/usr/bin/python
import ConfigParser
import subprocess
import readline
import getpass
import sys
import os

ldif_dir = './ldif'

# Read config file
config = ConfigParser.ConfigParser()
config.readfp(open('config'))
items = dict(config.items('LDAP_SETTINGS'))
cn = items['cn']
ou = items['ou']
dc1 = items['dc1']
dc2 = items['dc2']
if items['password']:
    ldap_password = items['password']
else:
    ldap_password = getpass.getpass('Enter LDAP password: ')

DN = "cn=%s,dc=%s,dc=%s" % (cn, dc1, dc2)

if not os.path.exists(ldif_dir):
    os.mkdir(ldif_dir)

def get_username_pass_from_config():
    result = []
    all_sections = config.sections()
    all_sections.remove('LDAP_SETTINGS') # Exclude ldap settings
    for section in all_sections:
        items = dict(config.items(section))
        username = items['username']
        password = items['password']
        result.append((username, password))
    return result
                
def get_username_pass():
    username = raw_input('Username: ')
    password = getpass.getpass('Password: ')
    return (username, password)

def get_last_uid():
    last_uid_command = 'ldapsearch -x | grep uidNumber | tail -1'
    last_uid = os.popen(last_uid_command).read().split(':')[-1] # Getting last user ID
    return last_uid or 16859

def create_ldif(username):     
    ldif = open('template.ldif', 'r').read()
    next_uid = str(int(get_last_uid()) + 1)
    changes = {
        '{username}'  :  username,
        '{uid}' :  next_uid,
        '{cn}'  :  cn,
        '{ou}'  :  ou,
        '{dc1}' :  dc1, 
        '{dc2}' :  dc2          
    }
    for key in changes.keys():
         ldif = ldif.replace(key, changes[key])    
    ldif_file_name = os.path.join(ldif_dir, '%s.ldif' % username)
    with open(ldif_file_name, 'w') as ldif_file:
        ldif_file.write(ldif)

def create(username, password, dn=DN):
    uid = "uid=%s,ou=%s,dc=%s,dc=%s" %  (username, ou, dc1, dc2)
    create_ldif(username)                
    os.system('ldapadd -x -w %s -D %s -f %s.ldif' % (ldap_password, dn, os.path.join(ldif_dir, username)))   
    os.system('ldappasswd -s %s -w %s -D %s -x %s' % (password, ldap_password, dn, uid))
    
def delete(username, dn=DN):
    uid =  "uid=%s,ou=%s,dc=%s,dc=%s" %  (username, ou, dc1, dc2)    
    os.system('ldapdelete -w %s -D %s %s' % (ldap_password, dn, uid))   
    os.remove(os.path.join(ldif_dir, '%s.ldif' % username)) 
    print 'deleted "%s"\n' % uid

if __name__ == '__main__':
    flags = {
        'delete' : '-d' in  sys.argv or '--delete' in sys.argv,
        'create_from_config' : '-c' in sys.argv or '--config' in sys.argv,
        'delete_from_config' : '-d' in sys.argv or '--delete' in sys.argv and ('-c' in sys.argv or'--config' in sys.argv)
    }
    if len(sys.argv) == 1:
        while True:                
            username, password = get_username_pass()      
            create(username, password)
            if raw_input('Continue? [Y/n] ').lower() == 'n': break
    elif len(sys.argv) == 2 and (sys.argv[1] == '-d' or sys.argv[1] == '--delete'):
        while True:
             username = raw_input('Username: ') 
             delete(username)
             print 'Deleted'
             if raw_input('Continue? [Y/n] ').lower() == 'n': break
    elif len(sys.argv) == 2 and (sys.argv[1] == '-c' or sys.argv[1] == '--config'):
        for (username, password) in get_username_pass_from_config():
            create(username, password)   
    elif len(sys.argv) == 3 and (sys.argv[2] == '-d' or sys.argv[1] == '--delete') and \
    (sys.argv[1] == '-c' or sys.argv[1] == '--config'):
        for (username, password) in get_username_pass_from_config():
            delete(username)          

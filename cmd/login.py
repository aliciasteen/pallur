import ldap

def check_credentials(username, password):
    """Checks username/password"""
    LDAP_SERVER = 'ldap://xxx'
    LDAP_USERNAME = '%s@xxx' %username
    LDAP_PASSWORD = password

    base_dn = 'DC=pallur'
    ldap_filter = 'userPrincipalName=%s@xxx.xx' % username
    attrs = ['memberOf']
    try:
        ldap_client = ldap.initialize(LDAP_SERVER)
        ldap_client.set_options(ldap.OPT_REFERALS,0)
        ldap_client.simple_bind_s(LDAP_USERNAME,LDAP_PASSWORD)
    except ldap.INVALID_CREDENTIALS:
        ldap_clind.unbind()
        return 'Wrong username or password'
    except ldap.SERVER_DOWN:
        return 'LDAP server not avalible'

    #all is well
    # maybe save username to file config file?
    return 'Login successful'

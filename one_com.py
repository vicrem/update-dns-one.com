#!/usr/bin/env python

import os
import sys
import json
import requests
from ipaddress import ip_interface, ip_address




class updateDns:


    def __init__(self, login_settings):

        self.domain = login_settings['domain']
        self.username = login_settings['username']
        self.password = login_settings['password']

        self.getextip = login_settings['ipify']
        self.redirect_url = login_settings['redirect_url']
        self.target_domain = login_settings['target_domain']





    def getExternalIp(self):

        extIP = requests.get(
            self.getextip
        ).text

        return extIP





    def findBetween(self, haystack, needle1, needle2):
        
        index1 = haystack.find(needle1) + len(needle1)
        index2 = haystack.find(needle2, index1 + 1)
        
        return haystack[index1 : index2]





    def selectAdminDomain(self, session):
        
        request = self.redirect_url + "/select-admin-domain.do?domain={}".format(self.domain)
        session.get(request)





    def getCustomRecords(self, session):
        
        print("Getting Records")
        
        getres = session.get(
            self.redirect_url + "/api/domains/" + self.domain + "/dns/custom_records"
        ).text

        return json.loads(getres)["result"]["data"]





    def changeIP(self, session, record):

        dns_url = self.redirect_url + "/api/domains/" + self.domain + "/dns/custom_records/" + record['id']

        sendheaders = {
            'Content-Type': 'application/json'
        }

        session.patch(
            dns_url, 
            data=json.dumps(record), 
            headers=sendheaders
        )

        print("Sent Change IP Request for record: " + '.'.join([record['attributes']['prefix'], self.domain]))





    def loginSession(self):
        
        print("Logging in...")
        session = requests.session()


        r = session.get(
            self.redirect_url
        )


        # find url to post login credentials to from form action attribute
        substrstart = '<form id="kc-form-login" class="Login-form login autofill" onsubmit="login.disabled = true; return true;" action="'
        substrend = '"'
        
        posturl = self.findBetween(
            r.text, 
            substrstart, 
            substrend
        ).replace('&amp;','&')



        logindata = {
            'username': self.username, 
            'password': self.password, 
            'credentialId' : ''
        }

        session.post(
            posturl, 
            data=logindata
        )

        print("Sent Login Data")

        

        # For accounts with multiple domains
        if self.target_domain:

            print("Setting active domain to: {}".format(self.target_domain))
            
            self.selectAdminDomain(
                session
            )

        return session






if __name__ == '__main__':

    login_settings = {
        'username': 'username@vicrem.se',
        'password': 'password',
        'domain': 'vicrem.se',
        'target_domain': 'vicrem.se',
        'ipify': 'https://api.ipify.org/',
        'redirect_url': 'https://www.one.com/admin'
    }

    run = updateDns(login_settings)


    if len(sys.argv) >= 2:

        try:

            extIP = ip_address(sys.argv[1])


        except ValueError:
            exit('Address is invalid: %s' % sys.argv[1])      


    else:
        
        extIP = run.getExternalIp()



    if extIP:

        session = run.loginSession()
        records = run.getCustomRecords(session)


        for record in records:

            ip_in_record = record['attributes']['content']


            if ip_interface(extIP) == ip_interface(ip_in_record):
                
                print('No need to update DNS entry')
            
            else:

                record['attributes']['content'] = extIP
                run.changeIP(session, record)

    else:

        sys.exit('Check your internet connection')

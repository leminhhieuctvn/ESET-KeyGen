from .SharedTools import *

from email import policy, parser

import requests
import time

DEFINE_PARSE_10MINUTEMAIL_INBOX_FUNCTION = """function parse_10minutemail_inbox() {
    updatemailbox()
    let mails = Array.from(document.getElementsByTagName('tr')).slice(1)
    let inbox = []
    for(let i=0; i < mails.length; i++) {
        let id = mails[i].children[0].children[0].href
        let from = mails[i].children[0].innerText
        let subject = mails[i].children[1].innerText
        inbox.push([id, from, subject]) }
    return inbox }"""
PARSE_GUERRILLAMAIL_INBOX = """
var email_list = document.getElementById('email_list').children
var inbox = []
for(var i=0; i < email_list.length-1; i++) {
    var mail = email_list[i].children
    var from = mail[1].innerText
    var subject = mail[2].innerText
    var mail_id = mail[0].children[0].value
    inbox.push([mail_id, from, subject])
}
return inbox
"""
GET_GUERRILLAMAIL_DOMAINS = """
var domains_options = document.getElementById('gm-host-select').options
var domains = [] 
for(var i=0; i < domains_options.length-1; i++) {
    domains.push(domains_options[i].value)
}
return domains
"""
PARSE_MAILTICKING_INBOX = """function MailTickingParse() {
    var inbox = []
    var mlist = document.getElementById("message-list").children
    for(i=0; i<mlist.length-1; i++) {
        var mfields = mlist[i].children
        var mail_id = mfields[0].children[0].href
        var from = mfields[0].innerText
        var subject = mfields[1].innerText
        inbox.push([mail_id, from, subject])
    }
    return inbox;
}
return MailTickingParse()"""
PARSE_FAKEMAIL_INBOX = """
let raw_inbox = Array.from(document.getElementById('schranka').children).slice(0, -3)
let inbox = []
for(let i=0; i < raw_inbox.length; i++) {
    let id = raw_inbox[i].dataset.href
    let from = raw_inbox[i].children[0].children[1].tagName.toLowerCase()
    let subject = raw_inbox[i].children[1].innerText.trim()
    inbox.push([id, from, subject])
}
return inbox
"""

class OneSecEmailAPI:
    def __init__(self):
        self.class_name = '1secmail'
        self.__login = None
        self.__domain = None
        self.email = None
        self.__api = 'https://www.1secmail.com/api/v1/'
        
    def init(self):
        url = f'{self.__api}?action=genRandomMailbox&count=1'
        try:
            r = requests.get(url)
        except:
            raise RuntimeError('SecEmailAPI: API access error!')
        if r.status_code != 200:
            raise RuntimeError('SecEmailAPI: API access error!')
        self.__login, self.__domain = str(r.content, 'utf-8')[2:-2].split('@')
        self.email = self.__login+'@'+self.__domain
    
    def login(self, login, domain):
        self.__login = login
        self.__domain = domain
    
    def read_email(self):
        url = f'{self.__api}?action=getMessages&login={self.__login}&domain={self.__domain}'
        print(url)
        try:
            r = requests.get(url)
        except:
            raise RuntimeError('SecEmailAPI: API access error!')
        if r.status_code != 200:
            raise RuntimeError('SecEmailAPI: API access error!')
        return r.json()
    
    def get_message(self, message_id):
        url = f'{self.__api}?action=readMessage&login={self.__login}&domain={self.__domain}&id={message_id}'
        print(url)
        try:
            r = requests.get(url)
        except:
            raise RuntimeError('SecEmailAPI: API access error!')
        if r.status_code != 200:
            raise RuntimeError('SecEmailAPI: API access error!')
        return r.json()

class DeveloperMailAPI:
    def __init__(self):
        self.class_name = 'developermail'
        self.email = None
        self.email_name = ''
        self.headers = {}
        self.api_url = 'https://www.developermail.com/api/v1'
    
    def init(self):
        r = requests.put(f'{self.api_url}/mailbox')
        self.email_name, token = list(r.json()['result'].values())
        self.email = self.email_name+'@developermail.com'
        self.headers = {'X-MailboxToken': token}

    def __parse_message(self, raw_message_body):
        message_bytes = raw_message_body.encode('utf-8')
        msg = parser.BytesParser(policy=policy.default).parsebytes(message_bytes)
        message_subject = msg['subject']
        message_from = msg['from']
        message_body = str(msg.get_payload(decode=True).decode(msg.get_content_charset())) # decoding MIME-Type to html
        return {'subject':message_subject, 'from':message_from, 'body':message_body}

    def get_messages(self):
        # get message IDs
        r = requests.get(
            f'{self.api_url}/mailbox/{self.email_name}',
            headers=self.headers
        )
        message_ids = r.json()['result']
        if message_ids == []:
            return None
        # parse messages
        messages = []
        for message_id in message_ids:
            try:
                r = requests.get(f'{self.api_url}/mailbox/{self.email_name}/messages/{message_id}', headers=self.headers)
                raw_message_body = r.json()['result']
                messages.append(self.__parse_message(raw_message_body))
            except:
                continue
        if messages == []:
            messages = None
        return messages
    
class GuerRillaMailAPI:
    def __init__(self, driver: Chrome):
        self.class_name = 'guerrillamail'
        self.driver = driver
        self.email = None
        self.window_handle = None

    def init(self):     
        self.driver.get('https://www.guerrillamail.com/')
        self.window_handle = self.driver.current_window_handle
        untilConditionExecute(self.driver, f'return {GET_EBID}("email-widget") != null')
        self.email = self.driver.execute_script(f'return {GET_EBID}("email-widget").innerText')
        # change to random available domain
        self.email = self.email.split('@')[0]+'@'+random.choice(self.driver.execute_script(GET_GUERRILLAMAIL_DOMAINS))
    
    def parse_inbox(self):
        self.driver.switch_to.window(self.window_handle)
        self.driver.get('https://www.guerrillamail.com/')
        inbox = self.driver.execute_script(PARSE_GUERRILLAMAIL_INBOX)
        return inbox

    def open_mail(self, id):
        self.driver.switch_to.window(self.window_handle)
        self.driver.get(f'https://www.guerrillamail.com/inbox?mail_id={id}')

class MailTickingAPI:
    def __init__(self, driver: Chrome):
        self.class_name = 'mailticking'
        self.driver = driver
        self.email = None
        self.window_handle = None

    def init(self):     
        self.driver.get('https://www.mailticking.com')
        self.window_handle = self.driver.current_window_handle
        untilConditionExecute(self.driver, f'return {GET_EBID}("newMailbox") != null')
        self.email = self.driver.execute_script(f'return {GET_EBCN}("form-control")[0].value')
        self.driver.execute_script(f'{GET_EBID}("newMailbox").click()')
        for _ in range(10):
            try:
                new_email = self.driver.execute_script(f'return {GET_EBCN}("form-control")[0].value')
                if new_email.lower().find('wait') == -1 and new_email != self.email:
                    self.email = new_email
                    return True
            except:
                pass
            time.sleep(1)
        raise RuntimeError("MailTickingAPI.init Error!")
    
    def parse_inbox(self):
        self.driver.switch_to.window(self.window_handle)
        self.driver.get('https://www.mailticking.com')
        inbox = self.driver.execute_script(PARSE_MAILTICKING_INBOX)
        return inbox

    def open_mail(self, id):
        self.driver.switch_to.window(self.window_handle)
        self.driver.get(id)

class FakeMailAPI:
    def __init__(self, driver: Chrome):
        self.class_name = 'fakemail'
        self.driver = driver
        self.email = None
        self.window_handle = None

    def init(self):     
        self.driver.get('https://www.fakemail.net')
        self.window_handle = self.driver.current_window_handle
        untilConditionExecute(self.driver, f'return {GET_EBID}("email").innerText != null')
        self.email = self.driver.execute_script(f'return {GET_EBID}("email").innerText')
    
    def parse_inbox(self):
        self.driver.switch_to.window(self.window_handle)
        self.driver.get('https://www.fakemail.net')
        inbox = self.driver.execute_script(PARSE_FAKEMAIL_INBOX)
        return inbox

    def open_mail(self, id):
        self.driver.switch_to.window(self.window_handle)
        self.driver.get(f'https://www.fakemail.net/email/id/{id}')

class InboxesAPI:
    def __init__(self, driver: Chrome):
        self.class_name = 'inboxes'
        self.driver = driver
        self.email = None
        self.window_handle = None
    
    def init(self):
        self.driver.get('https://inboxes.com')
        self.window_handle = self.driver.current_window_handle
        button = None
        for _ in range(DEFAULT_MAX_ITER):
            try:
                button = self.driver.find_element('xpath', '//button[contains(text(), "Get my first inbox!")]')
                break
            except:
                pass
            time.sleep(DEFAULT_DELAY)
        if button is not None:
            button.click()
            time.sleep(1)
            for button in self.driver.execute_script(f'return {GET_EBTN}("button")'):
                if button.text.strip().lower() == 'choose for me':
                    button.click()
                    break
            time.sleep(2)
            for element in self.driver.execute_script(f'return {GET_EBTN}("span")'):
                new_email = ''.join(element.text.split())
                if new_email is not None:
                    new_email = re.match(r'[-a-z0-9+.]+@[a-z]+(\.[a-z]+)+', new_email)
                    if new_email is not None:
                        self.email = new_email.group()
                        break
    
    def get_messages(self):
        r = requests.get(f'https://inboxes.com/api/v2/inbox/{self.email}')
        raw_inbox = r.json()['msgs']
        messages = []
        for message in raw_inbox:
            r = requests.get(f'https://inboxes.com/api/v2/message/{message["uid"]}').json()
            messages.append({
                'from': r['ff'][0]['address'],
                'subject': message['s'],
                'body': r['html']
            })
        return messages

class CustomEmailAPI:
    def __init__(self):
        self.class_name = 'custom'
        self.email = None

WEB_WRAPPER_EMAIL_APIS_CLASSES = (GuerRillaMailAPI, MailTickingAPI, FakeMailAPI, InboxesAPI)
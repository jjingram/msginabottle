import configparser
import imaplib
import email
from email.utils import parseaddr, parsedate_to_datetime

config = configparser.ConfigParser()
config.read('.miabrc')

M = imaplib.IMAP4_SSL(config['server']['hostname'])
M.login(config['login']['user'], config['login']['password'])

def getmsgs(mailbox, header):
    msgs = {}
    M.select(mailbox, True)
    typ, data = M.uid('search', None, 'ALL')
    for uid in data[0].split():
        typ, data = M.uid('fetch', uid, '(RFC822)')
        msg = email.message_from_bytes(data[0][1])
        name, addr = parseaddr(msg[header])
        if 'Date' not in msg or 'Message-Id' not in msg:
            continue
        if addr not in msgs:
            msgs[addr] = []
        msgs[addr].append(msg)
    M.close()
    return msgs

inbox = getmsgs('INBOX', 'From')
sent = getmsgs('Sent', 'To')
msgs = {}
for contact in sent:
    if contact in inbox:
        msgs[contact] = inbox[contact] + sent[contact]
    else:
        msgs[contact] = sent[contact]

for contact in msgs:
    print("### %s ###\n" % contact)
    msgs[contact] = sorted(msgs[contact], key=lambda msg: parsedate_to_datetime(msg['Date']).replace(tzinfo=None))
    chatmsgs = {}
    for msg in msgs[contact]:
        if 'Email2Chat-Version' in msg:
            chatmsgs[msg['Message-Id']] = True
        elif 'In-Reply-To' in msg and chatmsgs.get(msg['In-Reply-To'], False):
            chatmsgs[msg['Message-Id']] = True
    prev = {}
    for msg in msgs[contact]:
        if chatmsgs.get(msg['Message-Id'], False) and not prev.get(msg['Message-Id'], False):
            prev[msg['Message-Id']] = True
            print(msg)

M.logout()

import argparse
import email
from email.utils import parseaddr
from imapclient import IMAPClient
import nagiosplugin

__author__ = 'stk'

class Mail(nagiosplugin.Resource):

    def __init__(self, args):
        self.args = args

    def probe(self):

        # connect to imap server
        server = IMAPClient(self.args.host, use_uid=True, ssl=self.args.ssl)
        server.login(self.args.username, self.args.password)

        select_info = server.select_folder('INBOX')
        recentmessages = server.search(['RECENT'])
        unseenmessages = server.search(['UNSEEN'])

        print(len(unseenmessages))

        recentcount = 0
        unseencount = 0

        # get new mail sender and subjects
        responserecent = server.fetch(recentmessages, ['RFC822'])

        # get unseen mail sender and subjects
        responseunseen = server.fetch(unseenmessages, ['RFC822'])

        for msgid, data in responserecent.iteritems():
            msg = email.message_from_string(data['RFC822'])
            address = parseaddr(msg['from'])[1]
            subject = msg['subject']

            if self.args.address == address and self.args.subject == subject:
                recentcount = recentcount + 1

        for msgid, data in responseunseen.iteritems():

            msg = email.message_from_string(data['RFC822'])
            address = parseaddr(msg['from'])[1]
            subject = msg['subject']

            if self.args.address == address and self.args.subject == subject:
                unseencount = unseencount + 1

        status = 0

        if unseencount > 0:
            status = 1
        elif recentcount > 0:
            status = 2

        yield nagiosplugin.Metric('status', status, context='status')
        yield nagiosplugin.Metric('recent', recentcount, context='default')
        yield nagiosplugin.Metric('unseen', unseencount, context='default')

class MailSummary(nagiosplugin.Summary):

    def ok(self, results):
        return str(results["status"].metric)

@nagiosplugin.guarded
def main():

    argp = argparse.ArgumentParser(description=__doc__)
    argp.add_argument('-H', '--host', dest='host', default='', help='imap host')
    argp.add_argument('-u', '--user', dest='username', default='', help='imap user')
    argp.add_argument('-p', '--pass', dest='password', default='', help='imap password')
    argp.add_argument('-s', '--subject', dest='subject', default='', help='mail subject')
    argp.add_argument('-a', '--address', dest='address', default='', help='sender')
    argp.add_argument('-S', '--ssl', dest='ssl', action='store_true', default=False)
    args = argp.parse_args()


    check = nagiosplugin.Check(Mail(args), nagiosplugin.ScalarContext('status', '0:0', '0:1'), MailSummary())

    check.main()

if __name__ == '__main__':
    main()

#!~/bin/python -tt

import subprocess
import time
import sys
import getpass
import smtplib
import datetime

class Settings:
    url = 'http://cms.cern.ch/iCMS'
    report_as = None
    report_to = None
    cc_to = []
    smtp_server = None
    password = None
    use_tls = None
    verbose = None
    sleep_time = 60

    def __init__(self):
        return

def main():
    settings = Settings()
    args = sys.argv

    try:
        settings.verbose = '-v' in args or '--verbose' in args or '--v' in args
        settings.use_tls = '--use_tls' in args

        if '--help' in args or '-h' in args:
            print_help()
            return

        if '--url' in args:
            settings.url = args[args.index('--url')+1]

        print 'Checking availability of %s' % settings.url

        if '--sleep' in args:
            settings.sleep_time = args[args.index('--sleep')+1]

        if '--report-to' in args:
            settings.report_to = args[args.index('--report-to')+1].split()
            settings.report_as = args[args.index('--report-as')+1]
            settings.smtp_server = args[args.index('--smtp-server')+1]
            if '--password' in args:
                settings.password = args[args.index('--password')+1]
            elif '--pass' in args:
                settings.password = args[args.index('--pass')+1]
            elif '-p' in args:
                settings.password = args[args.index('-p')+1]
            else:
                settings.password = getpass.getpass()

            send_mail('Monitoring started', 'Started monitoring on %s\n' % settings.url, settings)
        else:
            settings.verbose = True

    except:
        print_help()
        return

    last_fine = True
    while True:
        code = subprocess.check_output('curl ' + settings.url + ' -sL -w "%{http_code}" -o /dev/null', 
                                       shell=True)
        if last_fine and code != '200':
            raise_an_issue(code, settings)
        elif not last_fine and code == '200':
            notify_problem_gone(code, settings)
        
        if settings.verbose:
            print 'Received code %s at %s UTC' % (code, str(datetime.datetime.utcnow()))
        
        last_fine = (code == '200')
        time.sleep(settings.sleep_time)

def raise_an_issue(code, settings):
    subject = '%s seems down!' % settings.url
    message = 'Last seen code was %s at %s UTC' % (code, str(datetime.datetime.utcnow()))
    if settings.report_to is not None:
        send_mail(subject, message, settings)
    print subject, message

def notify_problem_gone(code, settings):
    subject = '%s seems back up!' % settings.url
    message = 'Last seen code was %s at %s UTC' % (code, str(datetime.datetime.utcnow()))
    if settings.report_to is not None:
        send_mail(subject, message, settings)
    print subject, message

def send_mail(subject, message, settings):
    try:
        header = 'From: %s\n' % settings.report_as
        header += 'To: %s\n' % ','.join(settings.report_to)
        header += 'Cc: %s\n' % ','.join(settings.cc_to)
        header += 'Subject: %s\n\n' % subject
        message = header + message

        server = smtplib.SMTP(settings.smtp_server)
        if settings.use_tls:
            server.starttls()
        server.login(settings.report_as, settings.password)
        problems = server.sendmail(settings.report_as, settings.report_to, message)
        server.quit()
        return problems
    except:
        print "Problem with sending mail experienced! Message dump: \n%s" % (message)

def print_help():
    print """
Upsite - tool periodically checking and reporting a website's availability.
Usage:

upsite [--verbose | -v ] [--url ...] [--sleep ...] [--report-to ...] [--report-as ...] [--smtp_server ...] [--password | --pass | -p ]

Options:
    --verbose | -v              : prints every response it receives
    --url site_url              : address to watch
    --sleep time                : interval between requests (in seconds), 60 by default
    --report-to address         : e-mail address to send messages to, if provided, the program checks:
                                    --report-to,
                                    --report-as,
                                    --smtp-server
                                    --password | --pass | -p (or asks for password if not given).
    --reort-as address          : e-mail address to send messages from
    --smtp-server address:port  : SMTP server address of the --report-as e-mail account
    --password | --pass | -p    : Password needed to send emails.
    --use_tls                   : Enables TLS when connecting to the e-mail server.
    --help                      : Prints this message and exits.
"""


if __name__ == '__main__':
    main()


from personalcapital import PersonalCapital, RequireTwoFactorException, TwoFactorVerificationModeEnum
import getpass
import json
import logging
import os
from datetime import datetime, timedelta
import sys
import argparse

class PewCapital(PersonalCapital):
    """
    Extends PersonalCapital to save and load session
    So that it doesn't require 2-factor auth every time
    """
    def __init__(self):
        PersonalCapital.__init__(self)
        self.__session_file = os.getenv('PEW_SESSION_FILE','session.json')

    def load_session(self):
        try:
            with open(self.__session_file) as data_file:
                cookies = {}
                try:
                    cookies = json.load(data_file)
                except ValueError as err:
                    logging.error(err)
                self.set_session(cookies)
        except IOError as err:
            logging.error(err)

    def save_session(self):
        with open(self.__session_file, 'w') as data_file:
            data_file.write(json.dumps(self.get_session()))

def get_email():
    email = os.getenv('PEW_EMAIL')
    if not email:
        print('You can set the environment variables for PEW_EMAIL and PEW_PASSWORD so the prompts don\'t come up every time')
        return input('Enter email:')
    return email

def get_password():
    password = os.getenv('PEW_PASSWORD')
    if not password:
        return getpass.getpass('Enter password:')
    return password

# Instantiate the parser
parser = argparse.ArgumentParser(description='Optional app description')

parser.add_argument('--year', action='store_true',
                    help='Get a full year')

parser.add_argument("--stdout", "-", action='store_true')


def main():
    email, password = get_email(), get_password()
    pc = PewCapital()
    pc.load_session()

    args = parser.parse_args()
    year = args.year

    try:
        pc.login(email, password)
    except RequireTwoFactorException:
        pc.two_factor_challenge(TwoFactorVerificationModeEnum.SMS)
        pc.two_factor_authenticate(TwoFactorVerificationModeEnum.SMS, input('code: '))
        pc.authenticate_password(password)

    now = datetime.now()
    date_format = '%Y-%m-%d'
    # get the last week's transactions, there will be overlap
    days = 7
    if year:
        days = 365

    start_date = (now - (timedelta(days=days+1))).strftime(date_format)
    end_date = (now - (timedelta(days=1))).strftime(date_format)
    transactions_response = pc.fetch('/transaction/getUserTransactions', {
        'sort_cols': 'transactionTime',
        'sort_rev': 'true',
        'page': '0',
        'rows_per_page': '100',
        'startDate': start_date,
        'endDate': end_date,
        'component': 'DATAGRID'
    })
    pc.save_session()

    output_dir = os.path.abspath(os.getenv('PEW_OUTPUT_DIR','./'))

    if args.stdout:
        sys.stdout.buffer.write(transactions_response.content)
    else:
        path = output_dir+"/transactions_"+end_date+"_"+start_date+".json"
        with open (path, "wb") as f:
            f.write(transactions_response.content)

if __name__ == '__main__':
    main()

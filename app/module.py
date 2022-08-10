from werkzeug.security import generate_password_hash

from .secret import ADMIN_PASSWORD, FITRY_PASSWORD
from . import db
from .models import Staff


def format_pdf_title(title):
    result = ''
    for char in title:
        if char == ',':
            continue
        result += char
    return result


def format_name(name_part):
    splited_name = [letter for letter in name_part]
    splited_name[0] = splited_name[0].upper()
    return ''.join(splited_name)


# membuat akun admin untuk pertama kali run
def create_admin():
    check_admin = Staff.query.filter_by(username='admin').first()
    if not check_admin:
        print('##### Generating admin #####')
        admin = Staff(
            first_name = 'Admin',
            last_name = '_',
            username = 'admin',
            password = generate_password_hash(ADMIN_PASSWORD, method='sha256'),
            email = 'admin@admin.com',
            phone_number = '-',
            isAdmin = True
        )
        db.session.add(admin)
        db.session.commit()
        print('+++++ admin generated +++++')
    else:
        print('----- admin already exist -----')

    check_fitry = Staff.query.filter_by(username='fitry').first()
    if not check_fitry:
        print('##### Generating fitry #####')
        fitry = Staff(
            first_name = 'Fitry',
            last_name = 'Auliaallah',
            username = 'fitry',
            password = generate_password_hash(FITRY_PASSWORD, method='sha256'),
            email = 'email@email.com',
            phone_number = '1',
            isAdmin = False
        )
        db.session.add(fitry)
        db.session.commit()
        print('+++++ fitry generated +++++')
    else:
        print('----- fitry already exist -----')
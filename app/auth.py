from flask import Blueprint, flash, render_template, request, url_for, redirect
from flask_login import current_user, login_required, login_user, logout_user

from werkzeug.security import generate_password_hash, check_password_hash

import sqlalchemy

from .models import db, Staff
from .forms import Login
from .secret import ADMIN_PASSWORD, FITRY_PASSWORD


auth = Blueprint('auth', __name__)


# membuat akun admin untuk pertama kali run
def create_admin():
    from .models import Staff

    check_admin = Staff.query.filter_by(username='admin').first()
    if check_admin:
        print('----- admin already exist -----')
        return

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

    check_fitry = Staff.query.filter_by(username='fitry').first()
    if check_fitry:
        print('----- fitry already exist -----')
        return

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


# otentikasi user menggunakan class wtform login() dari forms.py
@auth.route('/', methods=['GET', 'POST'])
def login():
    login_form = Login()

    # jika request GET, rendre halaman saja
    if request.method == 'GET':
        if current_user.is_authenticated:
            return redirect(url_for('views.dashboard'))
        create_admin()
        return render_template('login.html', login_form=login_form)

    # jika POST lakukan otentikasi login
    staff = Staff.query.filter_by(username=login_form.username.data).first()
    if staff:
        if check_password_hash(staff.password, login_form.password.data):
            login_user(staff, remember=True)
            return redirect(url_for('views.init', from_login=1))

    flash('username atau password salah.', category='error')
    return redirect(url_for('auth.login'))


# logout user
@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout success', category='success')
    return redirect(url_for('auth.login'))

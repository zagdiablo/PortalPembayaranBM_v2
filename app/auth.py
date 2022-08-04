from flask import Blueprint, flash, render_template, request, url_for, redirect
from flask_login import current_user, login_required, login_user, logout_user

from werkzeug.security import check_password_hash

from .models import Staff
from .forms import Login
from .module import create_admin


auth = Blueprint('auth', __name__)


# otentikasi user menggunakan class wtform login() dari forms.py
@auth.route('/', methods=['GET', 'POST'])
def login():
    login_form = Login()

    # jika request GET, render halaman saja
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
            return redirect(url_for('operation.init', from_login=1))

    flash('username atau password salah.', category='error')
    return redirect(url_for('auth.login'))


# logout user
@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout success', category='success')
    return redirect(url_for('auth.login'))

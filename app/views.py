from flask import Blueprint, flash, render_template, request, url_for, redirect
from flask_login import login_required, current_user

import sqlalchemy

from .models import db, Staff, Client, Year, PaymentData
from .module import format_name
from datetime import date, datetime, timedelta
from werkzeug.security import generate_password_hash


views = Blueprint('views', __name__)


#TODO cetak kartu cetak kuitansi versi image


# ---- staff acessible part of the application ----
# menampilkan dashboard jikan login valid
@views.route('/dashboard')
@login_required
def dashboard():
    all_client = Client.query.all()
    all_staff = Staff.query.all()
    all_payment = PaymentData.query.order_by(PaymentData.last_edit_date.desc()).all()
    all_year = Year.query.filter_by(year_name=date.today().year).first()
    all_month = all_year.months
    client_data_last_5_day = []

    # query data yang tanggal editnya tidak lebih dari 5 hari yang lalu
    for payment in all_payment:
        for count in range(len(all_payment)):
            if count < 5 and payment.last_edit_date == date.today() - timedelta(days=count):
                client_data_last_5_day.append(payment)

    return render_template('dashboard.html', client_data=all_client, staff_data=all_staff, history_data=client_data_last_5_day,
        month_data=all_month, current_staff=current_user)
    

# halaman untuk mengubah username dan password staff
@views.route('/editprofile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    client_name = f'{current_user.first_name} {current_user.last_name} ({current_user.username})'

    # jika method GET
    # hanya muat halaman
    if request.method == 'GET':
        return render_template('editprofile.html', client_name = client_name, current_staff=current_user)

    # jika method POST
    # ambil data dari form halaman dan lakukan update database pada username dan password staff
    form_username = request.form.get('username')
    # cek form password jika sama lanjutkan jika berbeda ulangi input password
    if request.form.get('password1') != request.form.get('password2'):
        flash('Password tidak sama, ulangi input password', category='error')
        return redirect(url_for('views.edit_profile', client_name=client_name))
    form_password = request.form.get('password1')
    form_email = request.form.get('email')
    form_phone_number = request.form.get('phone_number')

    # update data berdasarkan form input
    staff = Staff.query.filter_by(id=current_user.id).first()
    if staff:
        update_profile = Staff.query.filter_by(id=current_user.id).update({
            Staff.username : form_username if form_username else current_user.username,
            Staff.email : form_email if form_email else current_user.email,
            Staff.phone_number : form_phone_number if form_phone_number else current_user.phone_number   
        })
        db.session.commit()
        if form_password:
            update_password = Staff.query.filter_by(id=current_user.id).update({
                Staff.password : generate_password_hash(form_password)
            })
            db.session.commit()
        flash('Berhasil update profil, silahkan login kembali', category='success')
        return redirect(url_for('auth.logout'))

    flash('Username tidak ditemukan, silahkan kontak admin', category='error')
    return redirect(url_for('views.edit_profile', client_name=client_name))


# menampilkan daftar client
@views.route('/clientlist', methods=['GET', 'POST'])
@login_required
def client_list():
    if request.method == 'GET':
        client_list = Client.query.order_by(Client.first_name).all()
        return render_template('clientlist.html', clients=client_list, current_staff=current_user)

    search_value = request.form.get('search_value')
    if search_value:
        return redirect(url_for('views.search_client', from_loc='client_list', value=search_value))
    return redirect(url_for('views.client_list'))


@views.route('/editclient/<int:client_id>', methods=['GET', 'POST'])
@login_required
def edit_client(client_id):
    if request.method == 'GET':
        client = Client.query.filter_by(id=client_id).first()
        return render_template('/views/editclient.html', current_staff=current_user, client=client)

    new_first_name = request.form.get('first_name')
    new_last_name = request.form.get('last_name')
    new_call_name = request.form.get('call_name')

    new_data = Client.query.filter_by(id=client_id).update({
        Client.first_name: new_first_name if new_first_name else Client.first_name,
        Client.last_name: new_last_name if new_last_name else Client.last_name,
        Client.call_name: new_call_name if new_call_name else Client.call_name
    })
    db.session.commit()

    return redirect(url_for('views.client_list'))


# menampilkan daftar client yang telah di archive
@views.route('/archivelist', methods=['GET', 'POST'])
@login_required
def archive_list():
    if request.method == 'GET':
        client_list = Client.query.order_by(Client.first_name).all()
        return render_template('archivelist.html', clients=client_list, current_staff=current_user)

    search_value = request.form.get('search_value')
    if search_value:
        return redirect(url_for('views.search_client', from_loc='archive_list', value=search_value))
    return redirect(url_for('views.archive_list'))


# endpoint pencarian client list dan archive list
@views.route('/search/<string:from_loc>/<string:value>', methods=['GET', 'POST'])
@login_required
def search_client(from_loc, value):
    raw_client_list = Client.query.order_by(Client.first_name).all()
    client_list = []
    for client in raw_client_list:
        name_str = f'{str(client.first_name).lower()} {str(client.last_name).lower()} ({str(client.call_name).lower()})'
        if value in name_str:
            client_list.append(client)

    if from_loc == 'client_list':
        return render_template('/operation_template/search_client_list.html', clients=client_list, current_staff=current_user, 
            search_value=value, is_search=True)

    if from_loc == 'archive_list':
        return render_template('/operation_template/search_archive_list.html', clients=client_list, current_staff=current_user, 
            search_value=value, is_search=True)

    return redirect(url_for('views.dashboard'))


# menambah client baru dan mempopulasi database dengan data inisial ('belum lunas')
@views.route('/addclientdata', methods = ['GET', 'POST'])
@login_required
def add_client_data():
    # jika method GET
    # hanya menampilkan halaman
    if request.method == 'GET':
        return render_template('addclient.html', current_staff=current_user)

    # jika method POST
    # ambil data dari form template dan memasukan data ke database
    form_firstname = format_name(request.form.get('firstname'))
    form_lastname = format_name(request.form.get('lastname'))
    form_callname = request.form.get('callname')

    new_client = Client(
        first_name = form_firstname,
        last_name = form_lastname,
        call_name = form_callname
    )
    db.session.add(new_client)
    try:
        db.session.commit()
    except sqlalchemy.exc.IntegrityError:
        flash(f'Client dengan nama panggilan {form_callname} sudah ada!', category='error')
        return redirect(url_for('views.add_client_data'))

    # populasi data pembayaran client dengan value "belum lunas"
    client = new_client
    year = Year.query.filter_by(year_name=date.today().year).first()
    month_in_year = year.months

    for month in month_in_year:
        new_payment_data = PaymentData(
            paid_month = month.id,
            paid_year = year.id,
            payer = client.id,
            isPaid = False,
            date_paid = None,
            last_edit_by = current_user.id,
            last_edit_date = date.today()
        )
        db.session.add(new_payment_data)
        db.session.commit()

    flash('Berhasil menambah client!', category='success')
    return redirect(url_for('views.add_client_data'))


# tampilkan list data tahun
@views.route('/datapembayaran/<int:client_id>')
@login_required
def data_pembayaran(client_id):
    client = Client.query.filter_by(id=client_id).first()
    year_list = Year.query.all()
    return render_template('datapembayaran.html', client=client, year_button_display='Pilih Tahun', 
        year_list=year_list, current_staff=current_user)


# display user payment data in that year montly
@views.route('/datapembayaran/<int:client_id>/<string:year>', methods=['GET', 'POST'])
@login_required
def display_data_pembayaran(client_id, year):
    # query data inisial untuk pemuatan halaman
    client = Client.query.filter_by(id=client_id).first()
    year_object = Year.query.filter_by(year_name=year).first()
    payment_data = PaymentData.query.filter_by(payer=client.id, paid_year=year_object.id).all()
    year_list = Year.query.all()
    staff_list = Staff.query.all()
    month_in_year = year_object.months
    display_table = True
    monthly_payment_date = []
    # populasi list monthly_payment_data dengan data tanggal pembayaran
    for num in range(12):
        the_month = PaymentData.query.filter_by(payer=client.id, paid_year=year_object.id, paid_month=num+1).first()
        monthly_payment_date.append(the_month.date_paid)

    # jika method GET
    # maka muat halaman tanpa melakukan update database
    if request.method == 'GET':
        return render_template('datapembayaran.html', client=client, year_button_display=year, 
            display_table=display_table, year_list=year_list, months=month_in_year, 
            month_payment_data=zip(payment_data, month_in_year, monthly_payment_date), staff_list=staff_list, 
            current_staff=current_user)

    # jika method POST
    # looping input database data pembayaran per bulan
    for num in range(12):
        old_payment_data = PaymentData.query.filter_by(payer=client.id, paid_year=year_object.id, paid_month=num+1).first()
        form_payment_state = request.form.get(f'month{num+1}')
        form_payment_paid_date = request.form.get(f'tanggal_bayar{num+1}')

        # jika form_state lunas dan state lama tidak sama dengan form_state, lakukan cek tanggal
        # jika tidak ada input tanggal maka alert error dan muat ulang
        if form_payment_state == 'lunas' and old_payment_data.states != 'lunas':
            if not form_payment_paid_date:
                flash('Jangan lupa isi tanggal pembayaran lunas', category='error')
                return redirect(url_for('views.display_data_pembayaran', client_id=client_id, year=year))
        
        # jika state tidak sama dengan yang lama maka update
        # (state, date_paid <wajib>, last edit by <wajib>, [jika lunas] is paid true <wajib>)
        if form_payment_state != old_payment_data.states:
            update_payment_data = PaymentData.query.filter_by(payer=client.id, paid_year=year_object.id, paid_month=num+1).update({
                PaymentData.states : form_payment_state if old_payment_data.states != form_payment_state else old_payment_data.states,
                PaymentData.date_paid : form_payment_paid_date if form_payment_paid_date else old_payment_data.date_paid,
                PaymentData.last_edit_by : current_user.id if old_payment_data.last_edit_by != current_user.id else old_payment_data.last_edit_by,
                PaymentData.last_edit_date : datetime.now(),
                PaymentData.isPaid : True if form_payment_state == 'lunas' else False
            })
        db.session.commit()
        # jika hanya tanggal pembayaran yang tidak sama maka update
        # (tanggal pembayaran, last edit <wajib>, last date <wajib>)
        if form_payment_paid_date:
            update_payment_data = PaymentData.query.filter_by(payer=client.id, paid_year=year_object.id, paid_month=num+1).update({
                PaymentData.date_paid : form_payment_paid_date if form_payment_paid_date else old_payment_data.date_paid,
                PaymentData.last_edit_by : current_user.id if old_payment_data.last_edit_by != current_user.id else old_payment_data.last_edit_by,
                PaymentData.last_edit_date : datetime.now(),
            })
        db.session.commit()

    return redirect(url_for('views.display_data_pembayaran', client_id=client_id, year=year))


# ---- admin accessible part of the aplication ----
@views.route('/adminpanel', methods=['GET', 'POST'])
@login_required
def admin_panel():
    if not current_user.isAdmin:
        return redirect(url_for('views.dashboard'))

    if request.method == 'GET':
        return render_template('adminpanel.html', current_staff=current_user)
 
    form_firstname = format_name(request.form.get('firstname'))
    form_lastname = format_name(request.form.get('lastname'))
    form_username = request.form.get('username')
    form_password1 = request.form.get('password1')
    form_password2 = request.form.get('password2')
    form_email = request.form.get('email')
    form_phonenumber = request.form.get('phonenumber')
    form_isadmin = True if request.form.get('isadmin') == 'on' else False

    if form_password1 != form_password2:
        flash('Password tidak sama', category='error')
        return redirect(url_for('views.admin_panel'))

    new_staff = Staff(
        first_name = form_firstname,
        last_name = form_lastname,
        username = form_username,
        password = generate_password_hash(form_password1, method='sha256'),
        email = form_email,
        phone_number = form_phonenumber,
        isAdmin = form_isadmin
    )
    db.session.add(new_staff)
    try:
        db.session.commit()
    except sqlalchemy.exc.IntegrityError as e:
        if 'UNIQUE' in str(e):
            flash('Username sudah ada!', category='error')
        else:
            flash(e, category='error')
        return redirect(url_for('views.admin_panel'))

    flash('Berhasil menambah staff!', category='success')
    return redirect(url_for('views.admin_panel'))
from flask import (
    redirect,
    Blueprint,
    url_for,
    flash,
    render_template,
    make_response,
    url_for,
)
from flask_login import login_required, current_user
from datetime import date

import pdfkit
import platform
import os

from . import db
from .models import Year, Month, Client, PaymentData, Staff
from .module import format_pdf_title


operation = Blueprint("operation", __name__)


# Variabel lokasi untuk css cetakkartu
if os.name == "posix":
    css = "/home/sistempembayaranbm/PortalPembayaranBM_v2/app/static/css/cetakkartu.css"
elif os.name == "nt":
    css = "C:/Users/Adit/Documents/github_repo/PortalPembayaranBM_v2/app/static/css/cetakkartu.css"


# konfigurasi wkhtmltopdf untuk deployment di heroku
# NOTE silahkan ubah sesuai kebutuhan server deployment
WKHTMLTOPDF_CMD = ""
if platform.system() == "Windows":
    WKHTMLTOPDF_CMD = "app/bin/windows/wkhtmltopdf.exe"
else:
    WKHTMLTOPDF_CMD = "/usr/bin/wkhtmltopdf"
pdfkit_config = pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF_CMD)


# inisialisasi dan update database secara otomatis ke tahun sekarang sebelum mengakses daftar client
@operation.route("/init/<int:from_login>")
@login_required
def init(from_login):
    year = Year.query.filter_by(year_name=str(date.today().year)).first()
    month_preset = [
        "Januari",
        "Februari",
        "Maret",
        "April",
        "Mei",
        "Juni",
        "Juli",
        "Agustus",
        "September",
        "Oktober",
        "November",
        "Desember",
    ]
    if not year:
        print("generated year")
        new_year = Year(year_name=str(date.today().year))
        db.session.add(new_year)
        db.session.commit()
        if not from_login:
            return redirect(url_for("operation.init"))
        else:
            return redirect(url_for("operation.init", from_login=from_login))

    month = Month.query.filter_by(year_id=year.id).first()
    if not month:
        print("generated month")
        for num in range(0, 12):
            new_month = Month(month_name=month_preset[num], year_id=year.id)
            db.session.add(new_month)
            db.session.commit()

    clients = Client.query.all()
    month_in_year = year.months

    for client in clients:
        for month in month_in_year:
            cek_payment_data_month = PaymentData.query.filter_by(
                payer=client.id, paid_month=month.id
            ).first()
            if cek_payment_data_month:
                continue
            new_payment_data = PaymentData(
                paid_month=month.id,
                paid_year=year.id,
                payer=client.id,
                isPaid=False,
                date_paid=None,
                last_edit_by=current_user.id,
                last_edit_date=date.today(),
            )
            db.session.add(new_payment_data)
            db.session.commit()

    if not from_login:
        return redirect(url_for("views.client_list"))
    else:
        return redirect(url_for("views.dashboard"))


# endpoint fungsi untuk meng-archive client
@operation.route("/archive/<int:client_id>")
@login_required
def archive_client(client_id):
    client = Client.query.filter_by(id=client_id).first()

    to_archive = Client.query.filter_by(id=client_id).update({Client.is_archived: True})
    db.session.commit()

    flash(
        f"Berhasil memasukan {client.first_name} {client.last_name} {client.call_name} archive",
        category="success",
    )
    return redirect(url_for("views.client_list", current_staff=current_user))


# endpoint fungsi untuk mengembalikan client dari archive ke daftar client
@operation.route("/unarchive/<int:client_id>")
@login_required
def unarchive_client(client_id):
    client = Client.query.filter_by(id=client_id).first()

    to_archive = Client.query.filter_by(id=client_id).update(
        {Client.is_archived: False}
    )
    db.session.commit()

    flash(f"Berhasil mengeluarkan {client.call_name} dari archive", category="success")
    return redirect(url_for("views.archive_list", current_staff=current_user))


# cetak kartu pdf
@operation.route("cetakkartu/pdf/<int:client_id>/<string:year>")
@login_required
def cetak_kartu(client_id, year):
    #     # query data inisial untuk pemuatan halaman
    client = Client.query.filter_by(id=client_id).first()
    client = Client.query.filter_by(id=client_id).first()
    deadline_pembayaran = client.deadline_pembayaran
    year_object = Year.query.filter_by(year_name=year).first()
    payment_data = PaymentData.query.filter_by(
        payer=client.id, paid_year=year_object.id
    ).all()
    year_list = Year.query.all()
    staff_list = Staff.query.all()
    month_in_year = Month.query.filter_by(year_id=year_object.id).all()
    monthly_payment_date = []

    # populasi list monthly_payment_data dengan data tanggal pembayaran
    for num in range(12):
        the_month = PaymentData.query.filter_by(
            payer=client.id, paid_year=year_object.id, paid_month=month_in_year[num].id
        ).first()
        monthly_payment_date.append(the_month.date_paid)

    rendered = render_template(
        "cetakkartu.html",
        client=client,
        year=year,
        year_list=year_list,
        months=month_in_year,
        month_payment_data=zip(payment_data, month_in_year, monthly_payment_date),
        staff_list=staff_list,
        deadline_pembayaran=deadline_pembayaran,
    )

    # NOTE silahkan ubah sesuai kebutuhan server deployment
    if os.name == "nt":
        pdf = pdfkit.from_string(
            rendered,
            False,
            configuration=pdfkit_config,
            options={"enable-local-file-access": ""},
            css=css,
        )
    elif os.name == "posix":
        pdf = pdfkit.from_string(
            rendered,
            False,
            configuration=pdfkit_config,
            css=css,
        )

    pdf_title = format_pdf_title(
        f"{client.first_name}_{client.last_name}_({client.call_name})_{year}"
    )
    response = make_response(pdf)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f"inline; filename={pdf_title}.pdf"

    return response


# cetak kuitansi pdf
@operation.route("cetakkuitansi/pdf/<int:client_id>/<string:year>/<int:kuitansi_id>")
@login_required
def cetak_kuitansi(client_id, year, kuitansi_id):
    # query data inisial untuk pemuatan halaman
    client = Client.query.filter_by(id=client_id).first()
    kuitansi = PaymentData.query.filter_by(id=kuitansi_id).first()
    client = Client.query.filter_by(id=client_id).first()
    year_object = Year.query.filter_by(year_name=year).first()
    payment_data = PaymentData.query.filter_by(
        payer=client.id, paid_year=year_object.id
    ).all()
    year_list = Year.query.all()
    staff_list = Staff.query.all()
    month_in_year = Month.query.filter_by(year_id=year_object.id).all()
    monthly_payment_date = []
    kuitansi = PaymentData.query.filter_by(id=kuitansi_id).first()

    # populasi list monthly_payment_data dengan data tanggal pembayaran
    for num in range(12):
        the_month = PaymentData.query.filter_by(
            payer=client.id, paid_year=year_object.id, paid_month=month_in_year[num].id
        ).first()
        monthly_payment_date.append(the_month.date_paid)

    if not kuitansi.isPaid:
        flash("Pembayaran belum lunas.", category="error")
        return redirect(
            url_for("views.display_data_pembayaran", client_id=client_id, year=year)
        )

    rendered = render_template(
        "cetakkuitansi.html",
        client=client,
        year=year,
        year_list=year_list,
        kuitansi=kuitansi,
        months=month_in_year,
        month_payment_data=zip(payment_data, month_in_year, monthly_payment_date),
        staff_list=staff_list,
    )

    # NOTE silahkan ubah sesuai kebutuhan server deployment
    if os.name == "nt":
        pdf = pdfkit.from_string(
            rendered,
            False,
            configuration=pdfkit_config,
            options={"enable-local-file-access": ""},
            css=css,
        )
    elif os.name == "posix":
        pdf = pdfkit.from_string(
            rendered,
            False,
            configuration=pdfkit_config,
            css=css,
        )

    pdf_title = format_pdf_title(
        f"{client.first_name}_{client.last_name}_({client.call_name})_{year}"
    )
    print(pdf_title)
    response = make_response(pdf)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f"inline; filename={pdf_title}.pdf"

    return response

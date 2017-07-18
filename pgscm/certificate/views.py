from flask import render_template
from . import certificate
from flask_security import roles_accepted
import datetime


class Certificate:
    def __init__(self, certificate_id, certificate_name, active_date,
                 group_area, status, owner_group):
        self.certificate_id = certificate_id
        self.certificate_name = certificate_name
        self.active_date = active_date
        self.group_area = group_area
        self.status = status
        self.owner_group = owner_group


@certificate.route('/vi/chung-chi', endpoint='index_vi')
@certificate.route('/en/certificates', endpoint='index_en')
@roles_accepted('national_admin', 'national_moderator', 'national_user')
def index():
    sample_certificate = Certificate(11, 'certificate smp',
                                     datetime.date(2015, 8, 23),
                                     100, "OK", "Group 1")
    result_certificates = []
    for i in range(1, 30):
        result_certificates.append(sample_certificate)
    return render_template('certificate/index.html',
                           certificates=result_certificates)


@certificate.route('/vi/chung-chi/chi-tiet/<string:certificate_id>',
                   endpoint='details_vi')
@certificate.route('/en/certificates/details/<string:certificate_id>',
                   endpoint='details_en')
@roles_accepted('national_admin', 'national_moderator', 'national_user')
def details(certificate_id):
    sample_certificate = Certificate(11, 'certificate smp',
                                     datetime.date(2015, 8, 23), 100,
                                     "OK", "Group 1")
    result_certificates = []
    for i in range(1, 30):
        result_certificates.append(sample_certificate)
    return render_template('certificate/details.html',
                           certificates=result_certificates)


@certificate.route('/vi/chung-chi/tim-kiem',
                   endpoint='advance_search_vi')
@certificate.route('/en/certificates/advance_search',
                   endpoint='advance_search_en')
@roles_accepted('national_admin', 'national_moderator', 'national_user')
def advance_search():
    sample_certificate = Certificate(11, 'certificate smp',
                                     datetime.date(2015, 8, 23), 100, "OK",
                                     "Group 1")
    result_certificates = []
    for i in range(1, 30):
        result_certificates.append(sample_certificate)
    return render_template('certificate/advance_search.html',
                           certificates=result_certificates)

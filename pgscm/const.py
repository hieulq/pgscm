from enum import IntEnum

N_ADMIN = 'national_admin'
N_MOD = 'national_moderator'
N_USER = 'national_user'
R_ADMIN = 'regional_admin'
R_MOD = 'regional_moderator'
R_USER = 'regional_user'


class GenderType(IntEnum):
    male = 0  # nam
    female = 1  # nu


class FarmerType(IntEnum):
    member = 0  # thanh vien
    reviewer = 1  # thanh tra


class CertificateStatusType(IntEnum):
    approve = 0  # dong y cap
    reject = 1  # tu choi cap
    not_check = 2  # chua xac nhan
    approve_no_cert = 3  # khong co chung chi


class CertificateReVerifyStatusType(IntEnum):
    not_check = 0  # chua thanh tra
    valid = 1  # ok
    decline = 2  # thu hoi
    warning = 3  # canh cao
    punish = 4  # dinh chi, xu phat

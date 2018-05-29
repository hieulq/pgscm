from enum import IntEnum

N_ADMIN = 'national_admin'
N_MOD = 'national_moderator'
N_USER = 'national_user'
R_ADMIN = 'regional_admin'
R_MOD = 'regional_moderator'
R_USER = 'regional_user'
C_USER = 'customer_user'
ALL_ROLES = [N_ADMIN, N_MOD, N_USER, R_ADMIN, R_MOD, R_USER]
ONLY_ADMIN_ROLE = [N_ADMIN, R_ADMIN]
ADMIN_MOD_ROLE = [N_ADMIN, R_ADMIN, N_MOD, R_MOD]
NATION_ROLE = [N_ADMIN, N_MOD, N_USER]
CUSTOMER_ROLE = [C_USER]


PAGE_HAVE_SOFT_DELETE = ['associate_group', 'group', 'farmer',
                         'certificate/farmers', 'certificate/groups']

MODAL_ADD_ID = 'modal-add'
MODAL_DEL_ID = 'modal-delete'
MODAL_EDIT_ID = 'modal-edit'
MODAL_HISTORY_ID = 'modal-history'
TAB_CERTIFICATE_ID = 'tab-certificate'
MODAL_DETAIL_ID = 'modal-detail'
BTNADD_ID = 'addBtn'
BTNEDIT_ID = 'editBtn'
BTNDEL_ID = 'delBtn'
BTNVIEW_ID = 'viewBtn'
BTNHISTORY_ID = 'historyBtn'

SELECT_DEFAULT_ID = 'pgs_select'

MULTI_SELECT_DEFAULT_CLASS = 'pgs_multi_select'

SUBMIT_DEFAULT_CLASS = 'pgs_submit'

DEL_SUBMIT_ID = 'pgs_del_submit'

BOLD_DISP = 'bold'
LINK_DISP = 'link'

DATETIME_SCHEMA = {
    "anyOf": [
        {"type": ["string", "null"], "format": "date"},
        {"type": "array",
         "items": {
             "anyOf": [
                 {"type": ["string", "null"], "format": "date"}
             ]
         }}
    ]}


class GenderType(IntEnum):
    male = 1  # nam
    female = 2  # nu


class FarmerType(IntEnum):
    member = 1  # thanh vien
    reviewer = 2  # thanh tra
    leader = 3  # truong nhom
    deputy_leader = 4  # pho nhom
    counter = 5  # ke toan


class CertificateStatusType(IntEnum):   # inspection
    approved = 1  # phe chuan
    rejected = 2  # tu choi cap (refuse)
    decline = 3  # thu hoi      (withdraw)
    warning = 4  # canh cao
    punish = 5  # phat


class CertificateReVerifyStatusType(IntEnum):   # decision
    adding = 1  # cap moi (new)
    keeping = 2  # duy tri (remaining)
    converting = 3  # dang chuyen doi (conversion)
    fortuity = 4  # dot xuat (suddenly)

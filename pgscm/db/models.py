from flask_security import UserMixin, RoleMixin
from pgscm import sqla, login_manager
import enum


class GenderType(enum.Enum):
    male = 0  # nam
    female = 1  # nu


class FarmerType(enum.Enum):
    member = 0  # thanh vien
    reviewer = 1  # thanh tra


class CertificateStateType(enum.Enum):
    valid = 0  # hop le
    invalid = 1  # thu hoi do vi pham
    checking = 2  # dang xem xet


class CertificateReVerifyStateType(enum.Enum):
    not_check = 0  # chua thanh tra
    ok = 1  # ok
    warning = 2  # Canh cao


# Create a table to support a many-to-many relationship between Users and Roles

roles_users = sqla.Table(
    'roles_users',
    sqla.Column('user_id', sqla.String(64), sqla.ForeignKey('user.id')),
    sqla.Column('role_id', sqla.String(64), sqla.ForeignKey('role.id'))
)


class Role(sqla.Model, RoleMixin):
    __tablename__ = 'role'
    id = sqla.Column(sqla.String(64), primary_key=True)
    name = sqla.Column(sqla.String(80), unique=True)
    description = sqla.Column(sqla.String(255))

    def __repr__(self):
        return '<Role %r>' % self.name


class User(sqla.Model, UserMixin):
    __tablename__ = 'user'
    id = sqla.Column(sqla.String(64), primary_key=True)
    email = sqla.Column(sqla.String(64), unique=True, index=True)
    fullname = sqla.Column(sqla.String(64), unique=True, index=True)
    roles = sqla.relationship('Role', secondary=roles_users,
                              backref=sqla.backref('user', lazy='dynamic'))
    region_id = sqla.Column(sqla.String(64), sqla.ForeignKey('region.id'), nullable=True)
    region = sqla.relationship('Region', back_populates='users')

    active = sqla.Column(sqla.Boolean())
    password = sqla.Column(sqla.String(255))
    last_login_at = sqla.Column(sqla.DateTime())
    current_login_at = sqla.Column(sqla.DateTime())
    last_login_ip = sqla.Column(sqla.String(50))
    current_login_ip = sqla.Column(sqla.String(50))
    login_count = sqla.Column(sqla.Integer())
    avatar = '/static/img/pgs-160x160.jpg'

    def __repr__(self):
        return '<User %r >' % self.fullname


class Region(sqla.Model):
    __tablename__ = 'region'
    id = sqla.Column(sqla.String(64), primary_key=True)

    region_code = sqla.Column(sqla.String(64))  # ma vung
    name = sqla.Column(sqla.String(64))
    description = sqla.Column(sqla.String(255))
    users = sqla.relationship('User', back_populates='region')
    associate_groups = sqla.relationship('AssociateGroup', back_populates='region')
    groups = sqla.relationship('Group', back_populates='region')
    __table_args__ = (sqla.Index('region_code_index', "region_code"),)


class AssociateGroup(sqla.Model):
    __tablename = 'associate_group'
    id = sqla.Column(sqla.String(64), primary_key=True)

    associate_group_code = sqla.Column(sqla.String(64))
    name = sqla.Column(sqla.String(80))
    email = sqla.Column(sqla.String(80))

    region_id = sqla.Column(sqla.String(64), sqla.ForeignKey('region.id'))
    region = sqla.relationship('Region', back_populates='associate_groups')

    groups = sqla.relationship('Group', back_populates='associate_group')

    deleted_at = sqla.Column(sqla.DateTime())
    modify_info = sqla.Column(sqla.String(255))
    __table_args__ = (sqla.Index('a_group_code_index', 'associate_group_code', "deleted_at"),)


class Group(sqla.Model):
    __tablename = 'group'
    id = sqla.Column(sqla.String(64), primary_key=True)

    group_code = sqla.Column(sqla.String(64))
    name = sqla.Column(sqla.String(80))
    address = sqla.Column(sqla.String(255))

    associate_group_id = sqla.Column(
        sqla.String(64), sqla.ForeignKey('associate_group.id'), nullable=True)
    associate_group = sqla.relationship('AssociateGroup', back_populates='groups')

    region_id = sqla.Column(sqla.String(64), sqla.ForeignKey('region.id'), nullable=True)
    region = sqla.relationship('Region', back_populates='groups')

    farmers = sqla.relationship('Farmer', back_populates='group')

    deleted_at = sqla.Column(sqla.DateTime())
    modify_info = sqla.Column(sqla.String(255))

    certificates = sqla.relationship('Certificate', back_populates='owner_group')
    __table_args__ = (sqla.Index('group_code_index', 'group_code', "deleted_at"),)


class Farmer(sqla.Model):
    id = sqla.Column(sqla.String(64), primary_key=True)

    farmer_code = sqla.Column(sqla.String(64))
    name = sqla.Column(sqla.String(80))
    gender = sqla.Column(sqla.Enum(GenderType))
    type = sqla.Column(sqla.Enum(FarmerType))

    group_id = sqla.Column(sqla.String(64), sqla.ForeignKey('group.id'), nullable=True)
    group = sqla.relationship('Group', back_populates='farmers')

    deleted_at = sqla.Column(sqla.DateTime())
    modify_info = sqla.Column(sqla.String(255))
    __table_args__ = (sqla.Index('farmer_code_index', 'farmer_code', "deleted_at"),)


class Certificate(sqla.Model):
    id = sqla.Column(sqla.String(64), primary_key=True)

    certificate_code = sqla.Column(sqla.String(64))
    owner_group_id = sqla.Column(sqla.String(64), sqla.ForeignKey('group.id'), nullable=True)
    owner_group = sqla.relationship('Group', back_populates='certificates')

    group_area = sqla.Column(sqla.String(64))
    certificate_start_date = sqla.Column(sqla.DateTime())
    gov_certificate_id = sqla.Column(sqla.String(64))
    certificate_expiry_date = sqla.Column(sqla.DateTime())
    state = sqla.Column(sqla.Enum(CertificateStateType))

    re_verify_state = sqla.Column(sqla.Enum(CertificateReVerifyStateType))

    deleted_at = sqla.Column(sqla.DateTime())
    modify_info = sqla.Column(sqla.String(255))
    __table_args__ = (sqla.Index('certificate_code_index', 'certificate_code', "deleted_at"),)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(str(user_id))

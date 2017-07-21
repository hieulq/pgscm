import uuid

from flask_security import UserMixin, RoleMixin

from pgscm import sqla, login_manager, const

# Create a table to support a many-to-many relationship between Users and Roles

roles_users = sqla.Table(
    'roles_users',
    sqla.Column('user_id', sqla.String(64), sqla.ForeignKey('user.id')),
    sqla.Column('role_id', sqla.String(64), sqla.ForeignKey('role.id'))
)


class Role(sqla.Model, RoleMixin):
    __tablename__ = 'role'
    id = sqla.Column(sqla.String(64), primary_key=True,
                     default=lambda: str(uuid.uuid4()))
    name = sqla.Column(sqla.String(80), unique=True)
    description = sqla.Column(sqla.String(255))

    def __repr__(self):
        return '<Role %r>' % self.name


class User(sqla.Model, UserMixin):
    __tablename__ = 'user'
    id = sqla.Column(sqla.String(64), primary_key=True,
                     default=lambda: str(uuid.uuid4()))
    email = sqla.Column(sqla.String(64), unique=True, index=True)
    fullname = sqla.Column(sqla.String(64), unique=True, index=True)
    roles = sqla.relationship('Role', secondary=roles_users,
                              backref=sqla.backref('user', lazy='dynamic'))
    province_id = sqla.Column(sqla.String(64), sqla.ForeignKey(
        'province.province_id'), nullable=True)
    province = sqla.relationship('Province', back_populates='users')

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


class AssociateGroup(sqla.Model):
    __tablename = 'associate_group'
    id = sqla.Column(sqla.String(64), primary_key=True,
                     default=lambda: str(uuid.uuid4()))
    associate_group_code = sqla.Column(sqla.String(64))

    name = sqla.Column(sqla.String(80))
    email = sqla.Column(sqla.String(80))

    province_id = sqla.Column(sqla.String(64), sqla.ForeignKey(
        'province.province_id'))
    province = sqla.relationship('Province', back_populates='associate_groups')

    groups = sqla.relationship('Group', back_populates='associate_group')

    deleted_at = sqla.Column(sqla.DateTime())
    modify_info = sqla.Column(sqla.String(255))
    __table_args__ = (sqla.Index('a_group_code_index', 'associate_group_code',
                                 "deleted_at"),)


class Group(sqla.Model):
    __tablename = 'group'
    id = sqla.Column(sqla.String(64), primary_key=True,
                     default=lambda: str(uuid.uuid4()))
    group_code = sqla.Column(sqla.String(64))
    name = sqla.Column(sqla.String(80))

    village = sqla.Column(sqla.String(64))  # lang, thon
    ward_id = sqla.Column(sqla.String(64),
                          sqla.ForeignKey('ward.ward_id'),
                          nullable=True, index=True)  # xa, phuong, thi tran
    ward = sqla.relationship('Ward', back_populates='groups')
    district_id = sqla.Column(sqla.String(64),
                              sqla.ForeignKey('district.district_id'),
                              nullable=True, index=True)  # huyen, thi xa
    district = sqla.relationship('District', back_populates='groups')

    associate_group_id = sqla.Column(
        sqla.String(64), sqla.ForeignKey('associate_group.id'), nullable=True)
    associate_group = sqla.relationship('AssociateGroup',
                                        back_populates='groups')

    province_id = sqla.Column(sqla.String(64),
                              sqla.ForeignKey('province.province_id'),
                              nullable=True, index=True)
    province = sqla.relationship('Province', back_populates='groups')

    farmers = sqla.relationship('Farmer', back_populates='group')

    deleted_at = sqla.Column(sqla.DateTime())
    modify_info = sqla.Column(sqla.String(255))

    certificates = sqla.relationship('Certificate',
                                     back_populates='owner_group')
    __table_args__ = (
        sqla.Index('group_code_index', 'group_code', "deleted_at"),)


class Farmer(sqla.Model):
    __tablename__ = 'farmer'

    id = sqla.Column(sqla.String(64), primary_key=True,
                     default=lambda: str(uuid.uuid4()))
    farmer_code = sqla.Column(sqla.String(64))
    name = sqla.Column(sqla.String(80), nullable=False)
    gender = sqla.Column(sqla.Enum(const.GenderType), nullable=False)
    type = sqla.Column(sqla.Enum(const.FarmerType))

    group_id = sqla.Column(sqla.String(64), sqla.ForeignKey('group.id'),
                           nullable=True)
    group = sqla.relationship('Group', back_populates='farmers')
    certificates = sqla.relationship('Certificate',
                                    back_populates='owner_farmer')

    deleted_at = sqla.Column(sqla.DateTime())
    modify_info = sqla.Column(sqla.String(255))
    __table_args__ = (
        sqla.Index('farmer_code_index', 'farmer_code', "deleted_at"),)


class Certificate(sqla.Model):
    __tablename__ = 'certificate'
    id = sqla.Column(sqla.String(64), primary_key=True,
                     default=lambda: str(uuid.uuid4()))
    certificate_code = sqla.Column(sqla.String(64))
    owner_group_id = sqla.Column(sqla.String(64), sqla.ForeignKey('group.id'),
                                 nullable=True)
    owner_farmer_id = sqla.Column(sqla.String(64),
                                  sqla.ForeignKey('farmer.id'), nullable=True)
    owner_group = sqla.relationship('Group', back_populates='certificates')
    owner_farmer = sqla.relationship('Farmer', back_populates='certificates')

    group_area = sqla.Column(sqla.Integer(), nullable=False, default=0)
    member_count = sqla.Column(sqla.Integer(), nullable=False, default=0)
    certificate_start_date = sqla.Column(sqla.Date(), nullable=True)
    gov_certificate_id = sqla.Column(sqla.String(64), nullable=True)
    certificate_expiry_date = sqla.Column(sqla.Date())
    status = sqla.Column(sqla.Enum(const.CertificateStatusType))

    re_verify_status = sqla.Column(
        sqla.Enum(const.CertificateReVerifyStatusType))

    deleted_at = sqla.Column(sqla.DateTime())
    modify_info = sqla.Column(sqla.String(255))
    __table_args__ = (
        sqla.Index('certificate_code_index', 'certificate_code',
                   "deleted_at"),)


class Ward(sqla.Model):
    __tablename__ = 'ward'
    ward_id = sqla.Column(sqla.String(64), primary_key=True,
                          default=lambda: str(uuid.uuid4()))
    name = sqla.Column(sqla.String(100), nullable=False, index=True)
    type = sqla.Column(sqla.String(100), nullable=False)
    location = sqla.Column(sqla.String(100), nullable=False)
    district_id = sqla.Column(sqla.String(100),
                              sqla.ForeignKey('district.district_id'),
                              nullable=False, index=True)
    district = sqla.relationship('District', back_populates='wards')
    groups = sqla.relationship('Group', back_populates='ward')


class District(sqla.Model):
    __tablename__ = 'district'
    district_id = sqla.Column(sqla.String(64), primary_key=True,
                              default=lambda: str(uuid.uuid4()))
    name = sqla.Column(sqla.String(100), nullable=False, index=True)
    type = sqla.Column(sqla.String(30), nullable=False)
    location = sqla.Column(sqla.String(30), nullable=False)
    province_id = sqla.Column(sqla.String(64),
                              sqla.ForeignKey('province.province_id'),
                              nullable=False, index=True)
    province = sqla.relationship('Province', back_populates='districts')
    wards = sqla.relationship('Ward', back_populates='district')
    groups = sqla.relationship('Group', back_populates='district')


class Province(sqla.Model):
    __tablename__ = 'province'
    province_id = sqla.Column(sqla.String(64), primary_key=True,
                              default=lambda: str(uuid.uuid4()))
    name = sqla.Column(sqla.String(100), nullable=False, index=True)
    type = sqla.Column(sqla.String(30), nullable=False)
    districts = sqla.relationship('District', back_populates='province')
    groups = sqla.relationship('Group', back_populates='province')
    associate_groups = sqla.relationship('AssociateGroup',
                                         back_populates='province')
    users = sqla.relationship('User', back_populates='province')


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(str(user_id))

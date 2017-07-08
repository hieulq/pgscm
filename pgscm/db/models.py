from flask_security import UserMixin, RoleMixin
from pgscm import sqla, login_manager

# Create a table to support a many-to-many relationship between Users and Roles
roles_users = sqla.Table(
    'roles_users',
    sqla.Column('user_id', sqla.Integer(), sqla.ForeignKey('user.id')),
    sqla.Column('role_id', sqla.Integer(), sqla.ForeignKey('role.id'))
)


class Role(sqla.Model, RoleMixin):
    __tablename__ = 'role'
    id = sqla.Column(sqla.Integer(), primary_key=True)
    name = sqla.Column(sqla.String(80), unique=True)
    description = sqla.Column(sqla.String(255))

    def __repr__(self):
        return '<Role %r>' % self.name


class User(sqla.Model, UserMixin):
    __tablename__ = 'user'
    id = sqla.Column(sqla.Integer(), primary_key=True)
    email = sqla.Column(sqla.String(64), unique=True, index=True)
    fullname = sqla.Column(sqla.String(64), unique=True, index=True)
    roles = sqla.relationship('Role', secondary=roles_users,
                              backref=sqla.backref('user', lazy='dynamic'))
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


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

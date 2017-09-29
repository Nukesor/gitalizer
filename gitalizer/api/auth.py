"""User auth things such as login and registering."""
from webargs.flaskparser import use_args

from gitalizer.api import api
from gitalizer.extensions import db
from gitalizer.models.user import User
from gitalizer.schemas.user import UserSchema
from gitalizer.helpers.decorators import login_exempt
from gitalizer.responses import ok, conflict, created, unauthorized


@api.route('/auth/login', methods=['POST'])
@login_exempt
@use_args(UserSchema())
def login(args):
    """Log the user in and return a response with an auth token.

    Return UNAUTHORIZED in case the user can't be found or if the password is incorrect.
    """
    user = db.session.query(User).filter_by(email=args['email']).first()

    # For privacy reasons, we'll not provide the exact reason for failure here.
    if not user:
        return unauthorized("Username or password incorrect.")
    if not user.verify_password(args['password']):
        return unauthorized("Username or password incorrect.")

    if user.has_valid_auth_token:
        token = user.current_auth_token
    else:
        token = user.generate_auth_token()

    return ok(data={"token": token})


@api.route('/auth/register', methods=['POST'])
@login_exempt
@use_args(UserSchema())
def register(args):
    """Register a new user using email and password.

    Return CONFLICT is a user with the same email already exists.
    """
    if db.session.query(User).filter_by(email=args['email']).first():
        return conflict("User already exists.")

    new_user = User(args['email'], args['password'])
    db.session.add(new_user)
    db.session.commit()

    user_schema = UserSchema()

    return created(data=user_schema.dump(new_user).data)

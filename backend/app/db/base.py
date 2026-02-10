from sqlalchemy.orm import declarative_base


Base = declarative_base()

# Import models so they are registered with SQLAlchemy metadata.
from app import models  # noqa: E402,F401

"""Create all tables in the database"""

from models import Base

from database import engine


if __name__ == "__main__":
    Base.metadata.create_all(engine)
    print("Tables created.")
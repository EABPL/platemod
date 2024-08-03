from .session import engine, Base
from .models import Plate

def init_db():
    Base.metadata.create_all(bind=engine)
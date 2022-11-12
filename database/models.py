from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, JSON
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import relationship

from .database import Base


class Game(Base):
    __tablename__ = "games"
    id = Column(Integer, primary_key=True, index=True)
    last_move_was_x = Column(Boolean, default=False)
    info = Column(MutableDict.as_mutable(JSON))




from sqlalchemy import Column, BigInteger, Numeric
from bot.helpers.sql_helper import SESSION, BASE

class Bandwidth(BASE):
    __tablename__ = "Bandwidth"
    id = Column(Numeric, primary_key=True)
    inbound = Column(BigInteger, default=0)
    outbound = Column(BigInteger, default=0)

    def __init__(self, id, inbound=0, outbound=0):
        self.id = id
        self.inbound = inbound
        self.outbound = outbound

Bandwidth.__table__.create(checkfirst=True)

def get_bandwidth():
    try:
        bw = SESSION.query(Bandwidth).filter(Bandwidth.id == 1).first()
        if bw:
            return bw.inbound, bw.outbound
        else:
            bw = Bandwidth(1, 0, 0)
            SESSION.add(bw)
            SESSION.commit()
            return 0, 0
    except:
        SESSION.rollback()
        return 0, 0
    finally:
        SESSION.close()

def add_inbound(size):
    try:
        bw = SESSION.query(Bandwidth).filter(Bandwidth.id == 1).first()
        if bw:
            bw.inbound = Bandwidth.inbound + size
        else:
            bw = Bandwidth(1, size, 0)
        SESSION.add(bw)
        SESSION.commit()
    except:
        SESSION.rollback()
    finally:
        SESSION.close()

def add_outbound(size):
    try:
        bw = SESSION.query(Bandwidth).filter(Bandwidth.id == 1).first()
        if bw:
            bw.outbound = Bandwidth.outbound + size
        else:
            bw = Bandwidth(1, 0, size)
        SESSION.add(bw)
        SESSION.commit()
    except:
        SESSION.rollback()
    finally:
        SESSION.close()

# db functions

from sqlalchemy.exc import NoResultFound
from sqlmodel import Session, SQLModel, create_engine, select

from .settings import DATABASE_URL, SQL_ECHO

engine = create_engine(DATABASE_URL, echo=SQL_ECHO, connect_args=dict(check_same_thread=False))


def init_db():
    SQLModel.metadata.create_all(engine)


def get_db():
    with Session(engine) as session:
        with CRUD(session) as db:
            yield db


class CRUD:
    def __init__(self, session):
        self.session = session

    def __enter__(self):
        return self

    def __exit__(self, _, exc, tb):
        self.session = None

    def create(self, record):
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return record

    def read_one(self, table, *where, allow_none=False):
        return self.read(table, *where, one=True, allow_none=allow_none)

    def read_all(self, table, *where, allow_none=False):
        return self.read(table, *where, one=False, allow_none=allow_none)

    def read(self, table, *where, one=None, allow_none=False):
        if len(where):
            statement = select(table).where(*where)
            results = self.session.exec(statement)
        else:
            results = self.session.exec(select(table))
        try:
            if one:
                return results.one()
            else:
                return results.all()
        except NoResultFound as exc:
            if allow_none:
                if one:
                    return None
                else:
                    return []
            raise exc from exc

    def upsert(self, record):
        return self.update(record, allow_none=True)

    def update(self, record, allow_none=False):
        if record.id is not None:
            table = record.__class__
            _record = self.read_one(table, table.id == record.id, allow_none=allow_none)
            if _record:
                record.id = _record.id
        return self.create(record)

    def delete(self, record, *where, allow_none=False):
        if len(where):
            table = record
            records = self.read_all(table, *where, allow_none=allow_none)
        else:
            records = [record]
        count = 0
        for record in records:
            self.session.delete(record)
            self.session.commit()
            count += 1
        return count

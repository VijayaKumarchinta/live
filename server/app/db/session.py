from sqlalchemy.orm import sessionmaker
from app.db.engine import reader_engine, writer_engine

WriterSession = sessionmaker(bind=writer_engine, autoflush=False, expire_on_commit=False)
ReaderSession = sessionmaker(bind=reader_engine, autoflush=False, expire_on_commit=False)

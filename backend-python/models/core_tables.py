# models/core_tables.py
from sqlalchemy import Table, Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from extensions import data_metadata as metadata

# Définition des tables avec SQLAlchemy Core
categories = Table('categories', metadata,
    Column('id', Integer, primary_key=True),
    Column('nom', String(255), nullable=False),
    Column('description', Text),
    Column('date_creation', DateTime),
    Column('entreprise_id', Integer, ForeignKey('entreprises.id')),
    extend_existing=True
)

users = Table('users', metadata,
    Column('id', Integer, primary_key=True),
    Column('nom', String(255), nullable=False),
    Column('email', String(255), unique=True, nullable=False),
    Column('password', String(255), nullable=False),
    Column('role', String(50), nullable=False),
    Column('actif', Boolean, default=True),
    Column('telephone', String(20)),
    Column('date_inscription', DateTime),
    Column('entreprise_id', Integer, ForeignKey('entreprises.id')),
    extend_existing=True
)

# Ajouter d'autres tables selon les besoins
# documents = Table('documents', metadata, ...)
# entreprises = Table('entreprises', metadata, ...)
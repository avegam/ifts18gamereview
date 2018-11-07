import sys
import datetime
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class Consola(Base):
	__tablename__ = 'consola'
	
	id = Column(Integer, primary_key=True)
	nombre_consola = Column(String(50), nullable=False)
	
class Genero(Base):
	__tablename__ = 'genero'
	
	id = Column(Integer, primary_key=True)
	nombre_genero = Column(String(50), nullable=False)	
	
class User(Base):
	__tablename__ = 'user'

	id = Column(Integer, primary_key=True)
	username = Column(String(50), nullable=False)
	email = Column(String(250), nullable=False)
	pw_hash = Column(String(250), nullable=False)
	fecha_creacion = Column(DateTime, nullable=False)
	
class Reviewjuego(Base):
	__tablename__ = 'review'

	id = Column(Integer, primary_key=True)
	puntaje = Column(String(4),nullable=False)
	titulo = Column(String(50), nullable=False)
	portada = Column(String(50), nullable=False)
	contenido = Column(String(250), nullable=False)
	fecha_creacion = Column(DateTime, nullable=False)
	id_consola = Column(Integer, ForeignKey("consola.id"))
	consola = relationship(Consola)
	id_autor = Column(Integer, ForeignKey("user.id"))
	user = relationship(User)	
	

class Generos(Base):
	__tablename__ = 'generos'
	
	id = Column(Integer, primary_key=True)
	id_genero = Column(Integer, ForeignKey("genero.id"))
	generos = relationship(Genero)
	id_juego = Column(Integer, ForeignKey("review.id"))
	review = relationship(Reviewjuego)	


class Blog(Base):
	__tablename__ = 'blog'

	id = Column(Integer, primary_key=True)
	titulo = Column(String(50), nullable=False)
	contenido = Column(String(250), nullable=False)
	fecha_creacion = Column(DateTime, nullable=False)
	id_juego = Column(Integer, ForeignKey("review.id"))
	review = relationship(Reviewjuego)
	id_autor = Column(Integer, ForeignKey("user.id"))
	user = relationship(User)
	
class Imagenes(Base):
	__tablename__ = 'imagenes'

	id = Column(Integer, primary_key=True)
	Direccion = Column(String(50), nullable=False)
	id_juego = Column(Integer, ForeignKey("review.id"))
	review = relationship(Reviewjuego)
	
class Puntaje(Base):
	__tablename__ = 'puntajecomunidad'

	id = Column(Integer, primary_key=True)
	puntaje = Column(Integer, nullable=False)
	id_juego = Column(Integer, ForeignKey("review.id"))
	review = relationship(Reviewjuego)
	id_autor = Column(Integer, ForeignKey("user.id"))
	user = relationship(User)




engine = create_engine('sqlite:///blog.db')
Base.metadata.create_all(engine)

from flask import Flask, g, render_template, jsonify, url_for, flash
from flask import request, redirect, make_response
from flask import session as login_session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from functools import wraps
from database_setup import Base, Blog, User,Consola,Genero,Generos,Reviewjuego,Imagenes,Puntaje
from oauth2client.client import flow_from_clientsecrets, FlowExchangeError
import random
import string
import json
import datetime
import hashlib
import httplib2
import requests


# Connect to Database and create database session
engine = create_engine('sqlite:///blog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


def VerConsolas():	

		consolitas = session.query(Consola).all()
		return consolitas


def VerGenero():	

		generito = session.query(Genero).all()
		return generito
def Search():		
			
			if request.form['Search'] == "Busqueda":
				buscar = request.form['Busqueda']
				return redirect(url_for('Verreviewtitu',id = buscar))
				
#fallo por lo mismo que el otro				
def LosGenero(posts):
	list1 = []
	for post in posts:
		idjuego = post.Reviewjuego.id
		print(idjuego)
		generitos = session.query(Genero,Generos).join(Generos,Generos.id_genero == Genero.id).filter(Generos.id_juego == idjuego).all()
		list1.append(list = [post.Reviewjuego.id])
		for gen in generitos:
			list.append(gen.nombre_genero)
	print (list1)
	return list1
		
	
#no funcionan nidea por que
#busqueda por titulo
#def VerSearch(Search):	
#
#		PostSearch = session.query(Reviewjuego,User,Consola).join(User,Reviewjuego.id_autor == User.id).join(Consola,Reviewjuego.id_consola == Consola.id).filter(Reviewjuego.titulo.like(Search)).all()
		

#		return PostSearch

#def VerSearchConsola(Search):	
#		print (Search)
#		PostSearch = session.query(Reviewjuego,User,Consola).join(User,Reviewjuego.id_autor == User.id).join(Consola,Reviewjuego.id_consola == Consola.id).filter(Reviewjuego.id_consola == 1).all()
		

#		return PostSearch

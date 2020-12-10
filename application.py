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
from consulta import VerConsolas,VerGenero,Search,LosGenero#,VerSearch,VerSearchConsola

app = Flask(__name__)

CLIENT_ID = json.loads(
		open('client_secrets.json', 'r').read())['web']['client_id']

# Connect to Database and create database session
engine = create_engine('sqlite:///blog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()
#Consultas Genericas
ConsolasNAV = VerConsolas()
GenerosNAV = VerGenero()

@app.route('/login', methods=['GET', 'POST'])
def login():

	if request.method == 'GET':
		state = ''.join(random.choice(
				string.ascii_uppercase + string.digits) for x in range(32))
		# store it in session for later use
		login_session['state'] = state
		return render_template('login.html', STATE = state,consolas=ConsolasNAV,generos=GenerosNAV)
	else:
		if request.method == 'POST':
			print ("dentro de POST login")
			user = session.query(User).filter_by(
				username = request.form['username']).first()

			if user and valid_pw(request.form['username'],
								request.form['password'],								
								user.pw_hash):
			
				login_session['username'] = request.form['username']				
				return render_template('public.html', username=login_session['username'],consolas=ConsolasNAV,generos=GenerosNAV)

			else:
				error = "Usuario no registrado!!!"
				return render_template('login.html', error = error,consolas=ConsolasNAV,generos=GenerosNAV)
				
# GConnect
@app.route('/gconnect', methods=['POST'])
def gconnect():
	print ("Dentro de GConnect")
		# Validate state token
	if request.args.get('state') != login_session['state']:
		response = make_response(json.dumps('Invalid state parameter.'), 401)
		response.headers['Content-Type'] = 'application/json'
		return response
	# Obtain authorization code, now compatible with Python3
	code = request.data

	try:
			# Upgrade the authorization code into a credentials object
		oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
		oauth_flow.redirect_uri = 'postmessage'
		credentials = oauth_flow.step2_exchange(code)
	except FlowExchangeError:
		response = make_response(
					json.dumps('Failed to upgrade the authorization code.'), 401)
		response.headers['Content-Type'] = 'application/json'
		return response

	# Check that the access token is valid.
	access_token = credentials.access_token
	url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
				 % access_token)
	# Submit request, parse response - Python3 compatible
	h = httplib2.Http()
	result = json.loads(h.request(url, 'GET')[1])

	# If there was an error in the access token info, abort.
	if result.get('error') is not None:
			response = make_response(json.dumps(result.get('error')), 500)
			response.headers['Content-Type'] = 'application/json'
			return response

	# Verify that the access token is used for the intended user.
	gplus_id = credentials.id_token['sub']
	if result['user_id'] != gplus_id:
			response = make_response(
					json.dumps("Token's user ID doesn't match given user ID."), 401)
			response.headers['Content-Type'] = 'application/json'
			return response

	# Verify that the access token is valid for this app.
	if result['issued_to'] != CLIENT_ID:
			response = make_response(
					json.dumps("Token's client ID does not match app's."), 401)
			print ("Token's client ID does not match app's.")
			response.headers['Content-Type'] = 'application/json'
			return response

	stored_credentials = login_session.get('credentials')
	stored_gplus_id = login_session.get('gplus_id')
	if stored_credentials is not None and gplus_id == stored_gplus_id:
			response = make_response(json.dumps('Current user is already connected.'),
																	 200)
			response.headers['Content-Type'] = 'application/json'
			return response

	# Store the access token in the session for later use.
	login_session['access_token'] = credentials.access_token
	login_session['gplus_id'] = gplus_id

	# Get user info
	userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
	params = {'access_token': access_token, 'alt': 'json'}
	answer = requests.get(userinfo_url, params=params)

	data = answer.json()

	login_session['username'] = data['name']
	login_session['picture'] = data['picture']
	login_session['email'] = data['email']

	# user_id = getUserID(login_session['email'])
	# if not user_id:
	# 		user_id = createUser(login_session)

	# login_session['user_id'] = user_id

	output = ''
	output += '<h3>Welcome, '
	output += login_session['username']
	output += '!</h3>'
	output += '<img src="'
	output += login_session['picture']
	output += ' " style = "width: 100px; height: 100px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
	flash("you are now logged in as %s" % login_session['username'])
	print ("done!")
	print ("Usuario " + login_session['username'])
	return output
	

@app.route('/gdisconnect')
def gdisconnect():
				# Only disconnect a connected user.
		access_token = login_session.get('access_token')
		if access_token is None:
				response = make_response(
						json.dumps('Current user not connected.'), 401)
				response.headers['Content-Type'] = 'application/json'
				return response
		url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
		h = httplib2.Http()
		result = h.request(url, 'GET')[0]
		if result['status'] == '200':
				# Reset the user's sesson.
				del login_session['access_token']
				del login_session['gplus_id']
				del login_session['username']
				del login_session['email']
				del login_session['picture']
				response = make_response(json.dumps('Successfully disconnected.'), 200)
				response.headers['Content-Type'] = 'application/json'
				return redirect(url_for('showGenres'))
		else:
				# For whatever reason, the given token was invalid.
				response = make_response(
						json.dumps('Failed to revoke token for given user.', 400))
				response.headers['Content-Type'] = 'application/json'
		return response



		
		
def login_required(f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		if 'username' not in login_session:
			return redirect(url_for('login'))
		return f(*args, **kwargs)
	return decorated_function

	
	
	
def make_salt():
	return ''.join(random.choice(
				string.ascii_uppercase + string.digits) for x in range(32))
		
def make_pw_hash(name, pw, salt = None):
	if not salt:
		salt = make_salt()
	h = hashlib.sha256((name + pw + salt).encode('utf-8')).hexdigest()
	return '%s,%s' % (salt, h)

def valid_pw(name, password, h):
	salt = h.split(',')[0]
	return h == make_pw_hash(name, password, salt)

@app.route('/logout')
def logout():
		
		del login_session['username']

		return render_template('public.html',consolas=ConsolasNAV,generos=GenerosNAV)

# Crear usuario
@app.route('/registrar', methods=['GET', 'POST'])
def registrar():

	if request.method == 'GET':
		return render_template('add-user.html',consolas=ConsolasNAV,generos=GenerosNAV)
	else:
		if request.method == 'POST':
			username = request.form['username']
			password=request.form['password']
			email = request.form['email']
			
			pw_hash = make_pw_hash(username, password)
			nuevoUsuario = User(
					username = username,
					email = email,
					fecha_creacion = datetime.datetime.now(),
					pw_hash=pw_hash) 
			session.add(nuevoUsuario)
			session.commit()
			login_session['username'] = request.form['username']
			return redirect(url_for('showMain'))

# Delete post
@app.route('/blog/eliminar/<int:id>', methods=['GET', 'POST'])
def eliminarItem(id):
	
	post = session.query(Blog).filter_by(id = id).one()

	if request.method == 'GET':
		if 'username' in login_session:
			username = login_session['username']
		return render_template('delete-post.html', post = post, username=login_session['username'],consolas=ConsolasNAV,generos=GenerosNAV)
	else:
		if request.method == 'POST':
			session.delete(post)
			session.commit()
			return redirect(url_for('showMain'))
			
# Delete postrevierw
@app.route('/blogreview/eliminar/<int:id>', methods=['GET', 'POST'])
def eliminarItemrevie(id):

	post = session.query(Reviewjuego,User,Consola).join(User,Reviewjuego.id_autor == User.id).join(Consola,Reviewjuego.id_consola == Consola.id).filter(Reviewjuego.id == id).one()
	postr = session.query(Reviewjuego).filter_by(id = id).one()
	if request.method == 'GET':
		return render_template('delete-review.html', post = post,consolas=ConsolasNAV,generos=GenerosNAV)
	else:
		if request.method == 'POST':
			session.delete(postr)
			session.commit()
			return redirect(url_for('showMain'))
			
# update postrevierw
@app.route('/blogreview/editar/<int:id>', methods=['GET', 'POST'])
def EditarItemrevie(id):	
	if request.method == 'GET':
		post = session.query(Reviewjuego,User,Consola).join(User,Reviewjuego.id_autor == User.id).join(Consola,Reviewjuego.id_consola == Consola.id).filter(Reviewjuego.id == id).one()
		return render_template('Update-review.html', post = post,consolas=ConsolasNAV,generos=GenerosNAV)
	else:
		if request.method == 'POST':
			postr = session.query(Reviewjuego).filter_by(id = id).one()
			postr.titulo = request.form['titulo']
			postr.contenido = request.form['contenido']
			postr.puntaje = request.form['puntaje']
			
			session.commit()
			return redirect(url_for('showMain'))
					 

# Crear Post
@app.route('/agregarPost', methods=['GET', 'POST'])
def agregarPost():

	if request.method == 'GET':
		return render_template('add-post.html',consolas=ConsolasNAV,generos=GenerosNAV)
	else:
		if request.method == 'POST':
			post = Blog(
					titulo = request.form['titulo'],
					contenido=request.form['contenido'],
					fecha_creacion = datetime.datetime.now())
			session.add(post)
			session.commit()
			return redirect(url_for('showMain'))
			
#crear review
@app.route('/agregarreview', methods=['GET', 'POST'])
def agregarPostreview():
	
	if request.method == 'GET':
		if 'username' in login_session:
			username = login_session['username']
			Autor = session.query(User).all()
			idautor = 0
			for user in Autor:
				if username == user.username:
					idautor = user.id
			consola = session.query(Consola).all()
			consolalist = []
			for x in consola:
				consolalist.append([x.id,x.nombre_consola])
			return render_template('add-review.html',username=username,idau=idautor,listaconsola = consolalist,consolas=ConsolasNAV,generos=GenerosNAV)
	else:
		if request.method == 'POST':
			review = Reviewjuego(
					titulo = request.form['titulo'],
					contenido=request.form['contenido'],
					fecha_creacion = datetime.datetime.now(),
					portada = request.form['titulo'],
					puntaje = request.form['puntaje'],
					id_consola = request.form['consola'],
					id_autor = request.form['autor'])
			session.add(review)
			session.commit()
			return redirect(url_for('showMain'))
#crear console
@app.route('/addconsole', methods=['GET', 'POST'])
def addconsol():

	if request.method == 'GET':
		return render_template('add-console.html',consolas=ConsolasNAV,generos=GenerosNAV)
	else:
		if request.method == 'POST':
			consola = request.form['consola']
			
			nuevoConsola = Consola(
					nombre_consola = consola,
					) 
			session.add(nuevoConsola)
			session.commit()
			return redirect(url_for('showMain'))
			
# VER postrevierw
@app.route('/blogreview/View/<int:id>', methods=['GET'])
def Verreview(id):	

		post = session.query(Reviewjuego,User,Consola).join(User,Reviewjuego.id_autor == User.id).join(Consola,Reviewjuego.id_consola == Consola.id).filter(Reviewjuego.id == id).one()
		return render_template('Post.html', post = post,consolas=ConsolasNAV,generos=GenerosNAV)
			
#crear genero
@app.route('/addgenero', methods=['GET', 'POST'])
def addgenero():

	if request.method == 'GET':
		return render_template('add-genero.html',consolas=ConsolasNAV,generos=GenerosNAV)
	else:
		if request.method == 'POST':
			genero = request.form['genero']
			
			nuevoGenero = Genero(
					nombre_genero = genero,
					) 
			session.add(nuevoGenero)
			session.commit()
			return redirect(url_for('showMain'))
# Show all


# Show all
@app.route('/', methods=['GET'])
@app.route('/public/', methods=['GET', 'POST'])
def showMain():
	if request.method == 'GET':
		posts = session.query(Reviewjuego,User,Consola).join(User,Reviewjuego.id_autor == User.id).join(Consola,Reviewjuego.id_consola == Consola.id).all()
		#posts = session.query(Reviewjuego,User).join(User,Reviewjuego.id_autor == User.id).all()
		
		#posts = session.query(Reviewjuego).join(User).all()
		#d = dir(posts)
		#print posts
		if 'username' in login_session:
			username = login_session['username']
			
			return render_template('public.html', posts = posts, username=username,consolas=ConsolasNAV,generos=GenerosNAV)	
		else:
			return render_template('public.html', posts = posts,consolas=ConsolasNAV,generos=GenerosNAV)
	else:
		if request.method == 'POST':
			
			if request.form['Search'] == "Busqueda":
				buscar = request.form['Busqueda']
				return redirect(url_for('Verreviewtitu',id = buscar))


#@app.route('/Search/Titulo/<id>', methods=['GET'])
@app.route('/Search/Titulo/<string:id>', methods=['GET', 'POST'])
def Verreviewtitu(id):
	if request.method == 'GET':
		id = str(id)	
		ID = "%{}%".format(id)
		
		posts = session.query(Reviewjuego,User,Consola).join(User,Reviewjuego.id_autor == User.id).join(Consola,Reviewjuego.id_consola == Consola.id).filter(Reviewjuego.titulo.like(ID)).all()
		
		return render_template('Search.html', posts = posts,consolas=ConsolasNAV,generos=GenerosNAV)
	else:
		return Search()
		
@app.route('/Search/Consola/<int:id>', methods=['GET'])
def searchConsola(id):

	#posts = VerSearchConsola(id)
	posts = session.query(Reviewjuego,User,Consola).join(User,Reviewjuego.id_autor == User.id).join(Consola,Reviewjuego.id_consola == Consola.id).filter(Reviewjuego.id_consola == id).all()
	if 'username' in login_session:
		username = login_session['username']
		
		return render_template('Search.html', posts = posts, username=username,consolas=ConsolasNAV,generos=GenerosNAV)	
	else:
		return render_template('Search.html', posts = posts,consolas=ConsolasNAV,generos=GenerosNAV)
		
@app.route('/Search/Genero/<int:id>', methods=['GET'])
def searchGenero(id):

	#posts = VerSearch(ID)
	posts = session.query(Reviewjuego,User,Consola,Generos).join(User,Reviewjuego.id_autor == User.id).join(Consola,Reviewjuego.id_consola == Consola.id).join(Generos,Reviewjuego.id == Generos.id_juego).filter(Generos.id_genero == id).all()
	
	
	
	
	list1 = []
	for post in posts:
		idjuego = post.Reviewjuego.id
		print(idjuego)
		generitos = session.query(Genero,Generos).join(Generos,Generos.id_genero == Genero.id).filter(Generos.id_juego == idjuego).all()
		list = [idjuego]
		list1.append(list)
		for gen in generitos:
			genes = str(gen.Genero.nombre_genero)
			list.append(genes)
	print (list1)
	#cosa = LosGenero(posts)
	#print (cosa)
	if 'username' in login_session:
		username = login_session['username']
		
		return render_template('Search.html', posts = posts, username=username,listageneros=list1,consolas=ConsolasNAV,generos=GenerosNAV)	
	else:
		return render_template('Search.html', posts = posts,listageneros=list1,consolas=ConsolasNAV,generos=GenerosNAV)
		
		

@app.route('/public/NOP', methods=['GET'])
def showMainda():
	posts = session.query(Blog).all()
	
	if 'username' in login_session:
		username = login_session['username']
		
		return render_template('public.html', posts = posts, username=username,consolas=ConsolasNAV,generos=GenerosNAV)	
	else:
		return render_template('public.html', posts = posts,consolas=ConsolasNAV,generos=GenerosNAV)

if __name__ == '__main__':
	app.secret_key = "secret key"
	app.debug = False
	app.run(host = '0.0.0.0', port = 8000)

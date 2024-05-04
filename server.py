from flask import Flask, render_template, redirect, session, url_for, flash, g, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError, DataRequired, Email, EqualTo, NumberRange
from flask_bcrypt import Bcrypt
from flask_marshmallow import Marshmallow
from werkzeug.utils import secure_filename
import cloudinary
import cloudinary.uploader
import cloudinary.api
import os

db = SQLAlchemy()
app = Flask(__name__)
app.app_context().push()
bcrypt = Bcrypt(app)


CORS(app)

# 'mysql://shady:123@localhost/react.db'
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///react.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY']=os.urandom(32)


db.init_app(app)
ma = Marshmallow(app)



cloudinary.config(
    cloud_name="drnoxkesy",
    api_key="828688123921376",
    api_secret="i0reEJH3AzbvkqP119DjXEzvKa8",
    secure=True,
)



class user(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String(80), nullable=False, unique=True)
  email = db.Column(db.String(100), nullable=False, unique=True)
  password = db.Column(db.String(100), nullable=False)


  def __init__(self, username, email, password):
    self.username = username
    self.email = email
    self.password = password


class Products(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  title = db.Column(db.String(1000), nullable=False)
  description = db.Column(db.String(3000), nullable=False)
  price =  db.Column(db.Float, nullable=False)
  category = db.Column(db.String(80), nullable=False)
  rate = db.Column(db.Float)
  image1 = db.Column(db.String(1000000), nullable=False)
  image2 = db.Column(db.String(1000000))
  image3 = db.Column(db.String(1000000))


  def __init__(self, title, description, price, category, rate, image1, image2, image3):
    self.title = title
    self.description = description
    self.price = price
    self.category = category
    self.rate = rate
    self.image1 = image1
    self.image2 = image2
    self.image3 = image3


#users schema:
class UserSchema(ma.Schema):
  class Meta:
    fields = ('id', 'username', 'email', 'password')

user_schema =  UserSchema()
users_schema = UserSchema(many=True)


#products schema:
class ProductsSchema(ma.Schema):
  class Meta:
    fields = ('id', 'title', 'description', 'price', 'category', 'rate', 'image1', 'image2', 'image3')

product_schema =  ProductsSchema()
products_schema = ProductsSchema(many=True)



@app.before_request
def before_request():

  g.id = None

  if "user_id" in session:
    g.id = session["user_id"]


#==============================================================================================================:
# ===================================> Users API Management Routes <===========================================:
#==============================================================================================================:

#                                   Get all users from database API:

@app.route("/api/get" , methods=["GET"])
def members():

   # get all users
  all_users = user.query.order_by(user.id).all()
  results = users_schema.dump(all_users)

  return jsonify(results)

# =============================================================================================================

#                         Create a new user in the database through an API route:

@app.route('/api/signUp' , methods=['POST'])
def add_user():
  username = request.json['username']
  email = request.json['email']
  password = request.json['password']

  existed_user = user.query.filter_by(username=username).first()

  if existed_user :
    return jsonify({ "message": "User with this username already exists!"}), 409

  hashed_password = bcrypt.generate_password_hash(password)
  new_user = user(username, email, hashed_password)
  db.session.add(new_user)
  db.session.commit()

  session["user_id"] = new_user.id
  return user_schema.jsonify(new_user)


#==============================================================================================================

#                                           login API route:

@app.route('/api/login' , methods=['POST'])
def login():
  username = request.json['username']
  # email = request.json['email']
  password = request.json['password']

  our_user = user.query.filter_by(username=username).first()

  if our_user is None:
    return jsonify({"message":" invalid Username or Password"}), 404

  if not bcrypt.check_password_hash(our_user.password, password):
    return jsonify({"message":"invalid Username or Password"}), 401


  session["user_id"] = our_user.id
  if g.id:
    return jsonify({"session": session["user_id"]})
  return user_schema.jsonify(our_user)


# Singing out API Route:
@app.route('/api/signout' , methods=['POST'])
def sign_out():
  session.clear()
  return jsonify({"message":"You have been signed out."})

# ==============================================================================================================

#                               Updating a user (PUT Request) API route:

@app.route('/api/update/<id>/' , methods=['PUT'])
def update_user(id):
  user_to_update = user.query.get(id)

  username = request.json['username']
  email = request.json['email']
  password = request.json['password']

  user_to_update.username = username
  user_to_update.email = email
  user_to_update.password = password

  db.session.commit()
  return  user_schema.jsonify(user_to_update)




# ==============================================================================================================

#                              Deleting a user (DELETE Request) API route:

@app.route('/api/delete/<id>/' , methods=['DELETE'])
def delete_user(id):
  user_to_delete = user.query.get(id)

  db.session.delete(user_to_delete)
  db.session.commit()

  return user_schema.jsonify(user_to_delete)




#==============================================================================================================:
# =================================> *** Products API Management Routes *** <==================================:
#==============================================================================================================:

#                                     Get all users from database API:

@app.route("/api/getProducts" , methods=["GET"])
def products():

   # get all users
  all_products = Products.query.order_by(Products.id).all()
  print("Raw Products Data:", all_products)

  results = products_schema.dump(all_products)
  print("Serialized Products Data:", results)

  return jsonify(results)


@app.route("/api/getOneProduct/<id>" , methods=["GET"])
def product(id):

  # get all users
  the_product = Products.query.get(id)
  print("Raw Products Data:", the_product)

  results = product_schema.dump(the_product)
  print("Serialized Products Data:", results)

  return jsonify(results)


#==============================================================================================================

#                              Create A New Product (POST Request) API Route:

app.config["IMAGE_UPLOADS"] = "client/public/images"
app.config["ALLOWED_IMAGE_EXTENSIONS"] = ["PNG", "JPG", "JPEG", "WEBP", "AVIF", "GIF", "CSV"]

def allowed_image(filename):
    if not "." in filename:
        return False
    ext = filename.rsplit(".", 1)[1]
    if ext.upper() in app.config["ALLOWED_IMAGE_EXTENSIONS"]:
        return True
    else:
        return False



@app.route('/api/addOneProduct' , methods=['POST'])
def add_one_product():
  title = request.form['title']
  description = request.form['description']
  price = request.form['price']
  category = request.form['category']
  rate = request.form['rate']
  image1 = request.files['image1']
  image2 = request.files['image2']
  image3 = request.files['image3']

  #check for error:
  if image1 and allowed_image(image1.filename):
    result1 = cloudinary.uploader.upload(image1)
  else:
    return jsonify({"message": "please upload a valid image extention"}),400
  if image2 and allowed_image(image2.filename):
    result2 = cloudinary.uploader.upload(image2)
  else:
    return jsonify({"message": "please upload a valid image extention"}),400
  if image3 and allowed_image(image3.filename):
    result3 = cloudinary.uploader.upload(image3)
  else:
    return jsonify({"message": "please upload a valid image extention"}),400

  image1_URL = result1['secure_url']
  image2_URL = result2['secure_url']
  image3_URL = result3['secure_url']

  new_product = Products(title=title, description=description, price=price, category=category, rate=rate, image1=image1_URL, image2=image2_URL, image3=image3_URL)
  try:
    db.session.add(new_product)
    db.session.commit()
    return jsonify({"SuccessMessage": "product has been added successfully!"}), 200
  except:
    return jsonify({"FailurMessage": "Something went wrong, can't add the product!"}), 500


#==============================================================================================================:
#                               Updating a Product (PUT Request) API route:
@app.route('/api/updateProduct/<id>' , methods=['PUT'])
def update_product(id):
  product_to_update = Products.query.get(id)
  product_to_update.title = request.form['title']
  product_to_update.description = request.form['description']
  product_to_update.price = request.form['price']
  product_to_update.category = request.form['category']
  product_to_update.rate = request.form['rate']

  image1 = request.files.get('image1')  # Use get() method to prevent KeyError
  image2 = request.files.get('image2')
  image3 = request.files.get('image3')

  # Check if images are provided
  if image1:
    if allowed_image(image1.filename):
      result1 = cloudinary.uploader.upload(image1)
      image1_URL = result1['secure_url']
      product_to_update.image1 = image1_URL

  if image2:
    if allowed_image(image2.filename):
      result2 = cloudinary.uploader.upload(image2)
      image2_URL = result2['secure_url']
      product_to_update.image2 = image2_URL

  if image3:
    if allowed_image(image3.filename):
      result3 = cloudinary.uploader.upload(image3)
      image3_URL = result3['secure_url']
      product_to_update.image3 = image3_URL

  try:
    db.session.commit()
    return jsonify({"SuccessMessage": "Product has been updated successfully!"}), 200
  except:
    return jsonify({"FailureMessage": "Something went wrong, can't update the product!"}), 500






#==============================================================================================================:

#                               Deleting a Product (DELETE Request) API route:

@app.route('/api/deleteProduct/<id>/' , methods=['DELETE'])
def delete_product(id):
  product_to_delete = user.query.get(id)

  db.session.delete(product_to_delete)
  db.session.commit()

  return product_schema.jsonify(product_to_delete)







if __name__ == "__main__":
  app.run(debug=True)


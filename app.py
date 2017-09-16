
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, jsonify
from flask_restful import reqparse, abort, Api, Resource
from sqlalchemy import desc
from sqlalchemy.ext.declarative import DeclarativeMeta
from datetime import datetime
import calendar

from marshmallow import Schema, fields, pprint
from flask_cors import CORS, cross_origin
from flask_jwt import JWT, jwt_required, current_identity

app = Flask(__name__)
api = Api(app)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///Blog.db"
app.config['SECRET_KEY'] = 'super-secret'

# use the default jwt generation route as login entry
app.config['JWT_AUTH_URL_RULE'] = '/api/blog/login'

db = SQLAlchemy(app)

import models
import json


def verify(username, password):
    user = models.User.query.filter(models.User.username==username, models.User.password==password).first()

    if not (username and password):
        return False
    if user:
        return user
    else:
        return False


def identity(payload):
    userid = payload['identity']
    return {"userid": userid}


jwt = JWT(app, verify, identity)



# use the marshmallow to create custom post serializer
class PostSchema(Schema):
    username = fields.Str()
    id = fields.Int()
    title = fields.Str()
    timestamp = fields.DateTime('%Y-%m-%d %H:%M:%S')
    body = fields.Str()
    category = fields.Str()

# api entry to return the post list
class PostList(Resource):
    def get(self):
        posts = models.Post.query.join(models.User, models.User.id==models.Post.userid).add_columns(models.User.username, models.Post.id, models.Post.title, models.Post.timestamp, models.Post.body, models.Post.category).order_by(desc(models.Post.timestamp)).all()  
        schema = PostSchema(many = True)
        return schema.dump(posts)


# use the marshmallow to create custom comment serializer
class CommentSchema(Schema):
    username = fields.Str()
    body = fields.Str()
    id = fields.Int()
    timestamp = fields.DateTime('%Y-%m-%d %H:%M:%S')
    postId = fields.Int()

# api entry to return the comment list of a specific post
class CommentList(Resource):
    def get(self, postId):
        Comments=models.Comment.query.outerjoin(models.User, models.User.id==models.Comment.userid).filter(models.Comment.postid == postId).add_columns(models.User.username, models.Comment.body, models.Comment.id, models.Comment.timestamp, models.Comment.postid).order_by(desc(models.Comment.timestamp)).all()
        schema = CommentSchema(many = True)
        return schema.dump(Comments)


# use the marshmallow to create custom user serializer
class UserSchema(Schema):
    id = fields.Int()
    username = fields.Str()
    password = fields.Str()


# api entry to register new user
class Register(Resource):
    def post(self):

        parser = reqparse.RequestParser()
        parser.add_argument('username', type=str)
        parser.add_argument('password', type=str)

        args = parser.parse_args()
        userName = args['username']
        passWord = args['password']

        user=models.User.query.filter(models.User.username == userName).all()
        if len(user) != 0:
            return jsonify({
            'status': 'failure',
            'msg': 'username taken!'
            })  
        else:
            newUser = models.User(username = userName
            ,password = passWord)
            db.session.add(newUser)
            db.session.commit()
            return jsonify({
            'status': 'success',
            'msg': 'succeed!'
            })



# api entry to submit new post to blog
class Post(Resource):
    @jwt_required()
    def post(self):

        parser = reqparse.RequestParser()
        parser.add_argument('title', type=str)
        parser.add_argument('category', type=str)
        parser.add_argument('body', type=str)


        args = parser.parse_args()
        title = args['title']
        category = args['category']
        body = args['body']
        

        newPost = models.Post(title = title
        ,category = category
        ,body = body
        ,userid = current_identity['userid']
        ,timestamp = datetime.now())
    
        db.session.add(newPost)
        db.session.commit()
        return jsonify({
            'status': 'success',
            'msg': 'succeed!'
            })



# api entry to submit new comment to a post
class Comment(Resource):
    @jwt_required()
    def post(self):

        parser = reqparse.RequestParser()
        parser.add_argument('postId', type=int)
        parser.add_argument('comment', type=str)



        args = parser.parse_args()
        postId = args['postId']
        comment = args['comment']

        

        newComment = models.Comment(body = comment
        ,userid = current_identity['userid']
        ,postid = postId
        ,timestamp = datetime.now())
    
        db.session.add(newComment)
        db.session.commit()
        return jsonify({
            'status': 'success',
            'msg': 'succeed!'
            })


# urls of api
api.add_resource(PostList, '/api/blog/postlist')
api.add_resource(CommentList, '/api/blog/post/<postId>/commentlist')
api.add_resource(Register, '/api/blog/register')
api.add_resource(Post, '/api/blog/post')
api.add_resource(Comment, '/api/blog/comment')

if __name__ == '__main__':
    app.run(debug=True)
from flask import Flask, render_template

from flask import request, redirect, url_for, flash, jsonify

from flask import session as login_session
import random
import string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

import os

import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Idea, Person, Comment

app = Flask(__name__)
app.secret_key = os.urandom(24)

CLIENT_ID = json.loads(open(
                            'client_secrets.json', 'r'
                            ).read())['web']['client_id']

engine = create_engine('sqlite:///vantage_feedback_users.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route('/')
@app.route('/login')
def showLogin():
    state = ''.join(
                    random.choice(
                                  string.ascii_uppercase + string.digits
                                  ) for x in xrange(32)
                   )
    login_session['state'] = state
    return render_template('login.html', STATE=state)


# allows users to login, code modified from
# https://github.com/udacity/ud330/tree/master/Lesson2
@app.route('/gconnect', methods=['POST'])
def gconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    code = request.data
    try:
        # Upgrading auth code into credentials
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
        	json.dumps(
                       'Failed to upgrade the authorization code.'
                      ), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    access_token = credentials.access_token
    url = (
            'https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
            % access_token
            )
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])

    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps(
                       "Token's user ID doesn't match given user ID."
                      ), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps(
                       "Token's client ID does not match app's"
                      ), 401)
        print "Token's client ID does not match app's"
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps(
                       'Current user is already connected.'
                      ), 200)
        response.headers['Content-Type'] = 'application/json'

    login_session['credentials'] = credentials.access_token
    login_session['gplus_id'] = gplus_id
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)
    data = answer.json()
    login_session['username'] = data['name']
    login_session['email'] = data['email']

    person_id = getPersonID(login_session['email'])
    if not person_id:
        person_id = createPerson(login_session)
    login_session['person_id'] = person_id

    output = ''
    output += '<p>Welcome to the Vantage backlog </p>'
    flash("You are now logged in!")

    print "done!"
    return output


# disconnects or logs off a user, redirect to login
@app.route('/gdisconnect')
def gdisconnect():
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(
            json.dumps(
                       'Current user not connected.'
                      ), 401)
        response.headers['Content-Type'] = 'application/json'
        return redirect('/login')

    access_token = credentials
    url = 'http://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        del login_session['credentials']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']

        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return redirect('/login')
    else:
        response = make_response(json.dumps('Failed to \
            revoke token for given user.'), 400)
        respone.headers['Content-Type'] = 'application/json'
        return response


# shows all the ideas in the database
@app.route('/all_ideas')
def showAllIdeas():
    ideas = session.query(Idea).all()
    if 'username' not in login_session:
        return redirect('/login')
    else:
        person_id = login_session['person_id']
        people = session.query(Person).all()
        comments = session.query(Comment).all()
        return render_template(
                               'ideas.html', people=people,
                               ideas=ideas, comments=comments,
                               person_id=person_id
                               )


# creates a comment when submit button for comment is pressed
@app.route('/all_ideas', methods=['POST'])
def createComment():
    if 'username' not in login_session:
        return redirect('/login')
    idea_id = request.form['id']
    person_id = login_session['person_id']
    person = session.query(Person).filter_by(id=person_id).one()
    comment = Comment()
    comment.text = request.form['text']
    comment.person_id = login_session['person_id']
    comment.idea_id = idea_id
    comment.person = person
    session.add(comment)
    session.commit()
    return redirect("http://0.0.0.0.xip.io:5000/all_ideas")


# page to edit a comment
@app.route('/comment/<int:comment_id>/edit')
def editCommentForm(comment_id):
    comment = session.query(Comment).filter_by(id=comment_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if comment.person_id != login_session['person_id']:
        return "<script> function myFunction(){alert('Only the\
         individual who created the comment is authorized to edit it. \
         Please ask them to edit it, or login as the prescribed \
         user');}</script><body onload='myFunction()'>"
    else:
        comment = session.query(Comment).filter_by(id=comment_id).one()
        return render_template('edit_comment.html', comment=comment)


# posting an edited comment
@app.route('/comment/<int:comment_id>/edit', methods=['POST'])
def editComment(comment_id):
    comment = session.query(Comment).filter_by(id=comment_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if comment.person_id != login_session['person_id']:
        return "<script> function myFunction(){alert('Only the individual\
         who created the comment is authorized to edit it. Please ask them\
          to edit it, or login as the prescribed\
           user');}</script><body onload='myFunction()'>"
    else:
        comment.text = request.form['text']
        session.add(comment)
        session.commit()
        return redirect("http://0.0.0.0.xip.io:5000/all_ideas")


# page to edit an idea
@app.route('/idea/<int:idea_id>/edit')
def editIdeaForm(idea_id):
    idea = session.query(Idea).filter_by(id=idea_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if idea.person_id != login_session['person_id']:
        return "<script> function myFunction(){alert('Only the\
         individual who created the idea is authorized to edit it.\
          Please ask them to edit it, or login as the prescribed\
           user');}</script><body onload='myFunction()'>"
    else:
        idea = session.query(Idea).filter_by(id=idea_id).one()
        return render_template('edit_idea.html', idea=idea)


# posting an edited comment
@app.route('/idea/<int:idea_id>/edit', methods=['POST'])
def editIdea(idea_id):
    idea = session.query(Idea).filter_by(id=idea_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if idea.person_id != login_session['person_id']:
        return "<script> function myFunction(){alert('Only the\
         individual who created the idea is authorized to edit it.\
          Please ask them to edit it, or login as the prescribed \
          user');}</script><body onload='myFunction()'>"
    else:
        idea = session.query(Idea).filter_by(id=idea_id).one()
        idea.description = request.form['text']
        session.add(idea)
        session.commit()
        return redirect("http://0.0.0.0.xip.io:5000/all_ideas")


# page to delete a comment
@app.route('/comment/<int:comment_id>/delete')
def deleteCommentForm(comment_id):
    comment = session.query(Comment).filter_by(id=comment_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if comment.person_id != login_session['person_id']:
        return "<script> function myFunction(){alert('Only the\
         individual who created the comment is authorized to delete it.\
          Please ask them to delete it, or login as the prescribed\
           user');}</script><body onload='myFunction()'>"
    else:
        comment = session.query(Comment).filter_by(id=comment_id).one()
        return render_template('delete_comment.html', comment=comment)


# posting to delete a comment
@app.route('/comment/<int:comment_id>/delete', methods=['POST'])
def deleteComment(comment_id):
    comment = session.query(Comment).filter_by(id=comment_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if comment.person_id != login_session['person_id']:
        return "<script> function myFunction(){alert('Only the\
         individual who created the comment is authorized to delete\
          it. Please ask them to delete it, or login as the prescribed\
           user');}</script><body onload='myFunction()'>"
    else:
        session.delete(comment)
        session.commit()
        return redirect("http://0.0.0.0.xip.io:5000/all_ideas")


# page to delete an idea
@app.route('/idea/<int:idea_id>/delete')
def deleteIdeaForm(idea_id):
    idea = session.query(Idea).filter_by(id=idea_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if idea.person_id != login_session['person_id']:
        return "<script> function myFunction(){alert('Only the\
         individual who created the idea is authorized to delete\
          it. Please ask them to delete it, or login as the prescribed\
           user');}</script><body onload='myFunction()'>"
    else:
        idea = session.query(Idea).filter_by(id=idea_id).one()
        return render_template('delete_idea.html', idea=idea)


# posting to delete an idea
@app.route('/idea/<int:idea_id>/delete', methods=['POST'])
def deleteIdea(idea_id):
    idea = session.query(Idea).filter_by(id=idea_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if idea.person_id != login_session['person_id']:
        return "<script> function myFunction(){alert('Only the\
         individual who created the idea is authorized to delete\
          it. Please ask them to delete it, or login as the prescribed\
           user');}</script><body onload='myFunction()'>"
    else:
        idea = session.query(Idea).filter_by(id=idea_id).one()
        comments = session.query(Comment).filter_by(idea_id=idea.id).all()
        session.delete(idea)
        for c in comments:
            session.delete(c)
        session.commit()
        return redirect("http://0.0.0.0.xip.io:5000/all_ideas")


# calls all the ideas created under a specific person
@app.route('/ideas/<int:person_id>/')
def personIdeas(person_id):
    if 'username' not in login_session:
        return redirect('/login')
    else:
        people = session.query(Person).all()
        ideas = session.query(Idea).filter_by(person_id=person_id).all()
        comments = session.query(Comment).all()
        return render_template(
                               'ideas.html', people=people,
                               ideas=ideas, comments=comments
                               )


# page to create a new idea
@app.route('/new_idea/<int:person_id>/')
def newIdea(person_id):
    if 'username' not in login_session:
        return redirect('/login')
    else:
        return render_template('new_idea.html', login_session=login_session)


# page to post a new idea
@app.route('/new_idea/<int:person_id>/', methods=['POST'])
def createIdea(person_id):
    if 'username' not in login_session:
        return redirect('/login')
    else:
        idea = Idea()
        idea.title = request.form['title']
        idea.description = request.form['description']
        idea.person_id = login_session['person_id']
        session.add(idea)
        session.commit()
        return redirect("http://0.0.0.0.xip.io:5000/all_ideas")


# creating API endpoints
# endpoint to get all ideas in json array
@app.route("/api/all_ideas")
def endpointAllIdeas():
    if request.method == 'GET':
        ideas = session.query(Idea).all()
        return jsonify(ideas=[i.serialize for i in ideas])
    else:
        return "This endpoint only accepts GET requests"


# call to get a specific idea based on idea id
@app.route("/api/<int:id>/idea")
def endpointIdea(id):
    if request.method == 'GET':
        idea = session.query(Idea).filter_by(id=id).one()
        return jsonify(idea=idea.serialize)
    else:
        return "This endpoint only accepts GET requests"


def getPersonID(email):
    try:
        person = session.query(Person).filter_by(email=email).one()
        return person.id
    except:
        return None


def getPersonInfo(person_id):
    person = session.query(Person).filter_by(id=person_id).one()


def createPerson(login_session):
    newPerson = Person(email=login_session['email'])
    session.add(newPerson)
    session.commit()
    person = session.query(Person).filter_by(
        email=login_session['email']).one()
    return person.id


# this is pulled from http://flask.pocoo.org/snippets/40/ \
# and removes caching so CSS is up to date
@app.context_processor
def override_url_for():
    return dict(url_for=dated_url_for)


def dated_url_for(endpoint, **values):
    if endpoint == 'static':
        filename = values.get('filename', None)
        if filename:
            file_path = os.path.join(
                app.root_path, endpoint, filename
                )
            values['q'] = int(os.stat(file_path).st_mtime)
    return url_for(endpoint, **values)

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0.xip.io', port=5000)

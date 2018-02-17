README.md

# Product Backlog - Flask Application

### Overview

This project has been completed as part of the Udacity Full-Stack Nanodegree. The goal was to create a web application using Flask that implements a 3rd party authorization system (Google OAuth API in this case) and allows users to perform various CRUD operations against a SQL database using an ORM. The app also has a JSON endpoint to serve as an API.

I created a product backlog tool that can be used to save and comment on feature ideas to a database. Often times product teams end up with feature ides strewn about on notepads, Dropbox paper and Slack channels. A single database and expanded upon version of this app could be useful for tracking product ideas and features.

### Run this Application

To run this application...

1. Install *Vagrant*
2. Install *Virtual Box*
3. Clone the *flask_product_backlog* repository
4. CD to vagrant folder, then run `vagrant up` -> `vagrant ssh` -> `cd vagrant` -> `cd catalog` -> `python app.py`
5. The app will run locally on http://0.0.0.0.xip.io:5000/

### API Access

1. Run application as of above
2. Make GET requests to `http://0.0.0.0.xip.io:5000/api/all_ideas` for a JSON array of all ideas in the database or `http://0.0.0.0.xip.io:5000/api/<str:idea_id>/idea` for a JSON object with a specific id

### Supporting Materials

Used the Udacity fullstack repo to base the project around
https://github.com/udacity/fullstack-nanodegree-vm

Used to structure Google login and logoff commands
https://github.com/udacity/ud330/tree/master/Lesson2

Used this API tester document to model `test_api.py`
https://github.com/udacity/APIs/blob/master/Lesson_3/06_Adding%20Features%20to%20your%20Mashup/Solution%20Code/tester.py

### Future Work

This was inspired by my own work on a news app and a conversation with an entrepreneur who was developing a scoring system for his company's product backlog. In the future I would like to incorporate an interface to record user feedback and interview notes, as well as a scoring system where team members can score the feasability, importance etc. of certain ideas.

# puzzlehunt_server
Server for Puzzlehunt CMU's bi-annual puzzlehunt.

Required Software:
* python 2.7
* Django 1.8 (pip)
* mysql-client
* mysql-server
* python-mysqldb
* redis-server
* python-dev
* django-websocket-redis (pip)
I'm sure I'm missing a few others (I'll try to get this virtualenv'd but no promises)

Database setup details:
* expects a pre-existing database named puzzlehunt_db
* expects a user named ```hunt``` on domain ```localhost``` with password ```wrongbaa``` with access to ```puzzlehunt_db```
* The above can be accomplished by running the following commands as a superuser:
   * ```CREATE DATABASE puzzlehunt_db;```
   * ```CREATE USER 'hunt'@'localhost' IDENTIFIED BY 'wrongbaa';```
   * ```GRANT ALL PRIVILEGES ON puzzlehunt_db.* TO 'hunt'@'localhost' WITH GRANT OPTION;```
* run ```python manage.py migrate``` to have django configure the database
* then run ```python manage.py runserver 8080``` to start a server at http://127.0.0.1:8080/ (this will be replaced with nginx in the production version)
 

Project Details:
* Check out file_map.txt for new developers.
* Planned (now out of date) models and views can be found and contributed to [here](https://docs.google.com/document/d/1m_et2SfdcPdOuWgtSCfs9RXN9QTxW9WGgjHZsOQ2yFo/edit)
* The django project is named ```puzzlehunt_server``` amd the app is named ```huntserver```
* We are using setup and coding practices taken from the django tutorial [here](https://docs.djangoproject.com/en/1.8/intro/tutorial01/)
* There is a branch with the tutorial server mentioned above up to halfway through the 4th part for code refrence.


Base Features:
- [x] Answer Submission
- [x] Team ID sign in
- [x] Answer response system
- [x] Landing Page
- [x] admin view - edit data
- [x] admin view - graphs
- [x] admin view - queue
- [x] admin view - puzzle stats
- [x] Graph unlocking structure


Desired Features
- [ ] Public facing charts and leaderboard (disableable)
- [ ] Hints
- [x] Upgraded Hunt home page with answers and status
- [x] Manual response being correct
- [x] Admins be able to see manual responses
- [ ] Send more than one manual response
- [ ] Multiple Landing pages
- [x] Very clear puzzle labeling
- [ ] Ability for puzzle solutions to unlock objects
- [ ] Ability to set interactive unlocks and give notifications
- [x] Chatroom with staff for difficulties
- [ ] Server can get puzzles from links using button on admin page.
- [ ] Upgrade puzzle page to have in-body pdf/puzzle
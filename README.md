### vyvyan

the aim of this service is to abstract away the pain of managing users in LDAP 


### Python Dependencies
* SQLAlchemy
* PyYAML
* python-ldap
* passlib 

### Required External Applications
* a database of some sort. we currently support MySQL and PostgreSQL

### Configuration
* copy vyvyan_daemon.yaml.sample and vyvyan_cli.yaml.sample to either ~/ or /etc/, remove .sample, edit to taste

### Usage
* run vyvyan_daemon.py to serve up the API interface
* use vyv.py (or the vyv symlink) to talk to the API from the command line

#### Current Contributors
* David Kovach [![endorse](http://api.coderwall.com/downneck/endorsecount.png)](http://coderwall.com/downneck)

function Student(name, grade, gender, init_assessment)
{
    this.name = name;
    this.grade = grade;
    this.gender = gender;
    this.init_assessment = init_assessment;
}

function Tutor(first, last, gender)
{
    this.first = first;
    this.last = last;
}

function DbTable(dbname, $scope)
{
    var remote_db = 'http://wcy.iriscouch.com';

    /*-------------------  Members ------------------*/
    this.data = [];
    dbtable = this;
    this.db = new Pouch(dbname, function(err, db) {
	if (err) {
	    console.log(err);
	}
	else {
	    db.allDocs(function(err, response) {
		if (err) {
		    console.log(err);
		}
		else {
		    dbtable.load(response.rows);
		}
	    });
	}
    });


    /*-------------------  Methods ------------------*/
    this.load = function(rows) {
	for (var ii = 0; ii < rows.length; ii++) {
	    this.db.get(rows[ii].id, function(err, doc) {
		if (err) {
		    console.log("Error loading objects, can't find object for row "
				+ rows[ii]);
		    console.log(err);
		} else {
		    $scope.$apply(function() {
			console.log(doc);
			dbtable.data.push(doc);
		    });
		    
		}
	    });
	    
	}
    }

    this.add = function(doc) {
	console.log(doc);
	doc = JSON.parse(JSON.stringify(doc));
	console.log(doc);
	this.db.post(doc, function(err, response) {
	    if (err) {
		console.log("Error adding object " + doc);
		console.log(err);
	    } else {
		doc._id = response.id;
		$scope.$apply(function() {
		    console.log(dbtable);
		    dbtable.data.push(doc);
		});
	    }
	});
    }

    this.get = function(id) {
	for (var ii = 0; ii < this.data.length; ii++) {
	    if (this.data[ii].id == id) {
		return this.data[ii];
	    }
	}
    }

    this.remove = function(id) {
	this.db.get(id, function(err, doc) {
	    if (err) {
		console.log("Error removing object, can't find id " + id);
		console.log(err);
	    } else {
		dbtable.db.remove(doc, function(err, response) {
		    if (err) {
			console.log("Error removing object id "
				    + id + " doc " + doc);
			console.log(err);
		    } else {
			$scope.$apply(function() {
			    var olddata = dbtable.data;
			    dbtable.data = [];
			    angular.forEach(olddata, function(doc) {
				if (doc._id != id) {
				    dbtable.data.push(doc);
				}
			    });
			});
		    }
		});
	    }
	});
    }

    this.update = function(id, newdoc) {
	newdoc = JSON.stringify(newdoc);
	this.db.get(id, function(err, existing) {
	    if (err) {
		console.log("Error updating object, can't find id " + id);
		console.log(err);
	    } else {
		newdoc._id = id;
		newdoc._rev = existing._rev;
		this.db.put(newdoc, function(err, response) {
		    if (err) {
			console.log("Error updating object, can't put newdoc "
				    + newdoc + " id " + id);
			console.log(err);
		    } else {
			$scope.$apply(function() {
			    var olddata = dbtable.data;
			    dbtable.data = [];
			    angular.forEach(olddata, function(olddoc) {
				if (olddoc.id != id) {
				    dbtable.data.push(olddoc);
				} else {
				    dbtable.data.push(newdoc);
				}
			    });
			});
		    }
		});
	    }
	});
    }
}

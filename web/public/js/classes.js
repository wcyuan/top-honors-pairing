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

    /*-------------------  Members ------------------*/
    this.data = [];
    this.cancels = []
    dbtable = this;

    /*-------------------  Replication ------------------*/

    var remote_db = 'http://wcy.iriscouch.com/' + dbname;

    function syncError() {
	console.log("Sync error!");
    }

    /*-------------------  Methods ------------------*/
    this.getdb = function(dbname, $scope) {
	return this.createdb(dbname, $scope);
    }

    this.createdb = function(dbname, $scope) {
	this.db = new Pouch(dbname, function(err, db) {
	    if (err) {
		console.log("Error creating database " + dbname);
		console.log(err);
	    }
	    else {
		dbtable.refresh(db, $scope);
	    }
	});
	//this.start_syncing($scope)
    }

    this.sync = function($scope) {
	console.log("Starting syncing...");
	var opts = {
	    complete: function(err, response) {
		if (err) {
		    console.log("Error syncing!");
		} else {
		    console.log("Done syncing!  " + response);
		}
	    },
	    onChange: function(change) {
		dbtable.refresh(dbtable.db, $scope);
	    }};
	this.db.replicate.to(remote_db, opts);
	this.db.replicate.from(remote_db, opts);
    }

    this.start_syncing = function($scope) {
	this.db.info(function(err, info) {
	    dbtable.cancels.push(dbtable.db.changes({
		since: info.update_seq,
		continuous: true,
		onChange: function() { dbtable.refresh(dbtable.db, $scope) }
	    }));
	});
	var opts = {continuous: true, complete: syncError};
	this.cancels.push(this.db.replicate.to(remote_db, opts));
	this.cancels.push(this.db.replicate.from(remote_db, opts));
    }

    this.stop_syncing = function($scope) {
	for (tocancel in this.cancels) {
	    tocancel.cancel();
	}
	this.cancels = []
    }

    this.refresh = function(db, $scope) {
	db.allDocs(function(err, response) {
	    if (err) {
		console.log("Error getting all objects");
		console.log(err);
	    }
	    else {
		dbtable.load(response.rows, $scope);
	    }
	});
    }

    this.load = function(rows, $scope) {
	$scope.$apply(function() {
	    dbtable.data = []
	});
	for (var ii = 0; ii < rows.length; ii++) {
	    this.db.get(rows[ii].id, function(err, doc) {
		if (err) {
		    console.log("Error loading objects, can't find object for row "
				+ rows[ii]);
		    console.log(err);
		} else {
		    $scope.$apply(function() {
			console.log("Loading: ");
			console.log(doc);
			dbtable.data.push(doc);
		    });
		    
		}
	    });
	    
	}
    }

    this.add = function(doc, $scope) {
	this.db.post(doc, function(err, response) {
	    if (err) {
		console.log("Error adding object " + doc);
		console.log(err);
	    } else {
		doc._id = response.id;
		$scope.$apply(function() {
		    console.log("Adding: ");
		    console.log(doc);
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

    this.remove = function(id, $scope) {
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
				} else {
				    console.log("Removing object id "
						+ id);
				    console.log(doc);
				}
			    });
			});
		    }
		});
	    }
	});
    }

    this.update = function(id, newdoc, $scope) {
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

    this.getdb(dbname, $scope);
}

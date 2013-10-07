'use strict';

/* Services */

/*
angular.module('th_database', []).
    factory('Database', function() {
        var remote_db = 'http://wcy.iriscouch.com';
	var dbs = {};

	function get_db(dbname) {
	    var fullname = remote_db + "/" + dbname;
	    if (!(fullname in dbs)) {
		dbs[fullname] = new Pouch(fullname, function(err, db) {
		};
	    }
	}

	this.get = function(dbname, key) {
	    get_db(dbname)
	}

    });
*/
/*
angular.module('phonecatServices', ['ngResource']).
    factory('Phone', function($resource){
  return $resource('phones/:phoneId.json', {}, {
    query: {method:'GET', params:{phoneId:'phones'}, isArray:true}
  });
});
*/

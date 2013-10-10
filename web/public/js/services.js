'use strict';

/* Services */

angular.module('th_database', []).
    factory('Database', function() {

	var cache = {}

	return function (dbname, $scope) {
	    if (!(dbname in cache)) {
		cache[dbname] = new DbTable(dbname, $scope);
	    }
	    return cache[dbname];
	}

    });


/*
angular.module('phonecatServices', ['ngResource']).
    factory('Phone', function($resource){
  return $resource('phones/:phoneId.json', {}, {
    query: {method:'GET', params:{phoneId:'phones'}, isArray:true}
  });
});
*/

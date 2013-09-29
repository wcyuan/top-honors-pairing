'use strict';

/* Services */

angular.module('thpairingServices', ['ngResource']).
factory('Student', function($resource){
          var db = new PouchDB('students');
          return $resource('student/:studentId', {}, {
                           query: {method:'GET', params:{studentId:''}, isArray:true}
                           });
        });

/*
angular.module('phonecatServices', ['ngResource']).
    factory('Phone', function($resource){
  return $resource('phones/:phoneId.json', {}, {
    query: {method:'GET', params:{phoneId:'phones'}, isArray:true}
  });
});
*/

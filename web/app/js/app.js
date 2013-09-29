'use strict';

/* App Module */

/* angular + pouch: http://jsfiddle.net/zrrrzzt/cNVhE/ */

angular.module('thpairing', ['thpairingServices']).
config(['$routeProvider', function($routeProvider) {
         $routeProvider.
           when('/students', {templateUrl: 'partials/student-list.html',   controller: StudentListCtrl}).
           otherwise({redirectTo: '/students'});
       }]);

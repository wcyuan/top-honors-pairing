'use strict';

/* App Module */

angular.module('thpairing', []).
config(['$routeProvider', function($routeProvider) {
         $routeProvider.
           when('/students', {templateUrl: 'partials/student-list.html',   controller: StudentListCtrl}).
           otherwise({redirectTo: '/students'});
       }]);

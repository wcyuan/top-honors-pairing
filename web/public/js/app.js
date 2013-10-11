'use strict';

/* App Module */

/* angular + pouch: http://jsfiddle.net/zrrrzzt/cNVhE/ */

angular.module('thpairing', ['th_database']).
config(['$routeProvider', function($routeProvider) {
         $routeProvider.
           when('/students', {templateUrl: 'partials/student-list.html',   controller: StudentListCtrl}).
           otherwise({redirectTo: '/students'});
       }]);


angular.module('thpairing').run(function($rootScope) {
    window.addEventListener("online", function () {
        $rootScope.$broadcast('onlineChanged', true);
    }, true);

    window.addEventListener("offline", function () {
        $rootScope.$broadcast('onlineChanged', false);
    }, true);
});


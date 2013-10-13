'use strict';

/* App Module */

/* angular + pouch: http://jsfiddle.net/zrrrzzt/cNVhE/ */

angular.module('thpairing', ['th_database']).
    config(['$routeProvider', function($routeProvider) {
	$routeProvider.
            when('/students', {templateUrl: 'partials/student-list.html',   controller: StudentListCtrl}).
            //when('/pairing', {templateUrl: 'partials/pairing-list.html',   controller: PairingListCtrl}).
            //when('/historical', {templateUrl: 'partials/historical-list.html',   controller: HistoricalListCtrl}).
            //when('/scoring', {templateUrl: 'partials/scoring-list.html',   controller: ScoringListCtrl}).
            //when('/tutors', {templateUrl: 'partials/tutor-list.html',   controller: TutorListCtrl}).
            otherwise({templateUrl: 'partials/default.html'});
    }]);


angular.module('thpairing').run(function($rootScope) {
    window.addEventListener("online", function () {
        $rootScope.$broadcast('onlineChanged', true);
    }, true);

    window.addEventListener("offline", function () {
        $rootScope.$broadcast('onlineChanged', false);
    }, true);
});


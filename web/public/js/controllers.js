'use strict';

/* Controllers */

function StudentListCtrl($scope, Database, $rootScope) {
    $scope.students = Database('students', $scope);
    $scope.isOnline = "online";
    $scope.addStudent = function() {
	var student = new Student($scope.studentName, '', '', '');
	$scope.students.add(student, $scope);
    }
    $scope.removeStudent = function(studentId) {
	$scope.students.remove(studentId, $scope);
    }
    $scope.sync = function() {
	$scope.students.sync($scope);
    }
    $rootScope.$on('onlineChanged', function(evt, isOnline) {
	if (isOnline) {
	    $scope.$apply(function() {
		$scope.isOnline = "online";
	    });
	    //$scope.students.start_syncing($scope);
	} else {
	    $scope.$apply(function() {
		$scope.isOnline = "offline";
	    });
	    //$scope.students.stop_syncing($scope);
	}
    });
}

function EditStudentCtrl($scope, Database) {
}

function AddStudentCtrl($scope, Database) {
}


function StudentListCtrl2($scope, Student) {
  $scope.students = [];
  $scope.order = 'name';

  $scope.pouchdb = Pouch('idb://thpairing_students', function(err, db) {
    if (err) {
      console.log(err);
    }
    else {
      db.allDocs(function(err, response) {
                   if (err) {
                     console.log(err);
                   }
                   else {
                     $scope.loadStudents(response.rows);
                   }
                 });
    }
  });

  $scope.loadStudents = function(students) {
    for (var i = 0; i < students.length - 1; i++) {
      var student = students[i];
      $scope.pouchdb.get(student.id, function(err, doc) {
                           if (err) {
                             console.log(err);
                           }
                           else {
                             $scope.$apply(function() {
                                             $scope.students.push(doc);
                                           });
                           }
                         });
    };
  }

    $scope.addStudent = function() {
        var newStudent = {
          _id: new Date().toISOString(),
            name: $scope.studentName
        };
        $scope.students.push(newStudent);
        $scope.studentName = '';
        $scope.pouchdb.put(newStudent, function callback(err, result) {
                             if(err) {
                               console.log('error! ' + err);
                             } else {
                               console.log('Added a student: ' + newStudent._id + '!');
                             }
           });
    };

    $scope.updateStudent = function(student) {
        $scope.pouchdb.put(student);
        // Need to update $scope.students too
    };

    $scope.removeStudent = function(studentId) {
        $scope.pouchdb.get(studentId, function(err, doc) {
            if (err) {
                console.log(err);
            }
            else {
                $scope.pouchdb.remove(doc, function(err, response) {
                    console.log(response);
                });
                $scope.$apply(function() {
                                var oldStudents = $scope.students;
                                $scope.students = [];
                                angular.forEach(oldStudents, function(student) {
                                                  if (student._id != studentId) {
                                                    $scope.students.push(student)
                                                      }
                                                });
                                console.log($scope.students);
                              });
            }
        });
    };
}

function PhoneListCtrl($scope, Phone) {
  $scope.phones = Phone.query();
  $scope.orderProp = 'age';
}

//PhoneListCtrl.$inject = ['$scope', 'Phone'];



function PhoneDetailCtrl($scope, $routeParams, Phone) {
  $scope.phone = Phone.get({phoneId: $routeParams.phoneId}, function(phone) {
    $scope.mainImageUrl = phone.images[0];
  });

  $scope.setImage = function(imageUrl) {
    $scope.mainImageUrl = imageUrl;
  }
}

//PhoneDetailCtrl.$inject = ['$scope', '$routeParams', 'Phone'];

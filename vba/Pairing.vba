Option Base 1
Public Minutes As Integer, Seconds As Integer, Time As Double
Sub Tutor_Student_Pairing()

Dim StudentScore As Range
Dim GroupScore As Range, ThreeGroupScore As Range
Dim FirstStudent As Range, SecondStudent As Range, ThirdStudent As Range, Tutor As Range

Application.ScreenUpdating = False

Time = Timer

'Take current week or have user input week
CurrentWeek = InputBox(Prompt:="Please input week number: ", Title:="Week Number")

'Variables and their point value
STIncompatible = -20
STPaired = 1
STGood = 5
SSIncompatible = -20
Attendance = 0.1
NotSameTopic = -5
OnOwn = -10
DifferentGrade = -2
DifferentAssessment = -3

'*********Add Students and Tutors to Score Sheet*****************************************************************'
Worksheets("Score Sheet").Activate
'Set the parameters for Find to "Whole Cell"
Cells.Find(What:="", After:=ActiveCell, LookIn:=xlFormulas, _
    LookAt:=xlWhole, SearchOrder:=xlByRows, SearchDirection:=xlNext, _
    MatchCase:=False, SearchFormat:=False).Activate
Cells.Delete
Cells(1, 1) = "Student"

'Add Students to Score Sheet
Worksheets("Student Info").Activate
StudentColumn = Rows(1).Find("Student").Column
StartRow = 2
EndRow = ActiveSheet.UsedRange.Rows.Count
DestinationRow = 2
DestinationColumn = 1

For CurrentRow = StartRow To EndRow
    Worksheets("Score Sheet").Cells(DestinationRow, DestinationColumn) = Cells(CurrentRow, StudentColumn)
    DestinationRow = DestinationRow + 1
Next

'Add Group names and rows for use in Group Scoring
Worksheets("Score Sheet").Cells(EndRow + 1, DestinationColumn) = "Group Score"
GroupScoreRow = EndRow + 1
Worksheets("Score Sheet").Cells(EndRow + 2, DestinationColumn) = "Three Group Score"
ThreeGroupScoreRow = EndRow + 2
Worksheets("Score Sheet").Cells(EndRow + 3, DestinationColumn) = "First Student"
FirstStudentRow = EndRow + 3
Worksheets("Score Sheet").Cells(EndRow + 4, DestinationColumn) = "Second Student"
SecondStudentRow = EndRow + 4
Worksheets("Score Sheet").Cells(EndRow + 5, DestinationColumn) = "Third Student"
ThirdStudentRow = EndRow + 5

'Add Tutors to Score Sheet
Worksheets("Tutor Info").Activate
TutorColumn = Rows(1).Find("Tutor").Column
StartRow = 2
EndRow = ActiveSheet.UsedRange.Rows.Count
DestinationRow = 1
DestinationColumn = 2

For CurrentRow = StartRow To EndRow
    Worksheets("Score Sheet").Cells(DestinationRow, DestinationColumn) = Cells(CurrentRow, TutorColumn)
    DestinationColumn = DestinationColumn + 1
Next

'*********Add Individual Score************************************************************************************'

Worksheets("Score Sheet").Activate
'AllTutors = Rows(1).End(xlToRight).Column - 1
'AllStudents = Columns(1).Find("Group Score").Row - 1
StartRow = 2
EndRow = Columns(1).Find("Group Score").Row - 1
StartColumn = 2
EndColumn = Rows(1).End(xlToRight).Column

'For EachStudent = 1 To AllStudents
'Cycle through each student and tutor combination to get students' score with that tutor
For EachStudent = StartRow To EndRow

    Worksheets("Score Sheet").Activate
    AttendanceScore = 0
    CurrentStudent = Cells(EachStudent, 1)

    'Determine whether student is here this week
    Worksheets("Attendance").Activate
    PersonColumn = Rows(1).Find("Person").Column
    WeekColumn = Rows(1).Find("Week").Column

    If WorksheetFunction.CountIfs(Columns(PersonColumn), CurrentStudent, Columns(WeekColumn), CurrentWeek) = 1 Then
        'Add score for how many times student has attended before
        AttendanceScore = Attendance * WorksheetFunction.CountIf(Columns(PersonColumn), CurrentStudent)
    Else
        GoTo NextStudent
    End If

    For EachTutor = StartColumn To EndColumn

'        Call TimeUpdate

        Worksheets("Score Sheet").Activate
        CurrentTutor = Cells(1, EachTutor)

        'Determine whether tutor is here this week
        Worksheets("Attendance").Activate
        If WorksheetFunction.CountIfs(Columns(PersonColumn), CurrentTutor, Columns(WeekColumn), CurrentWeek) <> 1 Then
            GoTo NextTutor
        End If

        Set StudentScore = Worksheets("Score Sheet").Cells(EachStudent, EachTutor)

        'STPaired
        Worksheets("Week to Week").Activate
        TutorColumn = Rows(1).Find("Tutor").Column
        StudentColumn = Rows(1).Find("Student").Column
        StudentScore = AttendanceScore + STPaired * WorksheetFunction.CountIfs(Columns(TutorColumn), CurrentTutor, Columns(StudentColumn), CurrentStudent)

        'STGood
        Worksheets("Absolutes").Activate
        Person1Column = Rows(1).Find("Person 1").Column
        Person2Column = Rows(1).Find("Person 2").Column
        AbsoluteColumn = Rows(1).Find("Absolute").Column
        StudentScore = StudentScore + STGood * WorksheetFunction.CountIfs(Columns(TutorColumn), CurrentTutor, Columns(StudentColumn), CurrentStudent, Columns(AbsoluteColumn), "Good Match")

        'STIncompatible
        StudentScore = StudentScore + STIncompatible * WorksheetFunction.CountIfs(Columns(TutorColumn), CurrentTutor, Columns(StudentColumn), CurrentStudent, Columns(AbsoluteColumn), "Tutor Student")

NextTutor:

    Next

NextStudent:

Next

'*********Add Group Score******************************************************************************************'

If EachStudent > EachTutor Then

    Worksheets("Score Sheet").Activate
    StartColumn = 2
    EndColumn = Rows(1).End(xlToRight).Column

    For Group = StartColumn To EndColumn

        Worksheets("Score Sheet").Activate

        'If Tutor is not there (nothing in column)
        If WorksheetFunction.CountA(Columns(Group)) = 1 Then
            GoTo NextGroup
        End If

        Set GroupScore = Worksheets("Score Sheet").Cells(GroupScoreRow, Group)
        Set ThreeGroupScore = Worksheets("Score Sheet").Cells(ThreeGroupScoreRow, Group)

        'Sort to get matching of largest correct
        With Worksheets("Score Sheet")
            .Sort.SortFields.Clear
            .Sort.SortFields.Add Key:=Range(Cells(2, Group), Cells(GroupScoreRow - 1, Group)) _
                , SortOn:=xlSortOnValues, Order:=xlDescending, DataOption:=xlSortNormal
            .Sort.SetRange Range(Cells(1, 1), Cells(GroupScoreRow - 1, EndColumn))
            .Sort.Header = xlYes
            .Sort.MatchCase = False
            .Sort.Orientation = xlTopToBottom
            .Sort.SortMethod = xlPinYin
            .Sort.Apply
        End With

        Set FirstStudent = Cells(2, 1)
        Set SecondStudent = Cells(3, 1)
        Set ThirdStudent = Cells(4, 1)
        Set Tutor = Cells(1, Group)

        GroupScore = Cells(2, Group) + Cells(3, Group)
        'Add third student score if needed
        If EachStudent / EachTutor > 2 Then
            ThreeGroupScore = ThreeGroupScore + Cells(2, Group) + Cells(3, Group) + Cells(4, Group)
        End If

        'OnOwn
        Worksheets("Absolutes").Activate
        Person1Column = Rows(1).Find("Person 1").Column
        Person2Column = Rows(1).Find("Person 2").Column
        AbsoluteColumn = Rows(1).Find("Absolute").Column
        GroupScore = GroupScore + OnOwn * WorksheetFunction.CountIfs(Columns(Person1Column), FirstStudent, Columns(AbsoluteColumn), "On Own")
        GroupScore = GroupScore + OnOwn * WorksheetFunction.CountIfs(Columns(Person1Column), SecondStudent, Columns(AbsoluteColumn), "On Own")
        GroupScore = GroupScore + OnOwn * WorksheetFunction.CountIfs(Columns(Person1Column), Tutor, Columns(AbsoluteColumn), "On Own")
        'Add third student score if needed
        If EachStudent / EachTutor > 2 Then
            ThreeGroupScore = ThreeGroupScore + OnOwn * WorksheetFunction.CountIfs(Columns(Person1Column), FirstStudent, Columns(AbsoluteColumn), "On Own")
            ThreeGroupScore = ThreeGroupScore + OnOwn * WorksheetFunction.CountIfs(Columns(Person1Column), SecondStudent, Columns(AbsoluteColumn), "On Own")
            ThreeGroupScore = ThreeGroupScore + OnOwn * WorksheetFunction.CountIfs(Columns(Person1Column), ThirdStudent, Columns(AbsoluteColumn), "On Own")
            ThreeGroupScore = GroupScore + OnOwn * WorksheetFunction.CountIfs(Columns(Person1Column), Tutor, Columns(AbsoluteColumn), "On Own")
        End If

        'SSIncompatible
        Worksheets("Absolutes").Activate
        GroupScore = GroupScore + SSIncompatible * WorksheetFunction.CountIfs(Columns(Person1Column), FirstStudent, Columns(Person2Column), SecondStudent, Columns(AbsoluteColumn), "Student Student")
        'Add third student score if needed
        If EachStudent / EachTutor > 2 Then
            ThreeGroupScore = ThreeGroupScore + SSIncompatible * WorksheetFunction.CountIfs(Columns(Person1Column), FirstStudent, Columns(Person2Column), SecondStudent, Columns(AbsoluteColumn), "Student Student")
            ThreeGroupScore = ThreeGroupScore + SSIncompatible * WorksheetFunction.CountIfs(Columns(Person1Column), FirstStudent, Columns(Person2Column), ThirdStudent, Columns(AbsoluteColumn), "Student Student")
            ThreeGroupScore = ThreeGroupScore + SSIncompatible * WorksheetFunction.CountIfs(Columns(Person1Column), SecondStudent, Columns(Person2Column), ThirdStudent, Columns(AbsoluteColumn), "Student Student")
        End If

        'NotSameTopic
        Worksheets("Current Topic").Activate
        StudentWeekColumn = Rows(1).Find("Student & Week").Column

        If Cells(WorksheetFunction.Match(FirstStudent & CurrentWeek, Columns(StudentWeekColumn), 0), 3) <> Cells(WorksheetFunction.Match(SecondStudent & CurrentWeek, Columns(StudentWeekColumn), 0), 3) Then
            GroupScore = GroupScore + NotSameTopic
        End If
        'Add third student score if needed
        If EachStudent / EachTutor > 2 Then
            If Cells(WorksheetFunction.Match(FirstStudent & CurrentWeek, Columns(StudentWeekColumn), 0), 3) <> Cells(WorksheetFunction.Match(SecondStudent & CurrentWeek, Columns(StudentWeekColumn), 0), 3) Then
                ThreeGroupScore = ThreeGroupScore + NotSameTopic
            End If
            If Cells(WorksheetFunction.Match(FirstStudent & CurrentWeek, Columns(StudentWeekColumn), 0), 3) <> Cells(WorksheetFunction.Match(ThirdStudent & CurrentWeek, Columns(StudentWeekColumn), 0), 3) Then
                ThreeGroupScore = ThreeGroupScore + NotSameTopic
            End If
            If Cells(WorksheetFunction.Match(SecondStudent & CurrentWeek, Columns(StudentWeekColumn), 0), 3) <> Cells(WorksheetFunction.Match(ThirdStudent & CurrentWeek, Columns(StudentWeekColumn), 0), 3) Then
                ThreeGroupScore = ThreeGroupScore + NotSameTopic
            End If
        End If

        'DifferentGrade
        Worksheets("Student Info").Activate
        StudentColumn = Rows(1).Find("Student").Column
        GradeColumn = Rows(1).Find("Grade").Column

        If WorksheetFunction.Index(Range("A:D"), WorksheetFunction.Match(FirstStudent, Columns(StudentColumn), 0), GradeColumn) <> WorksheetFunction.Index(Range("A:D"), WorksheetFunction.Match(SecondStudent, Columns(StudentColumn), 0), GradeColumn) Then
            GroupScore = GroupScore + DifferentGrade
        End If
        'Add third student score if needed
        If EachStudent / EachTutor > 2 Then
            If WorksheetFunction.Index(Range("A:D"), WorksheetFunction.Match(FirstStudent, Columns(StudentColumn), 0), GradeColumn) <> WorksheetFunction.Index(Range("A:D"), WorksheetFunction.Match(SecondStudent, Columns(StudentColumn), 0), GradeColumn) Then
                ThreeGroupScore = ThreeGroupScore + DifferentGrade
            End If
            If WorksheetFunction.Index(Range("A:D"), WorksheetFunction.Match(FirstStudent, Columns(StudentColumn), 0), GradeColumn) <> WorksheetFunction.Index(Range("A:D"), WorksheetFunction.Match(ThirdStudent, Columns(StudentColumn), 0), GradeColumn) Then
                ThreeGroupScore = ThreeGroupScore + DifferentGrade
            End If
            If WorksheetFunction.Index(Range("A:D"), WorksheetFunction.Match(SecondStudent, Columns(StudentColumn), 0), GradeColumn) <> WorksheetFunction.Index(Range("A:D"), WorksheetFunction.Match(ThirdStudent, Columns(StudentColumn), 0), GradeColumn) Then
                ThreeGroupScore = ThreeGroupScore + DifferentGrade
            End If
        End If

        'DifferentAssessment
        Worksheets("Student Info").Activate
        StudentColumn = Rows(1).Find("Student").Column
        AssessmentColumn = Rows(1).Find("Assessment").Column

        Difference = WorksheetFunction.Index(Range("A:D"), WorksheetFunction.Match(FirstStudent, Columns(StudentColumn), 0), AssessmentColumn) - WorksheetFunction.Index(Range("A:D"), WorksheetFunction.Match(SecondStudent, Columns(StudentColumn), 0), AssessmentColumn)
        If Difference < -2 Or Difference > 2 Then
            GroupScore = GroupScore + DifferentAssessment
        End If
        'Add third student score if needed
        If EachStudent / EachTutor > 2 Then
            Difference = WorksheetFunction.Index(Range("A:D"), WorksheetFunction.Match(FirstStudent, Columns(StudentColumn), 0), AssessmentColumn) - WorksheetFunction.Index(Range("A:D"), WorksheetFunction.Match(SecondStudent, Columns(StudentColumn), 0), AssessmentColumn)
            If Difference < -2 Or Difference > 2 Then
                ThreeGroupScore = ThreeGroupScore + DifferentAssessment
            End If
            Difference = WorksheetFunction.Index(Range("A:D"), WorksheetFunction.Match(FirstStudent, Columns(StudentColumn), 0), AssessmentColumn) - WorksheetFunction.Index(Range("A:D"), WorksheetFunction.Match(ThirdStudent, Columns(StudentColumn), 0), AssessmentColumn)
            If Difference < -2 Or Difference > 2 Then
                ThreeGroupScore = ThreeGroupScore + DifferentAssessment
            End If
            Difference = WorksheetFunction.Index(Range("A:D"), WorksheetFunction.Match(SecondStudent, Columns(StudentColumn), 0), AssessmentColumn) - WorksheetFunction.Index(Range("A:D"), WorksheetFunction.Match(ThirdStudent, Columns(StudentColumn), 0), AssessmentColumn)
            If Difference < -2 Or Difference > 2 Then
                ThreeGroupScore = ThreeGroupScore + DifferentAssessment
            End If
        End If

        Worksheets("Score Sheet").Activate
        Cells(FirstStudentRow, Group) = FirstStudent
        Cells(SecondStudentRow, Group) = SecondStudent
        'Add third student score if needed
        If EachStudent / EachTutor > 2 Then
            Cells(ThirdStudentRow, Group) = ThirdStudent
        End If

NextGroup:

    Next

'****************MUST ACCOUNT FOR 3 Student to 1 Tutor!!!!!!!!!!!!!!!!!!!!!!!'

    Worksheets("Score Sheet").Activate

    'Sort to get matching of largest correct
    With Worksheets("Score Sheet")
        .Sort.SortFields.Clear
        .Sort.SortFields.Add Key:=Range(Cells(GroupScoreRow, 2), Cells(GroupScoreRow, EndColumn)) _
            , SortOn:=xlSortOnValues, Order:=xlDescending, DataOption:=xlSortNormal
        .Sort.SetRange Range(Cells(1, 2), Cells(ThirdStudentRow, EndColumn))
        .Sort.Header = xlYes
        .Sort.MatchCase = False
        .Sort.Orientation = xlLeftToRight
        .Sort.SortMethod = xlPinYin
        .Sort.Apply
    End With

'*********Dual Pairings************************************************************************************'
    Dim LastStudent As Integer, LastTutor As Integer
    Worksheets("Score Sheet").Activate
    PairingColumn = 2
    PairingCount = 0
    LastStudent = Columns(2).End(xlDown).Row
    LastTutor = Rows(2).End(xlToRight).Column
    LastPairing = LastStudent - LastTutor

    Do

        If Len(Cells(FirstStudentRow, PairingColumn)) > 0 _
            And WorksheetFunction.CountIf(Rows(CStr(FirstStudentRow) & ":" & CStr(SecondStudentRow)), Cells(FirstStudentRow, PairingColumn)) = 2 Then

            Rows(CStr(FirstStudentRow) & ":" & CStr(SecondStudentRow)).Select
            Selection.Find(Cells(FirstStudentRow, PairingColumn)).Activate
            Selection.FindNext(After:=ActiveCell).Activate
            ActiveCell.ClearContents

        End If

        Do While Len(Cells(SecondStudentRow, PairingColumn)) > 0 _
            And WorksheetFunction.CountIf(Rows(CStr(FirstStudentRow) & ":" & CStr(SecondStudentRow)), Cells(SecondStudentRow, PairingColumn)) >= 2

            Rows(CStr(FirstStudentRow) & ":" & CStr(SecondStudentRow)).Select
            Selection.Find(Cells(SecondStudentRow, PairingColumn)).Activate
            If Selection.Find(Cells(SecondStudentRow, PairingColumn)).Column = PairingColumn Then
                Selection.FindNext(After:=ActiveCell).Activate
                ActiveCell.ClearContents
            Else
                ActiveCell.ClearContents
            End If

        Loop

        'If a student is missing in a pairing, have the pairing extend to next group of students
        If Len(Cells(FirstStudentRow, PairingColumn)) > 0 _
            And Len(Cells(SecondStudentRow, PairingColumn)) > 0 Then
            PairingCount = PairingCount + 1
        End If

    PairingColumn = PairingColumn + 1

    Loop Until PairingCount = LastPairing

'*********Individual Pairings***************************************************************************'

    'Remove remaining students for lookup below to work
    Do While PairingColumn <= LastTutor

        Cells(FirstStudentRow, PairingColumn).ClearContents
        Cells(SecondStudentRow, PairingColumn).ClearContents
        PairingColumn = PairingColumn + 1

    Loop

'*********Get Students***********'
    StudentCount = 0
    StudentRow = ThirdStudentRow + 2
    For StudentsLeft = 2 To LastStudent 'To account for Group Score row

        If WorksheetFunction.CountIf(Rows(CStr(FirstStudentRow) & ":" & CStr(SecondStudentRow)), Cells(StudentsLeft, 1)) = 0 Then
            Cells(StudentRow, 1) = Cells(StudentsLeft, 1)
            StudentRow = StudentRow + 1
            StudentCount = StudentCount + 1
        End If

    Next

'*********Get Tutors and Score***********'
    TutorColumn = 2
    TutorRow = ThirdStudentRow + 1
    For TutorsLeft = 2 To LastTutor

        If Len(Cells(FirstStudentRow, TutorsLeft)) = 0 _
            And Len(Cells(SecondStudentRow, TutorsLeft)) = 0 Then
            Cells(TutorRow, TutorColumn) = Cells(1, TutorsLeft)

            For StudentsLeft = 1 To StudentCount
                x = Columns(1).Find(Cells(TutorRow + StudentsLeft, 1)).Row
                Cells(TutorRow + StudentsLeft, TutorColumn) = Cells(x, TutorsLeft)
            Next

            TutorColumn = TutorColumn + 1

        End If

    Next

'*********Sort on Smallest then Largest Match***********'
    StudentRow = ThirdStudentRow + 2
    Cells(TutorRow, StudentCount + 2) = "Sum > 0"
    Cells(TutorRow, StudentCount + 3) = "Sum < 0"
    For SumRow = StudentRow To TutorRow + StudentCount
        Cells(SumRow, StudentCount + 2) = WorksheetFunction.SumIf(Range(Cells(SumRow, 2), Cells(SumRow, StudentCount + 1)), ">0")
        Cells(SumRow, StudentCount + 3) = WorksheetFunction.SumIf(Range(Cells(SumRow, 2), Cells(SumRow, StudentCount + 1)), "<0")
    Next

    'Sort to get matching of largest correct
    With Worksheets("Score Sheet")
        .Sort.SortFields.Clear
        .Sort.SortFields.Add Key:=Range(Cells(StudentRow, StudentCount + 3), Cells(StudentRow + StudentCount, StudentCount + 3)) _
            , SortOn:=xlSortOnValues, Order:=xlAscending, DataOption:=xlSortNormal
        .Sort.SortFields.Add Key:=Range(Cells(StudentRow, StudentCount + 2), Cells(StudentRow + StudentCount, StudentCount + 2)) _
            , SortOn:=xlSortOnValues, Order:=xlDescending, DataOption:=xlSortNormal
        .Sort.SetRange Range(Cells(StudentRow, 1), Cells(StudentRow + StudentCount, StudentCount + 3))
        .Sort.Header = xlGuess
        .Sort.MatchCase = False
        .Sort.Orientation = xlTopToBottom
        .Sort.SortMethod = xlPinYin
        .Sort.Apply
    End With

'*********Match Student to Tutor***********'
    For CurrentRow = StudentRow To TutorRow + StudentCount
        If Cells(CurrentRow, StudentCount + 2) < 0 Then
            For Individuals = 2 To StudentCount
                If Cells(CurrentRow, Individuals) < 0 Then
                    Cells(CurrentRow, Individuals).ClearContents
                End If
            Next
            Individuals = 1
            Do
                If Len(Cells(CurrentRow, Individuals)) > 0 _
                    And Len(Cells(CurrentRow, StudentCount + 3)) = 0 Then
                    Cells(CurrentRow, StudentCount + 3) = Cells(TutorRow, Individuals + 1)
                    Range(Cells(CurrentRow, Individuals + 1), Cells(CurrentRow - 1 + StudentCount, Individuals + 1)).ClearContents
                    Individuals = StudentCount + 1
                Else
                Individuals = Individuals + 1
                End If
            Loop While Individuals <= StudentCount
        Else
            'Sort to get matching of largest correct
            With Worksheets("Score Sheet")
                .Sort.SortFields.Clear
                .Sort.SortFields.Add Key:=Range(Cells(CurrentRow, 2), Cells(CurrentRow, StudentCount + 1)) _
                    , SortOn:=xlSortOnValues, Order:=xlDescending, DataOption:=xlSortNormal
                .Sort.SetRange Range(Cells(TutorRow, 2), Cells(CurrentRow + StudentCount, StudentCount + 1))
                .Sort.Header = xlYes
                .Sort.MatchCase = False
                .Sort.Orientation = xlLeftToRight
                .Sort.SortMethod = xlPinYin
                .Sort.Apply
            End With
            Cells(CurrentRow, StudentCount + 4) = Cells(TutorRow, 2)
            Range(Cells(StudentRow, 2), Cells(StudentRow - 1 + StudentCount, 2)).ClearContents
        End If

    Next

'*********Commit Matches to Schedule***********'
    Worksheets("Week to Week").Activate
    WeektoWeekRow = ActiveSheet.UsedRange.Rows.Count + 1
    TutorColumn = Rows(1).Find("Tutor").Column
    StudentColumn = Rows(1).Find("Student").Column
    WeekColumn = Rows(1).Find("Week").Column

    'Commit dual pairings
    Worksheets("Score Sheet").Activate
    For Number = 2 To PairingColumn - 2
        If Len(Cells(FirstStudentRow, Number)) > 0 Then
        Worksheets("Week to Week").Cells(WeektoWeekRow, TutorColumn) = Cells(1, Number) 'Tutor
        Worksheets("Week to Week").Cells(WeektoWeekRow, StudentColumn) = Cells(FirstStudentRow, Number) 'FirstStudent
        Worksheets("Week to Week").Cells(WeektoWeekRow, WeekColumn) = CurrentWeek
        WeektoWeekRow = WeektoWeekRow + 1
        End If
        If Len(Cells(SecondStudentRow, Number)) > 0 Then
        Worksheets("Week to Week").Cells(WeektoWeekRow, TutorColumn) = Cells(1, Number) 'Tutor
        Worksheets("Week to Week").Cells(WeektoWeekRow, StudentColumn) = Cells(SecondStudentRow, Number) 'SecondStudent
        Worksheets("Week to Week").Cells(WeektoWeekRow, WeekColumn) = CurrentWeek
        WeektoWeekRow = WeektoWeekRow + 1
        End If
    Next

    'Commit individual pairings
    For Number = StudentRow To TutorRow + StudentCount
        Worksheets("Week to Week").Cells(WeektoWeekRow, TutorColumn) = Cells(Number, StudentCount + 4) 'Tutor
        Worksheets("Week to Week").Cells(WeektoWeekRow, StudentColumn) = Cells(Number, 1) 'FirstStudent
        Worksheets("Week to Week").Cells(WeektoWeekRow, WeekColumn) = CurrentWeek
        WeektoWeekRow = WeektoWeekRow + 1
    Next

End If

Worksheets("RUN MACRO").Activate

MsgBox "Done"

End Sub

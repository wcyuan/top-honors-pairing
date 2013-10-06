Option Base 1
Sub Tutor_Student_Pairing()

Application.ScreenUpdating = False

Cells.Find(What:="", After:=ActiveCell, LookIn:=xlFormulas, _
    LookAt:=xlWhole, SearchOrder:=xlByRows, SearchDirection:=xlNext, _
    MatchCase:=False, SearchFormat:=False).Activate

'Dim StudentScore As Range
'Dim GroupScore As Range
'Dim FirstStudent As Range, SecondStudent As Range, ThirdStudent As Range, Tutor As Range
'
'CurrentWeek = 2
'
'STIncompatible = -20
'STPaired = 1
'STGood = 5
'SSIncompatible = -20
'Attendance = 0.1
'NotSameTopic = -5
'OnOwn = -10
'DifferentGrade = -2
'DifferentAssessment = -3
'
'Worksheets("Score Sheet").Activate
'AllStudents = Columns(1).End(xlDown).Row - 2
'AllTutors = Rows(1).End(xlToRight).Column - 1
'Range(Cells(2, 2), Cells(80, 51)).Delete
'
'For EachStudent = 1 To AllStudents
'
'    AttendanceScore = 0
'
'    'Determine whether student is here this week
'    Worksheets("Attendance").Activate
'    If WorksheetFunction.CountIfs(Columns(1), "Student " & EachStudent, Columns(2), CurrentWeek) = 1 Then
'        'Add score for how many times student has attended before
'        AttendanceScore = Attendance * WorksheetFunction.CountIf(Columns(1), "Student " & EachStudent)
'    Else
'        GoTo NextStudent
'    End If
'
'    For EachTutor = 1 To AllTutors
'
'        'Determine whether tutor is here this week
'        Worksheets("Attendance").Activate
'        If WorksheetFunction.CountIfs(Columns(1), "Tutor " & EachTutor, Columns(2), CurrentWeek) <> 1 Then
'            GoTo NextTutor
'        End If
'
'        Set StudentScore = Worksheets("Score Sheet").Cells(EachStudent + 1, EachTutor + 1)
'
'        'STPaired
'        Worksheets("Week to Week").Activate
'        StudentScore = AttendanceScore + STPaired * WorksheetFunction.CountIfs(Columns(2), "Tutor " & EachTutor, Columns(3), "Student " & EachStudent)
'
'        'STGood
'        Worksheets("Absolutes").Activate
'        StudentScore = StudentScore + STGood * WorksheetFunction.CountIfs(Columns(1), "Tutor " & EachTutor, Columns(2), "Student " & EachStudent, Columns(4), "GoodMatch")
'
'        'STIncompatible
'        Worksheets("Absolutes").Activate
'        StudentScore = StudentScore + STIncompatible * WorksheetFunction.CountIfs(Columns(1), "Tutor " & EachTutor, Columns(2), "Student " & EachStudent, Columns(4), "TutorStudent")
'
'NextTutor:
'
'    Next
'
'NextStudent:
'
'Next
'
'If AllStudents > AllTutors Then
'
'    For Groups = 1 To AllTutors
'
'        Worksheets("Score Sheet").Activate
'
'        'If Tutor is not there (nothing in column)
'        If WorksheetFunction.CountA(Columns(Groups + 1)) = 1 Then
'            GoTo NextGroup
'        End If
'
'        Set GroupScore = Worksheets("Score Sheet").Cells(77, Groups + 1)
'
'        'Sort to get matching of largest correct
'        With Worksheets("Score Sheet")
'            .Sort.SortFields.Clear
'            .Sort.SortFields.Add Key:=Range(Cells(2, Groups + 1), Cells(76, Groups + 1)) _
'                , SortOn:=xlSortOnValues, Order:=xlDescending, DataOption:=xlSortNormal
'            .Sort.SetRange Range(Cells(1, 1), Cells(76, 51))
'            .Sort.Header = xlYes
'            .Sort.MatchCase = False
'            .Sort.Orientation = xlTopToBottom
'            .Sort.SortMethod = xlPinYin
'            .Sort.Apply
'        End With
'
'        Set FirstStudent = Cells(2, 1)
'        Set SecondStudent = Cells(3, 1)
''        Set ThirdStudent = Cells(4, 1)
'        Set Tutor = Cells(1, Groups + 1)
'
'        GroupScore = Cells(2, Groups + 1) + Cells(3, Groups + 1)
'
'        'OnOwn
'        Worksheets("Absolutes").Activate
'        GroupScore = GroupScore + OnOwn * WorksheetFunction.CountIfs(Columns(1), FirstStudent, Columns(3), "OnOwn")
'        GroupScore = GroupScore + OnOwn * WorksheetFunction.CountIfs(Columns(1), SecondStudent, Columns(3), "OnOwn")
'        GroupScore = GroupScore + OnOwn * WorksheetFunction.CountIfs(Columns(1), Tutor, Columns(3), "OnOwn")
'
'        'SSIncompatible
'        Worksheets("Absolutes").Activate
'        GroupScore = GroupScore + SSIncompatible * WorksheetFunction.CountIfs(Columns(1), FirstStudent, Columns(2), SecondStudent, Columns(4), "StudentStudent")
'
'        'NotSameTopic
'        Worksheets("Current Topic").Activate
'        If Cells(WorksheetFunction.Match(FirstStudent & CurrentWeek, Columns(4), 0), 3) <> Cells(WorksheetFunction.Match(SecondStudent & CurrentWeek, Columns(4), 0), 3) Then
'            GroupScore = GroupScore + NotSameTopic
'        End If
'
'        'DifferentGrade
'        Worksheets("Student Info").Activate
'        If WorksheetFunction.Index(Range("A:D"), WorksheetFunction.Match(FirstStudent, Columns(1), 0), 3) <> WorksheetFunction.Index(Range("A:D"), WorksheetFunction.Match(SecondStudent, Columns(1), 0), 3) Then
'            GroupScore = GroupScore + DifferentGrade
'        End If
'
'        'DifferentAssessment
'        Worksheets("Student Info").Activate
'        Difference = WorksheetFunction.Index(Range("A:D"), WorksheetFunction.Match(FirstStudent, Columns(1), 0), 4) - WorksheetFunction.Index(Range("A:D"), WorksheetFunction.Match(SecondStudent, Columns(1), 0), 4)
'        If Difference < -2 Or Difference > 2 Then
'            GroupScore = GroupScore + DifferentAssessment
'        End If
'
'        Worksheets("Score Sheet").Activate
'        Cells(78, Groups + 1) = FirstStudent
'        Cells(79, Groups + 1) = SecondStudent
'
'NextGroup:
'
'    Next
'
'    Worksheets("Score Sheet").Activate
'
'    'Sort to get matching of largest correct
'    With Worksheets("Score Sheet")
'        .Sort.SortFields.Clear
'        .Sort.SortFields.Add Key:=Range(Cells(77, 2), Cells(77, 51)) _
'            , SortOn:=xlSortOnValues, Order:=xlDescending, DataOption:=xlSortNormal
'        .Sort.SetRange Range(Cells(1, 2), Cells(80, 51))
'        .Sort.Header = xlYes
'        .Sort.MatchCase = False
'        .Sort.Orientation = xlLeftToRight
'        .Sort.SortMethod = xlPinYin
'        .Sort.Apply
'    End With

'*********Dual Pairings***********'
    Worksheets("Score Sheet").Activate
    Pairings = 1
    ToEnd = 28

    Do

        If Len(Cells(78, Pairings + 1)) > 0 _
            And WorksheetFunction.CountIf(Rows("78:79"), Cells(78, Pairings + 1)) = 2 Then

            Rows("78:79").Select
            Selection.Find(Cells(78, Pairings + 1)).Activate
            Selection.FindNext(After:=ActiveCell).Activate
            ActiveCell.ClearContents

        End If

        Do While Len(Cells(79, Pairings + 1)) > 0 _
            And WorksheetFunction.CountIf(Rows("78:79"), Cells(79, Pairings + 1)) >= 2

            Rows("78:79").Select
            Selection.Find(Cells(79, Pairings + 1)).Activate
            If Selection.Find(Cells(79, Pairings + 1)).Column = Pairings + 1 Then
                Selection.FindNext(After:=ActiveCell).Activate
                ActiveCell.ClearContents
            Else
                ActiveCell.ClearContents
            End If

        Loop

        'If a student is missing in a pairing, have the pairing extend to next group of students
        If Len(Cells(78, Pairings + 1)) = 0 _
            Or Len(Cells(79, Pairings + 1)) = 0 Then
            ToEnd = ToEnd + 1
        End If

    Pairings = Pairings + 1

    Loop Until Pairings > ToEnd

'*********Individual Pairings***********'

    'Remove remaining students for lookup below to work
    Do While Pairings <= 44 'AllTutors

        Cells(78, Pairings + 1).ClearContents
        Cells(79, Pairings + 1).ClearContents
        Pairings = Pairings + 1

    Loop

    StudentCount = 0
    StudentRow = 83
    For StudentsLeft = 1 To 72 'AllStudents

        If WorksheetFunction.CountIf(Rows("78:79"), Cells(StudentsLeft + 1, 1)) = 0 Then
            Cells(StudentRow, 1) = Cells(StudentsLeft + 1, 1)
            StudentRow = StudentRow + 1
            StudentCount = StudentCount + 1
        End If

    Next

    TutorColumn = 2
    For TutorsLeft = 1 To 44 'AllTutors

        If Len(Cells(78, TutorsLeft + 1)) = 0 _
            And Len(Cells(79, TutorsLeft + 1)) = 0 Then
            Cells(82, TutorColumn) = Cells(1, TutorsLeft + 1)

            For StudentsLeft = 1 To StudentCount
                x = Columns(1).Find(Cells(82 + StudentsLeft, 1)).Row
                Cells(82 + StudentsLeft, TutorColumn) = Cells(x, TutorsLeft + 1)
            Next

            TutorColumn = TutorColumn + 1

        End If

    Next

    For SumRow = 83 To 82 + StudentCount
        Cells(SumRow, StudentCount + 2) = WorksheetFunction.SumIf(Range(Cells(SumRow, 2), Cells(SumRow, StudentCount + 1)), ">0")
        Cells(SumRow, StudentCount + 3) = WorksheetFunction.SumIf(Range(Cells(SumRow, 2), Cells(SumRow, StudentCount + 1)), "<0")
    Next

    'Sort to get matching of largest correct
    With Worksheets("Score Sheet")
        .Sort.SortFields.Clear
        .Sort.SortFields.Add Key:=Range(Cells(83, StudentCount + 3), Cells(91, StudentCount + 3)) _
            , SortOn:=xlSortOnValues, Order:=xlAscending, DataOption:=xlSortNormal
        .Sort.SortFields.Add Key:=Range(Cells(83, StudentCount + 2), Cells(91, StudentCount + 2)) _
            , SortOn:=xlSortOnValues, Order:=xlDescending, DataOption:=xlSortNormal
        .Sort.SetRange Range(Cells(83, 1), Cells(91, StudentCount + 3))
        .Sort.Header = xlGuess
        .Sort.MatchCase = False
        .Sort.Orientation = xlTopToBottom
        .Sort.SortMethod = xlPinYin
        .Sort.Apply
    End With

    For StudentRow = 83 To 82 + StudentCount
        If Cells(StudentRow, 12) < 0 Then
            For Individuals = 1 To StudentCount
                If Cells(StudentRow, Individuals + 1) < 0 Then
                    Cells(StudentRow, Individuals + 1).ClearContents
                End If
            Next
            Individuals = 1
            Do
                If Len(Cells(StudentRow, Individuals)) > 0 _
                    And Len(Cells(StudentRow, 13)) = 0 Then
                    Cells(StudentRow, 13) = Cells(82, Individuals + 1)
                    Range(Cells(StudentRow, Individuals + 1), Cells(StudentRow - 1 + StudentCount, Individuals + 1)).ClearContents
                    Individuals = StudentCount + 1
                Else
                Individuals = Individuals + 1
                End If
            Loop While Individuals <= StudentCount
        Else
            'Sort to get matching of largest correct
            With Worksheets("Score Sheet")
                .Sort.SortFields.Clear
                .Sort.SortFields.Add Key:=Range(Cells(StudentRow, 2), Cells(StudentRow, StudentCount + 1)) _
                    , SortOn:=xlSortOnValues, Order:=xlDescending, DataOption:=xlSortNormal
                .Sort.SetRange Range(Cells(82, 2), Cells(91, StudentCount + 1))
                .Sort.Header = xlYes
                .Sort.MatchCase = False
                .Sort.Orientation = xlLeftToRight
                .Sort.SortMethod = xlPinYin
                .Sort.Apply
            End With
            Cells(StudentRow, 13) = Cells(82, 2)
            Range(Cells(StudentRow, 2), Cells(StudentRow - 1 + StudentCount, 2)).ClearContents
        End If

    Next

'*********Commit Matches to Schedule***********'
    Worksheets("Week to Week").Activate
    WeektoWeekRow = ActiveSheet.UsedRange.Rows.Count + 1

    Worksheets("Score Sheet").Activate
    For Number = 1 To ToEnd
        If Len(Cells(78, Number + 1)) > 0 Then
        Worksheets("Week to Week").Cells(WeektoWeekRow, 2) = Cells(1, Number + 1) 'Tutor
        Worksheets("Week to Week").Cells(WeektoWeekRow, 3) = Cells(78, Number + 1) 'FirstStudent
        Worksheets("Week to Week").Cells(WeektoWeekRow, 4) = CurrentWeek
        WeektoWeekRow = WeektoWeekRow + 1
        End If
        If Len(Cells(79, Number + 1)) > 0 Then
        Worksheets("Week to Week").Cells(WeektoWeekRow, 2) = Cells(1, Number + 1) 'Tutor
        Worksheets("Week to Week").Cells(WeektoWeekRow, 3) = Cells(79, Number + 1) 'SecondStudent
        Worksheets("Week to Week").Cells(WeektoWeekRow, 4) = CurrentWeek
        WeektoWeekRow = WeektoWeekRow + 1
        End If
    Next

    For Number = 83 To 82 + StudentCount
        Worksheets("Week to Week").Cells(WeektoWeekRow, 2) = Cells(Number, 13) 'Tutor
        Worksheets("Week to Week").Cells(WeektoWeekRow, 3) = Cells(Number, 1) 'FirstStudent
        Worksheets("Week to Week").Cells(WeektoWeekRow, 4) = CurrentWeek
        WeektoWeekRow = WeektoWeekRow + 1
    Next

'End If

Worksheets("Score Sheet").Activate

MsgBox "Done"

End Sub



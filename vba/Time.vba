Sub TimeUpdate()

'To convert Timer into Minutes and Seconds
If Timer - Time >= 60 Then
    Seconds = (Timer - Time) Mod 60
    Minutes = Int((Timer - Time) / 60)
Else
    Seconds = Timer - Time
    Minutes = 0
End If

PercentComplete = Format(CurrentRow / RowEnd * 100, "0.00") & "% Done"

Application.StatusBar = Status & " - " & Minutes & " Mins, " & Seconds & " Seconds" & " - " & PercentComplete

End Sub

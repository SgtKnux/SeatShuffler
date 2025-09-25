# SeatShuffler
This web app was designed to help SNCOA classes quickly shuffle around the seats each week.  The algorithm behind the app attempts to account for students sitting next to each other prior to the shuffle so that students are placed next to new neighbors (this is not preserved across multiple shuffles, just one to the other).

It can be used for other reasons as well, such as determining briefing order, setting up groups for other tasks, and so on.  I hope you find use in it!


## How to use the Seat Shuffler
### First Time Use
When first loading up the shuffler, you'll see two columns with 1 thru 16 in them.  The left column's items are EDITABLE and can be changed from a number to a name.  When setting up, first change the top input box to match your class size. Then, pick a side of the class (doesn't matter if it's left or right) and choose that as seat 1.  Then set the name accordingly. For example, if John is sitting in seat 1, then change 1 to John in the left column.  If Jill is in seat 2 next to John, change 2 to Jill, and so on. 

Once all the names are filled in, hit the Shuffle button to shuffle everyone to new seats.  Once you have shuffled, click "Download CSV" and save the CSV file somewhere on your computer.  This will allow you to quick-load your class roster and their current locations for the next shuffle.

### Subsequent Uses
After opening the shuffler, click the "Load CSV" button, then select your previously saved csv file.  The shuffler will then load in your previous state, allowing you to quickly shuffle again.

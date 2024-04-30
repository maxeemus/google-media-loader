param(
    [int]$MonthsBack = 0
)

.\.venv\Scripts\Activate.ps1

$currentDate = Get-Date

# Extract the year and month
$year = $currentDate.Year
$month = $currentDate.Month

# Create a DateTime object for the first day of the current month
$firstDayOfMonth = Get-Date -Year $year -Month ($month - $MonthsBack) -Day 1
$lastDayOfMonth = $firstDayOfMonth.AddMonths(1).AddDays(-1)

# Convert the first day to a string in the desired format (e.g., "2024-04-01")
$firstDayString = $firstDayOfMonth.ToString("yyyy-MM-dd")
$lastDayString = $lastDayOfMonth.ToString("yyyy-MM-dd")

python.exe .\download-google-media.py --start-date $firstDayString --end-date $lastDayString

 
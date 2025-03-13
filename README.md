# FundRacer
Basic code for a multi-page/window desktop application that operates on the user's web browser on the local port of 5000. Made for Windows environments but can be adapted.

Can be used to track donation amounts for fundraisers:

    Open application to the initial page (input.html); click "Fund Race Display" to open display page (progress.html)

    Input a donor's name, a donation amount, and a fund name that will display on the progress screen and update the progress bars in real time.

    Progress bars are set to populate input values from donation_history.txt; reset to return to 0.

    FundRace progress page is developed to be displayed on a projector screen but can be adapted to any style or screen type.

    MUST click "Exit" button at the bottom of Donation Input page to close the server and fully exit the application.


To continue working on the project after packaging, or adding updates, recreate the virtual environment:

bash:

    python -m venv .venv
    .venv\Scripts\activate  # On Windows
    pip install -r requirements.txt # Install the dependencies from requirements.txt

For best results when compiling executable application, use pyinstaller main.spec and ensure that .exe file and _internal folder are in the dist folder.


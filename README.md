# Transcibe Demo

Transcribes an audio file containing a meeting or conversation



Decisions on demo:



Use Whisper on local machine, Reason: on local machine, do not need to communicate with Internet, security risk is lower, and developer used before Whisper with some experience.



Use simple API,reason: easy to be consumed be other applications.





1\. install whisper on local machine:

&#x20;  command line: pip install -U openai-whisper

&#x20;  trouble shooting: 

&#x20;  If you already installed it but the command still fails, the folder containing the whisper.exe executable is likely missing from your system PATH.

&#x20;  Find the installation path: Run pip show openai-whisper. Look for the "Location" line (e.g., C:\\Python312\\Lib\\site-packages). 

&#x20;  The executable is usually in a sibling Scripts folder, such as C:\\Python312\\Scripts.

&#x20;  Add to Environment Variables:Search for "Edit the system environment variables" in the Windows Start menu.

&#x20;  Click Environment Variables > Select Path under "User variables" > Click Edit. 

&#x20;  Click New and paste the path to your Python Scripts folder. 

&#x20;  Restart Terminal.

2\. install ffmpeg: 

&#x20;  run command line with Admin

&#x20;  choco install ffmpeg

3\. install pyannote.audio: 

&#x20;  run command line: pip install pyannote.audio


\------------------------------------------------Whisper local is tested. Mile Stone-----------------------------------------

Test:

    Clone my repo from github and use main branch, and isntalled python on your computer, and run command line in the project folder and below to run the api:

    cd app

    $env:HF_TOKEN="[your huggingface_token]"

    python -m uvicorn main:app

 visit url: http://127.0.0.1:8000/docs



Test Optimization：


    Clone my repo from github and use Optimization branch, and isntalled python on your computer, and run command line in the project folder and below to run the api:

    cd app

    $env:HF_TOKEN="[your huggingface_token]"

    python -m uvicorn main:app

 visit url: http://127.0.0.1:8000/docs

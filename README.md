# delphi

## How to run the test from oracle
1. Clone this repository
2. create `.env` in the root directory
3. put OPENAI_API_KEY=<your_api_key_from_together_ai>
4. `AgentSpce_CustomMcpTest.ipynb` now works, congrats!

## How to run the IMAGE-TO-TEXT and SEARCH
1. cd into the `delphi/` dir
2. `python ./agenspec-image.py resources/word_screenshot.png --resources-dir resources`
3. `python ./search/search-engine.py index --resources-dir resources` 
4. `python ./search/search-engine.py search "SmartArt"`
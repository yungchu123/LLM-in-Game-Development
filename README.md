# LLM in Game Development

## Installation and Setup
1. Git Clone

2. Create a Python virtual environment (Below example is for Windows)
```
python -m venv project_env
project_env\Scripts\activate.bat
```

3. Install required packages
```
cd File_Location
pip install -r requirements.txt
```

4. Run the game file
```
python main.py
```

## Creating Executable File
If you have not installed pyinstaller:
```
pip install pyinstaller
```
Create an executable file:
```
pyinstaller --hidden-import=pydantic --hidden-import=pydantic-core --hidden-import=pydantic.deprecated.decorator main.py --onefile --windowed
```

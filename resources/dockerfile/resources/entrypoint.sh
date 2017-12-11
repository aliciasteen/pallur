#!bin/bash
echo $project_name
pip install $project_name/requirements.txt
python $project_name/$application_file

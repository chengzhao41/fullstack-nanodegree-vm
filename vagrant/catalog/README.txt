**Cheng's Catalog App**

**Introduction**
This website allows users to view the categories and items in the categories.

**Section 1: Set Up Environment**
Explain how to install, start and connect to the virtual machine (vagrant)

**Section 2: Requirements**
See requirements.txt. Install by executing "pip install -r requirements.txt".

**Section 3: Installation**
Clone this repo by executing "git clone https://github.com/chengzhao41/fullstack-nanodegree-vm"
or download the zip file.

**Section 4: Set Up**
1) Install the database by executing "python create_db.py"
2) Populate the database with sample data by executing "python populate_db.py"

**Section 5: How to run**
1) Change the port number from 9000 if you wish, by modifying the last line in application.py "app.run(host='localhost', port=9000)".
2) Run the server by executing "python application.py".
3) Go to website by "http://localhost:9000/". Use the port number that you changed in step 3) instead of 9000 if you changed it. 

**Section 6: Usage**
User can use google plus or Facebook to create an account or to login. 
If the user is logged in, she/he can create items in the existing categories. 
She/he can also modify or delete existing items that she/he has created.
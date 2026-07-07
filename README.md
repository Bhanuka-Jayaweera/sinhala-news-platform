# Sinhala News Platform
This AI-based application collects, categorizes, visualizes and recommends Sinhalese news articles.

## Instructions to Start the Application

### Pre-Requisites
Python greater than 3.11 installed. Anaconda prefererd

### How to start the application

1. Create a new anaconda environment.
    ```bash
    conda create --name sinhala-news-platform python=3.11
    ```

2. Activate anaconda environment.
    ```bash
    conda activate sinhala-news-platform
    ```

3. Install required python dependencies.
    ```bash
    pip install -r requirements.txt
    ```

4. Download models from [OneDrive](https://ssu-my.sharepoint.com/:f:/r/personal/2senan77_solent_ac_uk/Documents/Dissertation%20Project/Documentations/Final%20Report/Shared%20Models?csf=1&web=1&e=hGldD5) location.
    1. Create a new directory in project root directories with path "temp/models" if not exists.
    2. Move the downloaded files into "temp/models" folder. (Make sure not to rename any folder in downloaded files)
    3. At the end, file structure should look like below.
        ```
        <Project Root Directory>
        ├─ <Current Project Files>
        └─ temp
           └─ models
              ├─ sinbert-1810
              └─ xgboost
        ```

5. Start the application.
    ```bash
    python manage.py runserver --noreload
    ```

6. Start browser and navigate to [http://127.0.0.1:8000/users/login_user](http://127.0.0.1:8000/users/login_user)

7. Use following credentials to log into the system.
    * Username: Admin
    * Password: 123

## Development Notes
This sections is only for development purposes and please ignore if you want to run the application.

### Start the server
```bash
python manage.py runserver
```

Run server without duplicate schedulers
```bash
python manage.py runserver --noreload
```

### Migrate database changes

`python manage.py makemigrations`

then migrate using
`python manage.py migrate`


### Create superuser
A superuser login is required to login to the django admin portal
`python manage.py createsuperuser`

Admin portal url: `http://localhost:8000/admin`

Default credentials
* Username: admin
* Password: 123


### Create a new app
`python manage.py startapp <appname>`

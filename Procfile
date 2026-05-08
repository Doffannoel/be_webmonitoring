web: cd be_basedir && python manage.py migrate && python manage.py collectstatic --noinput && gunicorn be.wsgi:application --bind 0.0.0.0:$PORT

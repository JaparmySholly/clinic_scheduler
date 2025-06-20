#!/usr/bin/env bash
set -e

# Apply any pending migrations
python manage.py migrate

# If no superuser exists, you could auto-create one here (optional)
# echo "from django.contrib.auth import get_user_model; \
# User=get_user_model(); \
# User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin','admin@example.com','adminpass')" \
# | python manage.py shell

# Finally, launch the server on 0.0.0.0:8000
exec python manage.py runserver 0.0.0.0:8000

from mongoengine import Document, StringField, DateTimeField, DictField, ListField, ImageField, IntField
from datetime import datetime
from django.db import models

class Resume(Document):
    user_id = StringField(required=True)  # This will be the username from SQLite
    version = IntField(default=1)  # Use an integer for version and start with 1
    resume_content = DictField()  # Store entire form data as a dictionary
    created_at = DateTimeField(default=datetime.now)
    certifications = ListField()
    skills = ListField() 
    hobbies = ListField()
    languages = ListField() 
    personal_information = DictField()
    professional_summary = StringField()
    profile_photo  = ImageField()
    references = ListField(DictField())
    work_experience = ListField(DictField()) 
    education = ListField(DictField())

    meta = {
        'db_alias': 'default',
        'collection': 'resumes'
    }


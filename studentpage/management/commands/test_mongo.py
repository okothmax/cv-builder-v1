from django.core.management.base import BaseCommand
from mongoengine import connect
from mongoengine.connection import get_db
from django.conf import settings
from studentpage.models_mongo import Resume  # Import your MongoDB model


class Command(BaseCommand):
    help = 'Test MongoDB connection and display a document for the specified user_id'

    def add_arguments(self, parser):
        # Define a command-line argument for the user_id (email)
        parser.add_argument('user_id', type=str, help='The user_id to filter by (e.g., username or email)')

    def handle(self, *args, **kwargs):
        user_id = kwargs['user_id']  # Get the user_id from command-line arguments

        try:
            # Connect to MongoDB
            connect(
                db=settings.MONGODB_NAME,
                host=settings.MONGODB_HOST,
                port=settings.MONGODB_PORT
            )

            # Attempt to get the MongoDB database object
            db = get_db()
            self.stdout.write(self.style.SUCCESS(f"Successfully connected to MongoDB: {db.name}"))

            # Query for the document where user_id matches the provided value
            document = Resume.objects(user_id=user_id).first()

            if document:
                # Convert the document to a JSON-like format and print it
                self.stdout.write(self.style.SUCCESS(f"Document found for user_id '{user_id}': {document.to_json(indent=4)}"))
            else:
                self.stdout.write(self.style.WARNING(f"No documents found for user_id '{user_id}' in the collection."))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Failed to connect to MongoDB: {e}"))

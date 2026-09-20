from app.database.connection import SessionLocal
from app.database.models import DatasetProfile


class DatasetProfileRepository:

    @staticmethod
    def save_profile(
        dataset_name,
        profile_data
    ):

        db = SessionLocal()

        try:

            profile = DatasetProfile(
                dataset_name=dataset_name,
                profile_data=profile_data
            )

            db.add(profile)

            db.commit()

            return profile

        finally:
            db.close()
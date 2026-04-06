from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Import all models so Alembic can discover them for autogenerate.
import app.models.document   # noqa: F401, E402
import app.models.job        # noqa: F401, E402
import app.models.submittal  # noqa: F401, E402
import app.models.equipment  # noqa: F401, E402

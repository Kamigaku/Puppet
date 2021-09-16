from discord import Embed
from peewee import Model, TextField, ModelBase

from discordClient.dal import dbContext


dbContext = dbContext.DbContext()


class MetaBaseModel(ModelBase):
    def __init__(cls, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cls.table_name = cls._meta.table_name

    def __str__(self):
        return self.table_name


class BaseModel(Model, metaclass=MetaBaseModel):

    def generate_embed(self) -> Embed:
        raise NotImplementedError("This model has no embed display implementation.")

    class Meta:
        database = dbContext.sqliteConnection


class EnumTextField(TextField):
    def __init__(self, enum_class, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.enum_class = enum_class

    def db_value(self, value):
        return value.value

    def python_value(self, value):
        return self.enum_class(value)

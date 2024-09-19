class DatabaseNotSupportedException(Exception):

    def __init__(self, database_type: str):
        super(DatabaseNotSupportedException, self).__init__()
        self.database_type = database_type

    def __str__(self):
        return f"Database {self.database_type} not supported"

    def __repr__(self):
        return self.__str__()

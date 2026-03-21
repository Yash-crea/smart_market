class SmartMarketRouter:
    """
    DEPRECATED: Database router - now all models use default SQLite database
    """
    
    def db_for_read(self, model, **hints):
        return None  # Use default database
    
    def db_for_write(self, model, **hints):
        return None  # Use default database
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return None  # Allow default migration behavior
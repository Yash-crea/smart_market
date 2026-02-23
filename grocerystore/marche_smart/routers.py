class SmartMarketRouter:
    """
    Database router to direct smart market models to the smart_market database
    and all other models to the default SQLite database
    """
    
    smart_market_models = {
        'customers', 'smartproducts', 'orders', 'orderitems', 'payments',
        'reviews', 'inventory', 'suppliers', 'employees', 'customersupport',
        'dailysales', 'storeinfo', 'auditlog'
    }
    
    def db_for_read(self, model, **hints):
        """Suggest the database to read from."""
        if model._meta.app_label == 'marche_smart' and model._meta.model_name in self.smart_market_models:
            return 'smart_market'
        return 'default'
    
    def db_for_write(self, model, **hints):
        """Suggest the database to write to."""
        if model._meta.app_label == 'marche_smart' and model._meta.model_name in self.smart_market_models:
            return 'smart_market'
        return 'default'
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """Ensure that smart market models get migrated to the smart_market database."""
        if app_label == 'marche_smart':
            if model_name in self.smart_market_models:
                return db == 'smart_market'
            else:
                return db == 'default'
        elif db == 'smart_market':
            return False
        return db == 'default'
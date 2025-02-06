from django.core.exceptions import ValidationError
import re

class UserPasswordValidator:
    def validate(self, password, user=None):
        if not re.search(r'[A-Z]', password):
            raise ValidationError(self.get_help_text())
        if not re.search(r'[a-z]', password):
            raise ValidationError(self.get_help_text())
        if not re.search(r'[0-9]', password):
            raise ValidationError(self.get_help_text())
        if not re.search(r'[!@#$%^&*()_+]', password):
            raise ValidationError(self.get_help_text())
        
    def get_help_text(self):
        return "Password must contain at least 8 characters including one uppercase letter, one lowercase letter, one digit, and one special character"
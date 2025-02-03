from django import forms
from .models import Account
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

LIMITED_USER_TYPE_CHOICES = [
    choice for choice in Account.USER_TYPE_CHOICES if choice[0] != 'admin'
]

class AccountSignupForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(AccountSignupForm, self).__init__(*args, **kwargs)
        for fieldname, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'w-full text-sm text-gray-800 bg-gray-100 focus:bg-transparent pl-4 pr-10 py-3.5 rounded-md outline-blue-600',
                'placeholder': field.label + ' (Required)' if field.required else field.label
            })
            field.label = ''
            
    email_address = forms.EmailField(required=True,label='Your Email')
    password_1 = forms.CharField(widget=forms.PasswordInput, required=True, label='Password')
    password_2 = forms.CharField(widget=forms.PasswordInput, required=True, label='Confirm Password')
    user_type = forms.ChoiceField(choices=LIMITED_USER_TYPE_CHOICES, required=True, label='User Type')
    contact_number = forms.CharField(required=True, label='Contact Number', widget=forms.TextInput(attrs={
            'type': 'tel',       
            'pattern': '[0-9]*',          
            'inputmode': 'numeric',       
        }))

    class Meta:
        model = Account
        fields = ['email_address', 'user_type', 'contact_number']

    def clean_password_1(self):
        password = self.cleaned_data.get('password_1')
        try:
            validate_password(password)
        except ValidationError as e:
            raise forms.ValidationError(e.messages)
        return password

    def clean_password_2(self):
        password_1 = self.cleaned_data.get('password_1')
        password_2 = self.cleaned_data.get('password_2')
        if password_1 and password_2 and password_1 != password_2:
            raise forms.ValidationError("Passwords do not match")
        return password_2

    def clean_contact_number(self):
        prefix = self.data.get('contact_prefix')
        number = self.cleaned_data.get('contact_number')

        if not prefix or not number:
            raise forms.ValidationError("Please enter a valid contact number")
        if not number.isdigit():
            raise forms.ValidationError("Please enter a valid contact number")
        full_contact_number = f"{prefix}{number}"
        if not full_contact_number.startswith('+'):
            raise forms.ValidationError("Please enter a valid contact number")
        
        return full_contact_number

    def save(self, commit=False):
        account = super().save(commit=False)
        # if commit:
        #     account.save() # Not committing to the database yet as we need to navigate to volunteer/organization details and collect those so to not create an Account object which is not linked to a Volunteer or Organization object
        return account

class LoginForm(AuthenticationForm):
    # Password field automatically included and validated
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for fieldname, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'w-full text-sm text-gray-800 bg-gray-100 focus:bg-transparent pl-4 pr-10 py-3.5 rounded-md outline-blue-600',
                'placeholder': field.label,
            })

    username = forms.EmailField(
        label="Enter email address",
        required=True,
        error_messages={
            'invalid': "Invalid email address"
        }
    ) # Overriding the default username field to be an email field

    password = forms.CharField(widget=forms.PasswordInput, required=True, label='Enter password')

    # Redundant as the email field is already validated as an email field
    # def clean_username(self):
    #     email=self.cleaned_data.get('username')
    #     if email and '@' not in email:
    #         raise forms.ValidationError("Invalid email address")
    #     return email